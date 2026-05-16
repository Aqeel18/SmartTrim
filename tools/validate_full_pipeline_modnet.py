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
    print("=== SmartTrim_360: Full Pipeline Validation (MODNet) ===")
    
    # Paths
    image_path = "test_images/Muhammed Aqeel Haroon.jpg"
    template_path = os.path.join("app", "assets", "cleaned_hairstyles", "quiff.png")
    output_path = "test_images/full_pipeline_modnet_validation.png"
    
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        return
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    # Load Original
    original_image = cv2.imread(image_path)
    if original_image is None:
        print("Failed to load original image.")
        return
    h, w = original_image.shape[:2]
    
    # Initialize Modules
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
    
    # 1. Face Analysis & Landmarks
    print("1. Face Analysis...")
    analysis_result = analyzer.detect_landmarks(original_image)
    if not analysis_result or not analysis_result.get('face_detected'):
        print("No face detected.")
        return
    target_landmarks = np.array(analysis_result['landmarks_pixel'], dtype=np.float32)
    
    # 2. Segmentation (BiSeNet) -> Hair Mask
    print("2. Segmentation...")
    hair_mask = segmenter.segment_hair(original_image)
    # Visual: Hair Mask (Grayscale to BGR)
    hair_mask_visual = cv2.cvtColor(hair_mask, cv2.COLOR_GRAY2BGR)
    
    # 3. Hair Removal
    print("3. Hair Removal...")
    hair_removed_img = remover.remove_hair(original_image, hair_mask)
    
    # 4. Process Template (Cleaned Asset)
    print("4. Processing Template...")
    template_rgba = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
    if template_rgba is None:
        print("Failed to load template.")
        return
        
    template_rgb = template_rgba[:, :, :3]
    template_alpha_orig = template_rgba[:, :, 3]
    
    # 4a. Template Landmarks
    t_result = analyzer.detect_landmarks(template_rgb)
    if t_result and t_result.get('face_detected'):
        template_landmarks = np.array(t_result['landmarks_pixel'], dtype=np.float32)
    else:
        template_landmarks = None # Warper might fail or fallback
        print("Warning: No face in template.")
        
    # 4b. Template Hair Segmentation
    # We want ONLY hair from the template.
    template_hair_mask = segmenter.segment_hair(template_rgb)
    
    # Combine MODNet Alpha with BiSeNet Hair Mask
    # Using logical AND equivalent for byte images
    template_alpha = cv2.bitwise_and(template_alpha_orig, template_hair_mask)
    
    # 5. Warping
    print("5. Warping...")
    warped_rgb, warped_alpha = warper.warp_hairstyle(
        template_rgb, 
        template_alpha, 
        target_landmarks, 
        template_landmarks=template_landmarks, 
        output_shape=(h, w)
    )
    
    # Visual: Warped Template (Composite over black)
    warped_visual = np.zeros_like(original_image)
    alpha_f = warped_alpha.astype(float) / 255.0
    for c in range(3):
        warped_visual[:, :, c] = (warped_rgb[:, :, c] * alpha_f).astype(np.uint8)
        
    # 6. Color Extraction & Transfer
    print("6. Color Transfer...")
    color_stats = extractor.extract_color_stats(original_image, hair_mask)
    recolored_hair = transfer.transfer_color(warped_rgb, warped_alpha, color_stats)
    
    # Visual: Color Matched (Composite over black)
    recolored_visual = np.zeros_like(original_image)
    for c in range(3):
        recolored_visual[:, :, c] = (recolored_hair[:, :, c] * alpha_f).astype(np.uint8)
        
    # 7. Final Overlay
    print("7. Overlay...")
    final_result = overlay_engine.overlay(
        original_image,
        hair_removed_img,
        recolored_hair,
        warped_alpha,
        hair_region_mask=hair_mask
    )
    
    # 8. Create Comparison Image
    # [ Original | Hair Mask | Hair Removed | Warped Template | Color Matched | FINAL RESULT ]
    
    row = np.hstack([
        original_image,
        hair_mask_visual,
        hair_removed_img,
        warped_visual,
        recolored_visual,
        final_result
    ])
    
    cv2.imwrite(output_path, row)
    print(f"Saved full pipeline validation to {output_path}")

if __name__ == "__main__":
    main()
