from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
import cv2
import numpy as np
import os
import glob
from typing import List

# Core pipeline imports
from app.core.face_analysis import FaceAnalyzer
from app.core.hair_segmentation import HairSegmenter
from app.core.hair_removal import HairRemover
from app.core.color_extraction import HairColorExtractor
from app.core.warp import HairstyleWarper
from app.core.color_transfer import HairColorTransfer
from app.core.overlay import FinalOverlayEngine
from app.core.hairstyle_templates import hairstyle_loader
from app.core.face_shape_classifier import FaceShapeClassifier
from app.core.hairstyle_recommender import HairstyleRecommender

# New AI modules
from app.ai_modules.inference.diffusion_engine import DiffusionEngine

router = APIRouter()

# Global instances (Lazy loading or immediate)
# We initialize them immediately here. In a production app, we might use lifespan events.
try:
    print("Initializing Pipeline Models...")
    analyzer = FaceAnalyzer()
    segmenter = HairSegmenter()
    remover = HairRemover()
    extractor = HairColorExtractor()
    warper = HairstyleWarper()
    transfer = HairColorTransfer()
    overlay_engine = FinalOverlayEngine()
    face_shape_classifier = FaceShapeClassifier()
    recommender = HairstyleRecommender()
    diffusion_engine = DiffusionEngine()
    MODELS_LOADED = True
    print("Pipeline Models Initialized Successfully.")
except Exception as e:
    print(f"CRITICAL: Failed to initialize pipeline models: {e}")
    MODELS_LOADED = False

@router.get("/hairstyles")
async def get_available_hairstyles():
    """
    Returns a list of available hairstyles grouped by category, including a thumbnail URL
    for each item so the frontend can render previews before generation.
    """
    data = hairstyle_loader.list_available_styles()
    # Enrich with image_url the frontend can use directly; choose base by source
    enriched = {}
    for cat, items in data.items():
        new_items = []
        for it in items:
            val = it.get('value')
            source = it.get('source', 'cleaned')
            if isinstance(val, str):
                if source == 'cleaned':
                    image_url = f"/hairstyle-assets/{val}"
                elif source == 'orig':
                    image_url = f"/hairstyle-assets-orig/{val}"
                elif source == 'raw':
                    image_url = f"/hairstyle-assets-raw/{val}"
                else:
                    image_url = f"/hairstyle-assets/{val}"
                image_url = image_url.replace('\\', '/')
            else:
                image_url = None
            new_items.append({**it, 'image_url': image_url})
        enriched[cat] = new_items
    return enriched


