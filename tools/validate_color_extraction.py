import cv2
import numpy as np
import os
import sys

# Ensure we can import from app
sys.path.append(os.getcwd())

from app.core.hair_segmentation import HairSegmenter
from app.core.color_extraction import HairColorExtractor

def main():
    image_path = "test_images/Muhammed Aqeel Haroon.jpg"
    
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

    # 2. Extract Color
    print("Initializing HairColorExtractor...")
    extractor = HairColorExtractor()
    
    try:
        stats = extractor.extract_color_stats(original_image, hair_mask)
        
        print("\n--- Extracted Color Statistics (LAB) ---")
        print(f"Pixel Count: {stats['pixel_count']}")
        print(f"Median (L, A, B): ({stats['lab_median'][0]:.2f}, {stats['lab_median'][1]:.2f}, {stats['lab_median'][2]:.2f})")
        print(f"Std Dev (L, A, B): ({stats['lab_std'][0]:.2f}, {stats['lab_std'][1]:.2f}, {stats['lab_std'][2]:.2f})")
        
        # 3. Create Visualization Swatch
        # Create a 200x200 swatch of the median color
        # Convert median LAB back to BGR for display
        median_lab = np.array([[stats['lab_median']]], dtype=np.uint8)
        median_bgr = cv2.cvtColor(median_lab, cv2.COLOR_LAB2BGR)[0,0]
        
        swatch = np.zeros((200, 200, 3), dtype=np.uint8)
        swatch[:] = median_bgr
        
        # Add text
        text = f"L:{stats['lab_median'][0]:.0f} A:{stats['lab_median'][1]:.0f} B:{stats['lab_median'][2]:.0f}"
        cv2.putText(swatch, text, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255) if stats['lab_median'][0] < 128 else (0, 0, 0), 2)
        
        output_path = "test_images/validation_color_swatch.png"
        cv2.imwrite(output_path, swatch)
        print(f"\nColor swatch saved to {output_path}")
        
    except Exception as e:
        print(f"Error during color extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
