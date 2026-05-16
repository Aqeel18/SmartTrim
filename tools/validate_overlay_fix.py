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
from app.core.hair_estimation import estimate_hair
from app.core.hairstyle_templates import HairstyleTemplateLoader

def main():
    print("=== SmartTrim_360: Validation of Overlay Corrective Integration ===")
    
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
        loader = HairstyleTemplateLoader()
    except Exception as e:
        print(f"Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. Pipeline Execution
    try:
        # Step A: Face Analysis
        print("A. Analyzing face...")
        analysis_result = analyzer.detect_landmarks(original_image)
        if not analysis_result or not analysis_result.get('face_detected'):
            print("No face detected.")
            return
        
        # Get the landmarks (it returns a flat list for the single face detected)
        target_landmarks = np.array(analysis_result['landmarks_pixel'], dtype=np.float32)
        print(f"   Face detected. Landmarks: {len(target_landmarks)}")
        
        # Step B: Segmentation
        print("B. Segmenting hair...")
        hair_mask = segmenter.segment_hair(original_image)

        # Step C: Hair Removal
        print("C. Removing hair...")
        hair_removed_img = remover.remove_hair(original_image, hair_mask)

        # Step D: Color Extraction
        print("D. Extracting hair color...")
        color_stats = extractor.extract_color_stats(original_image, hair_mask)
        print(f"   Median Color (L,A,B): {color_stats['lab_median']}")

        # Step E: Load and Process Template (Raw Image)
        print("E. Processing 'quiff.png' template...")
        template_path = os.path.join("app", "assets", "hairstyles", "quiff.png")
        if not os.path.exists(template_path):
            print(f"Template not found: {template_path}")
            return
        
        template_original = cv2.imread(template_path)
        if template_original is None:
            print("Failed to load template image.")
            return

        # E1. Detect Landmarks on Template
        print("   Analyzing template face...")
        t_result = analyzer.detect_landmarks(template_original)
        template_landmarks = None
        if t_result and t_result.get('face_detected') and t_result['landmarks_pixel']:
            template_landmarks = np.array(t_result['landmarks_pixel'], dtype=np.float32)
            print(f"   Template face detected. Landmarks: {len(template_landmarks)}")
        else:
            print("   No face detected in template. Using bounding box fallback.")

        # E2. Segment Hair on Template
        print("   Segmenting template hair...")
        template_mask = segmenter.segment_hair(template_original)
        
        # Refine Mask to remove roughness
        print("   Refining template mask...")
        # 1. Morphological Closing to fill small holes
        kernel_close = np.ones((5, 5), np.uint8)
        template_mask = cv2.morphologyEx(template_mask, cv2.MORPH_CLOSE, kernel_close)
        
        # 2. Morphological Opening to remove noise/rough edges
        kernel_open = np.ones((3, 3), np.uint8)
        template_mask = cv2.morphologyEx(template_mask, cv2.MORPH_OPEN, kernel_open)

        # Use the original image and generated mask
        template_rgb = template_original
        template_alpha = template_mask

        # Step F: Warping
        print("F. Warping hairstyle template...")
        # Ensure output matches original image size
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
        
        # Step I: Final Overlay
        print("I. Blending final result with Corrective Integration...")
        # FIX: Pass the authoritative BiSeNet hair_mask from Step B
        final_result = overlay_engine.overlay(
            original_image,
            hair_removed_img,
            recolored_hair,
            warped_alpha,
            hair_region_mask=hair_mask  # Use BiSeNet mask!
        )
        
        # 4. Save and Visualize
        print("Saving results...")
        
        output_path = "test_images/validation_overlay_fix.png"
        
        # Create a side-by-side comparison: [Original | Hair Removed | Final]
        # Ensure hair_removed_img is same size
        if hair_removed_img.shape != original_image.shape:
            hair_removed_img = cv2.resize(hair_removed_img, (w, h))
        
        combined = np.hstack([original_image, hair_removed_img, final_result])
        
        cv2.imwrite(output_path, combined)
        print(f"Validation result saved to {output_path}")

    except Exception as e:
        print(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
