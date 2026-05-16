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
    print("=== SmartTrim_360: Applying 'Hair-Only' Asset ===")
    
    # 1. Load Input Image
    image_path = os.path.join("test_images", "Muhammed Aqeel Haroon.jpg")
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
        import traceback
        traceback.print_exc()
        return

    # 3. Pipeline Execution
    try:
        # A. Analyze face landmarks for warping
        print("A. Analyzing face...")
        analysis_result = analyzer.detect_landmarks(original_image)
        if not analysis_result or not analysis_result.get('face_detected'):
            print("No face detected.")
            return
        target_landmarks = np.array(analysis_result['landmarks_pixel'], dtype=np.float32)
        print(f"   Face detected. Landmarks: {len(target_landmarks)}")

        # B. Segment hair on target
        print("A. Segmenting hair on target...")
        hair_mask = segmenter.segment_hair(original_image)

        # C. Remove target hair (with root preservation and seam blending)
        print("B. Removing target hair...")
        hair_removed_img = remover.remove_hair(original_image, hair_mask)

        # D. Extract target hair color statistics
        print("C. Extracting hair color...")
        color_stats = extractor.extract_color_stats(original_image, hair_mask)
        print(f"   Median Color (L,A,B): {color_stats['lab_median']}")

        # E. Load hair-only template (RGBA)
        print("D. Loading hair-only template...")
        template_path = os.path.join("app", "assets", "hairstyles", "hair-only.png")
        if not os.path.exists(template_path):
            print(f"Template not found: {template_path}")
            return

        template_rgba = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
        if template_rgba is None or template_rgba.shape[2] != 4:
            print("Failed to load RGBA hair-only asset.")
            return

        b, g, r, a = cv2.split(template_rgba)
        template_rgb = cv2.merge([b, g, r])
        template_alpha = a

        # F. Warp hairstyle to target geometry
        print("E. Warping hairstyle template...")
        warped_rgb, warped_alpha = warper.warp_hairstyle(
            template_rgb,
            template_alpha,
            # Landmarks from target face
            face_landmarks=target_landmarks,
            template_landmarks=None,
            output_shape=(h, w)
        )

        # G. Color transfer to match target hair color
        print("F. Transferring color...")
        recolored_hair = transfer.transfer_color(warped_rgb, warped_alpha, color_stats)

        # H. Final overlay restricted to segmented hair region
        print("G. Blending final result with corrective integration...")
        final_result = overlay_engine.overlay(
            original_image,
            hair_removed_img,
            recolored_hair,
            warped_alpha,
            hair_region_mask=hair_mask
        )

        # I. Save side-by-side comparison
        print("Saving results...")
        output_path = os.path.join("test_images", "output_hair_only_tryon.png")
        combined = np.hstack([original_image, final_result])
        cv2.imwrite(output_path, combined)
        print(f"Result saved to {output_path}")

    except Exception as e:
        print(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
