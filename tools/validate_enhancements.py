import cv2
import numpy as np
import os
import sys

# Ensure we can import from app
sys.path.append(os.getcwd())

from app.core.face_analysis import FaceAnalyzer
from app.core.hair_segmentation import HairSegmenter
from app.core.hair_removal import HairRemover
from app.core.color_extraction import HairColorExtractor
from app.core.warp import HairstyleWarper
from app.core.color_transfer import HairColorTransfer
from app.core.overlay import FinalOverlayEngine

def main():
    print("=== SmartTrim_360: Validation of Realism Enhancements ===")
    
    # 1. Load Input Image
    image_path = "test_images/Muhammed Aqeel Haroon.jpg"
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        return

    original_image = cv2.imread(image_path)
    if original_image is None:
        print("Failed to load image.")
        return
    
    h, w = original_image.shape[:2]
    print(f"Loaded image: {w}x{h}")

    # 2. Initialize Modules
    print("Initializing modules...")
    try:
        analyzer = FaceAnalyzer()
        segmenter = HairSegmenter()
        remover = HairRemover()
        extractor = HairColorExtractor()
        warper = HairstyleWarper()
        transfer = HairColorTransfer()
        overlay_engine = FinalOverlayEngine()
    except Exception as e:
        print(f"Initialization failed: {e}")
        return

    # 3. Pipeline Execution
    try:
        # Step A: Face Analysis
        print("A. Analyzing face...")
        analysis_result = analyzer.detect_landmarks(original_image)
        if not analysis_result or not analysis_result.get('face_detected'):
            print("No face detected.")
            return
        
        target_landmarks = np.array(analysis_result['landmarks_pixel'], dtype=np.float32)
        
        # Step B: Segmentation
        print("B. Segmenting hair...")
        hair_mask = segmenter.segment_hair(original_image)

        # Step C: Hair Removal
        print("C. Removing hair...")
        hair_removed_img = remover.remove_hair(original_image, hair_mask)

        # Step D: Color Extraction
        print("D. Extracting hair color...")
        color_stats = extractor.extract_color_stats(original_image, hair_mask)

        # Step E: Processing 'quiff.png' template
        print("E. Processing 'quiff.png' template...")
        template_path = os.path.join("app", "assets", "hairstyles", "quiff.png")
        if not os.path.exists(template_path):
            print(f"Template not found: {template_path}")
            return
        
        template_original = cv2.imread(template_path)
        
        # E1. Detect Landmarks on Template
        t_result = analyzer.detect_landmarks(template_original)
        template_landmarks = None
        if t_result and t_result.get('face_detected') and t_result['landmarks_pixel']:
            template_landmarks = np.array(t_result['landmarks_pixel'], dtype=np.float32)

        # E2. Segment Hair on Template
        template_mask = segmenter.segment_hair(template_original)
        
        # Refine Mask
        kernel_close = np.ones((5, 5), np.uint8)
        template_mask = cv2.morphologyEx(template_mask, cv2.MORPH_CLOSE, kernel_close)
        kernel_open = np.ones((3, 3), np.uint8)
        template_mask = cv2.morphologyEx(template_mask, cv2.MORPH_OPEN, kernel_open)

        template_rgb = template_original
        template_alpha = template_mask

        # Step F: Warping
        print("F. Warping hairstyle template...")
        warped_rgb, warped_alpha = warper.warp_hairstyle(
            template_rgb, 
            template_alpha, 
            target_landmarks, 
            template_landmarks=template_landmarks, 
            output_shape=(h, w)
        )

        # Step G: Color Transfer
        print("G. Transferring color...")
        recolored_hair = transfer.transfer_color(warped_rgb, warped_alpha, color_stats)
        
        # Step H: Simulate "Before Enhancement" (Simple Blend)
        print("H. Generating 'Before Enhancement' baseline...")
        
        # Simple blend logic similar to previous implementation
        # Constrain alpha with mask but no fancy edge or shadow
        alpha_f = warped_alpha.astype(np.float32) / 255.0
        seg_mask_f = hair_mask.astype(np.float32) / 255.0
        # Simple dilation
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        seg_dilated = cv2.dilate(seg_mask_f, kernel, iterations=1)
        alpha_simple = alpha_f * seg_dilated
        # Simple blur
        alpha_simple = cv2.GaussianBlur(alpha_simple, (5, 5), 0)
        
        alpha_3c = np.dstack([alpha_simple] * 3)
        before_result = (recolored_hair.astype(np.float32) * alpha_3c + 
                         hair_removed_img.astype(np.float32) * (1.0 - alpha_3c))
        before_result = np.clip(before_result, 0, 255).astype(np.uint8)

        # Step I: Final Overlay with Enhancements
        print("I. Blending final result with Realism Enhancements...")
        
        final_result = overlay_engine.overlay(
            original_image,
            hair_removed_img,
            recolored_hair,
            warped_alpha,
            hair_region_mask=hair_mask
        )
        
        # 4. Save and Visualize
        print("Saving results...")
        
        output_path = "test_images/validation_realism_enhancements.png"
        
        # Resize images if needed
        if hair_removed_img.shape != original_image.shape:
            hair_removed_img = cv2.resize(hair_removed_img, (w, h))
            
        # Comparison: [Original | Before (Standard) | After (Enhanced)]
        # Adding labels would be nice but simple stacking is fine
        combined = np.hstack([original_image, before_result, final_result])
        
        cv2.imwrite(output_path, combined)
        print(f"Validation result saved to {output_path}")

    except Exception as e:
        print(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