@router.post("/analyze-face-shape")
async def analyze_face_shape(image: UploadFile = File(...)):
    """
    Independent analysis endpoint.
    - Reuses FaceAnalyzer to compute landmarks
    - Computes geometry-based face shape
    - Returns recommended hairstyles (filtered to available)
    Rendering pipeline remains untouched.
    """
    if not MODELS_LOADED:
        raise HTTPException(status_code=500, detail="Server models failed to initialize.")

    try:
        file_bytes = await image.read()
        np_buf = np.frombuffer(file_bytes, dtype=np.uint8)
        face_bgr = cv2.imdecode(np_buf, cv2.IMREAD_COLOR)
        if face_bgr is None:
            raise HTTPException(status_code=400, detail="Invalid image data.")

        analysis_result = analyzer.detect_landmarks(face_bgr)
        if not analysis_result or not analysis_result.get('face_detected'):
            raise HTTPException(status_code=422, detail="No face detected in the image.")

        landmarks_pixel = analysis_result['landmarks_pixel']
        head_pose       = analysis_result.get('head_pose', {})

        # Warn if the face is significantly turned — results will be less accurate
        is_front_facing = head_pose.get('is_front_facing', True)

        # Now passing face_bgr to utilise the ML classifier when weights are present
        fs_result = face_shape_classifier.analyze(landmarks_pixel, face_bgr=face_bgr)

        # Gather available style values
        available = hairstyle_loader.list_available_styles()
        available_values = []
        for _, items in available.items():
            for it in items:
                val = it.get('value')
                if isinstance(val, str):
                    available_values.append(val)

        rec_values, reasons = recommender.recommend_with_reasons(fs_result['face_shape'], available_values)

        return {
            'face_shape':      fs_result['face_shape'],
            'confidence':      fs_result.get('confidence', None),
            'scores':          fs_result.get('scores', {}),
            'method':          fs_result.get('method', 'geometric'),
            'metrics':         fs_result['metrics'],
            'head_pose':       head_pose,
            'is_front_facing': is_front_facing,
            'recommended':     rec_values,
            'reasons':         reasons,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Analyze Face Shape Error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@router.post("/preview")
async def create_hairstyle_preview(
    image: UploadFile = File(...),
    hairstyle: str = Form(...),
):
    """
    Orchestrates the full hairstyle preview pipeline:
    1. Face Analysis & Landmarks
    2. Hair Segmentation
    3. Hair Removal
    4. Template Processing & Warping
    5. Color Transfer (Optional/TODO)
    6. Final Overlay
    """
    if not MODELS_LOADED:
        raise HTTPException(status_code=500, detail="Server models failed to initialize.")

    try:
        # 1. Read Uploaded Image
        file_bytes = await image.read()
        np_buf = np.frombuffer(file_bytes, dtype=np.uint8)
        face_bgr = cv2.imdecode(np_buf, cv2.IMREAD_COLOR)
        if face_bgr is None:
            raise HTTPException(status_code=400, detail="Invalid image data.")

        # 2. Face Analysis
        analysis_result = analyzer.detect_landmarks(face_bgr)
        if not analysis_result or not analysis_result.get('face_detected'):
            raise HTTPException(status_code=422, detail="No face detected in the image.")
        
        target_landmarks = np.array(analysis_result['landmarks_pixel'], dtype=np.float32)

        # 3. Hair Segmentation
        hair_mask = segmenter.segment_hair(face_bgr)

        # 4. Use Generative Diffusion Engine to synthesize the new hairstyle
        # We pass the requested hairstyle as a prompt parameter
        # If the requested hairstyle is a filename like 'fade.png', we strip the extension
        target_style_name = os.path.splitext(hairstyle)[0].replace('_', ' ')
        
        try:
            # We use the diffusion engine to generate realistic hair.
            final_bgr = diffusion_engine.generate_hair(
                face_image=face_bgr, 
                hair_mask=hair_mask, 
                target_style_name=target_style_name
            )
        except Exception as e:
            print(f"Diffusion failed, falling back to basic overlay: {e}")
            # Fallback to standard overlay if Diffusion OOMs or fails
            hair_removed_img = remover.remove_hair(face_bgr, hair_mask)
            template_bgra = hairstyle_loader.load_template(hairstyle)
            template_rgb = template_bgra[:, :, :3]
            template_alpha_orig = template_bgra[:, :, 3]
            t_result = analyzer.detect_landmarks(template_rgb)
            template_landmarks = np.array(t_result['landmarks_pixel'], dtype=np.float32) if t_result else None
            template_hair_mask = segmenter.segment_hair(template_rgb)
            template_alpha = cv2.bitwise_and(template_alpha_orig, template_hair_mask)
            h, w = face_bgr.shape[:2]
            warped_rgb, warped_alpha = warper.warp_hairstyle(
                template_rgb, template_alpha, target_landmarks, template_landmarks, output_shape=(h, w)
            )
            color_stats = extractor.extract_color_stats(face_bgr, hair_mask)
            warped_rgb = transfer.transfer_color(warped_rgb, warped_alpha, color_stats)
            final_bgr = overlay_engine.overlay(face_bgr, hair_removed_img, warped_rgb, warped_alpha, hair_mask)

        # 5. Encode Response
        ok, encoded = cv2.imencode('.jpg', final_bgr)
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to encode output image.")

        return Response(content=encoded.tobytes(), media_type="image/jpeg")

    except HTTPException:
        raise
    except Exception as e:
        # Log error
        print(f"Pipeline Error: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")
