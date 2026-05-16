import cv2
import numpy as np
import os
import sys

# Ensure we can import from app
sys.path.append(os.getcwd())

from app.core.hair_segmentation import HairSegmenter
from app.core.hair_removal import HairRemover

def main():
    print("=== Validation: Hair Removal Fix ===")
    
    # 1. Load Input Image
    image_path = "test_images/Muhammed Aqeel Haroon.jpg"
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        return

    original_image = cv2.imread(image_path)
    if original_image is None:
        print("Failed to load image.")
        return
    
    print(f"Loaded image: {original_image.shape}")

    # 2. Segment Hair
    print("Segmenting hair...")
    segmenter = HairSegmenter()
    hair_mask = segmenter.segment_hair(original_image)
    
    # 3. Remove Hair (Current Implementation)
    print("Removing hair...")
    remover = HairRemover()
    
    hair_removed = remover.remove_hair(original_image, hair_mask)
    
    output_path = "test_images/validation_hair_removal_before.png"
    # If "before" exists, save as "after"
    if os.path.exists(output_path):
        output_path = "test_images/validation_hair_removal_after.png"
        
    cv2.imwrite(output_path, hair_removed)
    print(f"Saved hair removal result to {output_path}")

    # If we have both, create a comparison
    if os.path.exists("test_images/validation_hair_removal_before.png") and \
       os.path.exists("test_images/validation_hair_removal_after.png"):
        before = cv2.imread("test_images/validation_hair_removal_before.png")
        after = cv2.imread("test_images/validation_hair_removal_after.png")
        
        # Ensure dimensions match
        h, w = before.shape[:2]
        if after.shape[:2] != (h, w):
            after = cv2.resize(after, (w, h))
            
        comparison = np.hstack([before, after])
        cv2.imwrite("test_images/validation_hair_removal_comparison.png", comparison)
        print("Comparison saved to test_images/validation_hair_removal_comparison.png")

if __name__ == "__main__":
    main()
