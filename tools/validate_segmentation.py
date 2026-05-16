import cv2
import numpy as np
import os
import torch
from app.core.hair_segmentation import HairSegmenter

def validate_segmentation():
    input_path = "test_images/Muhammed Aqeel Haroon.jpg"
    output_path = "test_images/validation_hair_mask.png"
    
    if not os.path.exists(input_path):
        print(f"Error: Input image {input_path} not found.")
        return

    print("Initializing HairSegmenter...")
    try:
        segmenter = HairSegmenter()
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Failed to initialize segmenter: {e}")
        return

    print(f"Loading image from {input_path}...")
    image = cv2.imread(input_path)
    if image is None:
        print("Failed to read image.")
        return

    print("Running segmentation...")
    mask = segmenter.segment_hair(image)
    
    # Convert mask to 3-channel for visualization
    mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    
    # Create a side-by-side comparison
    # Resize mask to match image if needed (segmenter should already do this, but safe to check)
    if mask_bgr.shape != image.shape:
        print(f"Warning: Mask shape {mask_bgr.shape} differs from image {image.shape}. Resizing mask.")
        mask_bgr = cv2.resize(mask_bgr, (image.shape[1], image.shape[0]))

    # Create a green overlay on the original image where hair is detected
    overlay = image.copy()
    overlay[mask == 255] = [0, 255, 0]  # Green hair
    combined_overlay = cv2.addWeighted(image, 0.7, overlay, 0.3, 0)

    # Stack: Original | Mask | Green Overlay
    comparison = np.hstack([image, mask_bgr, combined_overlay])
    
    cv2.imwrite(output_path, comparison)
    print(f"Validation result saved to {output_path}")
    print("Check the image to ensure:")
    print("1. Hair is cleanly segmented (middle image is white on hair)")
    print("2. No skin/background included")
    print("3. Green overlay (right image) aligns with hair")

if __name__ == "__main__":
    validate_segmentation()

