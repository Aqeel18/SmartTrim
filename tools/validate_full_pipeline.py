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

def create_dummy_template(h=512, w=512):
    """Creates a dummy blonde bob hairstyle template."""
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    alpha = np.zeros((h, w), dtype=np.uint8)
    
    # Draw a bob shape
    # Head center roughly at 256, 200
    center = (256, 200)
    axes = (120, 160) # Width, Height
    
    # Blonde color (BGR)
    color = (180, 230, 250) 
    
    # Draw hair mass
    cv2.ellipse(rgb, center, axes, 0, 0, 180, color, -1) # Top dome
    pts = np.array([
        [center[0] - axes[0], center[1]],
        [center[0] - axes[0], center[1] + 200], # Left drop
        [center[0] + axes[0], center[1] + 200], # Right drop
        [center[0] + axes[0], center[1]]
    ], np.int32)
    cv2.fillPoly(rgb, [pts], color)
    
    # Draw alpha
    cv2.ellipse(alpha, center, axes, 0, 0, 180, 255, -1)
    cv2.fillPoly(alpha, [pts], 255)
    
    # Cut out face area (approximate)
    face_axes = (70, 90)
    face_center = (256, 250)
    cv2.ellipse(rgb, face_center, face_axes, 0, 0, 360, (0,0,0), -1)
    cv2.ellipse(alpha, face_center, face_axes, 0, 0, 360, 0, -1)
    
    return rgb, alpha

def main():
    print("=== SmartTrim_360 Full Pipeline Validation ===")
    
    # 1. Load Input Image
    image_path = "test_images/Muhammed Aqeel Haroon.jpg"
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        return

    original_image = cv2.imread(image_path)
    if original_image is None:
        print("Failed to load image.")
        return
    
    # Resize for consistency/speed (optional, but good for display)
    # Keeping original size is better for quality, but let's ensure it's not massive
    h, w = original_image.shape[:2]
    print(f"Loaded image: {w}x{h}")

    # 2. Initialize Modules
    print("Initializing modules...")
    try:
        analyzer = FaceAnalyzer() # Automatically finds model
        segmenter = HairSegmenter() # Automatically finds model
        remover = HairRemover()
        extractor = HairColorExtractor()
        warper = HairstyleWarper()
        transfer = HairColorTransfer()
        overlay_engine = FinalOverlayEngine()
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
        
        landmarks = np.array(analysis_result['landmarks_pixel'])
        print(f"   Face detected. Landmarks: {len(landmarks)}")
        
        # Step B: Segmentation
        print("B. Segmenting hair...")
        hair_mask = segmenter.segment_hair(original_image)
        # Visualize mask (optional, handled by result image)

        # Step C: Hair Removal
        print("C. Removing hair...")
        hair_removed_img = remover.remove_hair(original_image, hair_mask)

        # Step D: Color Extraction
        print("D. Extracting hair color...")
        color_stats = extractor.extract_color_stats(original_image, hair_mask)
        print(f"   Median Color (L,A,B): {color_stats['lab_median']}")

        # Step E: Prepare Template (Warping)
        print("E. Warping hairstyle template...")
        
        # Try to load real template
        template_path = "test_images/template_original.png"
        if os.path.exists(template_path):
            print(f"   Loading template from {template_path}")
            template_img = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
            if template_img is not None and template_img.shape[2] == 4:
                template_rgb = template_img[:, :, :3]
                template_alpha = template_img[:, :, 3]
            else:
                print("   Template invalid or no alpha. Using dummy.")
                template_rgb, template_alpha = create_dummy_template()
        else:
            print("   Template file not found. Using dummy.")
            template_rgb, template_alpha = create_dummy_template()
        
        # Warp it to the face
        # Note: HairstyleWarper expects landmarks.
        # It also accepts an optional hair_region_poly (not mask).
        # We can pass None for poly if we trust landmarks.
        # Ensure output matches original image size
        h, w = original_image.shape[:2]
        warped_rgb, warped_alpha = warper.warp_hairstyle(
            template_rgb, template_alpha, landmarks, None, output_shape=(h, w)
        )

        # Step F: Color Transfer
        print("F. Transferring color...")
        # Apply user's hair color to the warped template
        recolored_hair = transfer.transfer_color(warped_rgb, warped_alpha, color_stats)

        # Step G: Hair Estimation (Optional Masking)
        print("G. Estimating scalp region...")
        # We can use this to constrain the overlay if needed.
        est_result = estimate_hair(landmarks, original_image.shape)
        hair_region_mask = est_result['mask'] if est_result['success'] else None

        # Step H: Final Overlay
        print("H. Blending final result...")
        # Note: We can try with and without the hair_region_mask to see the difference.
        # For now, let's use it as requested by the user, but handle it carefully.
        # If the generated wig is long, hair_region_mask might cut it.
        # Given the "bob" shape, it might be okay.
        final_result = overlay_engine.overlay(
            original_image,
            hair_removed_img,
            recolored_hair,
            warped_alpha,
            hair_region_mask=hair_mask # Set to hair_region_mask to test restriction, None for full wig
        )
        
        # 4. Save and Visualize
        print("Saving results...")
        
        # Create comparison grid
        # Resize all to match if needed (they should match)
        
        # Row 1: Original | Hair Removed
        row1 = np.hstack([original_image, hair_removed_img])
        
        # Row 2: Warped Wig (Colored) | Final Result
        # Warped wig is on black background for visualization
        wig_vis = cv2.bitwise_and(recolored_hair, recolored_hair, mask=warped_alpha)
        # Make background gray for better visibility
        wig_bg = np.full_like(recolored_hair, 128)
        wig_vis_final = np.where(warped_alpha[:,:,None] > 0, wig_vis, wig_bg)
        
        row2 = np.hstack([wig_vis_final, final_result])
        
        full_grid = np.vstack([row1, row2])
        
        output_path = "test_images/validation_full_pipeline.png"
        cv2.imwrite(output_path, full_grid)
        print(f"Full pipeline validation saved to {output_path}")

    except Exception as e:
        print(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()







