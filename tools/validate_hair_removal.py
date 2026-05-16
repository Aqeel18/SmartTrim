import cv2
import numpy as np
import os
import sys

# Ensure we can import from app
sys.path.append(os.getcwd())

from app.core.hair_segmentation import HairSegmenter
from app.core.hair_removal import HairRemover

def main():
    image_path = "test_images/Muhammed Aqeel Haroon.jpg"
    output_path = "test_images/validation_hair_removal.png"

    if not os.path.exists(image_path):
        print(f"Error: Test image not found at {image_path}")
        return

    print(f"Loading image from {image_path}...")
    original_image = cv2.imread(image_path)
    if original_image is None:
        print("Error: Failed to load image.")
        return

    # 1. Segment Hair
    print("Initializing HairSegmenter...")
    try:
        segmenter = HairSegmenter()
        hair_mask = segmenter.segment_hair(original_image)
    except Exception as e:
        print(f"Error during segmentation: {e}")
        return

    # 2. Remove Hair
    print("Initializing HairRemover...")
    try:
        remover = HairRemover(inpaint_radius=9)
        hair_removed_image = remover.remove_hair(original_image, hair_mask)
    except Exception as e:
        print(f"Error during hair removal: {e}")
        return

    # 3. Create Visualization
    print("Creating visualization...")
    
    # Convert mask to 3-channel BGR for concatenation
    hair_mask_bgr = cv2.cvtColor(hair_mask, cv2.COLOR_GRAY2BGR)
    
    # Concatenate: Original | Mask | Result
    # Resize for better viewing if too large (optional, but good for side-by-side)
    # Keeping original size for pixel-peeping accuracy
    
    comparison = cv2.hconcat([original_image, hair_mask_bgr, hair_removed_image])
    
    cv2.imwrite(output_path, comparison)
    print(f"Validation result saved to {output_path}")
    print("Check the image to ensure:")
    print("1. Hair region is filled (inpainted).")
    print("2. Non-hair regions (face features) are preserved.")
    print("3. No obvious artifacts outside the hair region.")

if __name__ == "__main__":
    main()

