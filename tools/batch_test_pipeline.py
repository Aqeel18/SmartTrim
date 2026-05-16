import os
import sys
import cv2
import numpy as np
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.face_analysis import FaceAnalyzer
from app.core.hair_segmentation import HairSegmenter
from app.core.hair_removal import HairRemover
from app.core.color_extraction import HairColorExtractor
from app.core.warp import HairstyleWarper
from app.core.color_transfer import HairColorTransfer
from app.core.overlay import FinalOverlayEngine
from app.core.hairstyle_templates import hairstyle_loader

def run_batch_test():
    # Initialize components
    print("Initializing Pipeline Models...")
    try:
        analyzer = FaceAnalyzer()
        segmenter = HairSegmenter()
        remover = HairRemover()
        extractor = HairColorExtractor()
        warper = HairstyleWarper()
        transfer = HairColorTransfer()
        overlay_engine = FinalOverlayEngine()
    except Exception as e:
        print(f"CRITICAL: Failed to initialize pipeline models: {e}")
        return

    faces_root = os.path.join("app", "assets", "faces")
    styles_root = os.path.join("app", "assets", "cleaned_hairstyles")
    results_root = "results"

    if not os.path.exists(results_root):
        os.makedirs(results_root)

    # Restrict testing to men only (app is now men-only)
    categories = ["men"]

    for category in categories:
        face_dir = os.path.join(faces_root, category)
        style_dir = os.path.join(styles_root, category)

        if not os.path.exists(face_dir) or not os.path.exists(style_dir):
            print(f"Skipping {category}: Directory not found.")
            continue

        face_files = [f for f in os.listdir(face_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        style_files = [f for f in os.listdir(style_dir) if f.lower().endswith('.png')]

        if not face_files or not style_files:
            print(f"Skipping {category}: Missing faces or styles.")
            continue

        print(f"\nProcessing {category}: {len(face_files)} faces, {len(style_files)} styles")

        for face_name in face_files:
            face_path = os.path.join(face_dir, face_name)
            face_bgr = cv2.imread(face_path)
            if face_bgr is None:
                print(f"  Failed to read face: {face_name}")
                continue

            # 1. Face Analysis
            analysis_result = analyzer.detect_landmarks(face_bgr)
            if not analysis_result or not analysis_result.get('face_detected'):
                print(f"  No face detected in {face_name}")
                continue
            
            target_landmarks = np.array(analysis_result['landmarks_pixel'], dtype=np.float32)

            # 2. Hair Segmentation
            hair_mask = segmenter.segment_hair(face_bgr)

            # 3. Hair Removal
            hair_removed_img = remover.remove_hair(face_bgr, hair_mask)

            # 4. Color Extraction (for transfer)
            color_stats = extractor.extract_color_stats(face_bgr, hair_mask)

            for style_name in style_files:
                # The loader expects path relative to cleaned_hairstyles
                style_rel_path = f"{category}/{style_name}"
                
                output_dir = os.path.join(results_root, category, os.path.splitext(face_name)[0])
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                output_path = os.path.join(output_dir, style_name.replace('.png', '.jpg'))
                
                # Check if already exists (optional)
                # if os.path.exists(output_path): continue

                try:
                    # 5. Load and Process Template
                    template_bgra = hairstyle_loader.load_template(style_rel_path)
                    template_rgb = template_bgra[:, :, :3]
                    template_alpha_orig = template_bgra[:, :, 3]

                    # 5a. Template Landmarks
                    t_result = analyzer.detect_landmarks(template_rgb)
                    if not t_result or not t_result.get('face_detected'):
                        print(f"    Skipping {style_name}: No face in template.")
                        continue
                    template_landmarks = np.array(t_result['landmarks_pixel'], dtype=np.float32)

                    # 5b. Refine Template Alpha
                    template_hair_mask = segmenter.segment_hair(template_rgb)
                    template_alpha = cv2.bitwise_and(template_alpha_orig, template_hair_mask)

                    # 6. Warping
                    h, w = face_bgr.shape[:2]
                    warped_rgb, warped_alpha = warper.warp_hairstyle(
                        template_rgb,
                        template_alpha,
                        target_landmarks,
                        template_landmarks,
                        output_shape=(h, w)
                    )

                    # 7. Color Transfer
                    processed_warped_rgb = transfer.transfer_color(warped_rgb, warped_alpha, color_stats)
                    
                    # 8. Overlay
                    final_bgr = overlay_engine.overlay(
                        original_face=face_bgr,
                        hair_removed_img=hair_removed_img,
                        warped_hair_rgb=processed_warped_rgb,
                        warped_alpha=warped_alpha,
                        hair_region_mask=hair_mask
                    )

                    # 9. Save result
                    cv2.imwrite(output_path, final_bgr)
                    print(f"    Saved: {category}/{os.path.splitext(face_name)[0]}/{style_name}")

                except Exception as e:
                    print(f"    Error processing {style_name} on {face_name}: {e}")

    print("\nBatch testing completed. Results stored in 'results' folder.")

if __name__ == "__main__":
    run_batch_test()
