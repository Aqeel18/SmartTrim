import cv2
import numpy as np
import os
import sys

# Ensure we can import from app
sys.path.append(os.getcwd())

from app.core.warp import HairstyleWarper

def main():
    # 1. Create a dummy hairstyle template (Circle)
    print("Creating dummy hairstyle template...")
    template_size = 512
    template_rgb = np.zeros((template_size, template_size, 3), dtype=np.uint8)
    template_rgb[:] = (50, 50, 50) # Dark gray background (irrelevant where alpha is 0)
    
    # Draw a "wig" shape: A semi-circle/ellipse at the top
    center = (template_size // 2, template_size // 2)
    axes = (150, 200)
    cv2.ellipse(template_rgb, center, axes, 0, 180, 360, (0, 0, 200), -1) # Red hair
    
    # Create Alpha mask
    template_alpha = np.zeros((template_size, template_size), dtype=np.uint8)
    cv2.ellipse(template_alpha, center, axes, 0, 180, 360, 255, -1)
    
    # Save original template
    cv2.imwrite("test_images/template_original.png", cv2.merge([template_rgb, template_alpha]))

    # 2. Define Dummy Face Landmarks
    # Simulating a face that is slightly wider and shifted to the right
    # Face bbox: x=200, y=200, w=200, h=250
    print("Defining dummy landmarks...")
    
    # Let's create a dummy landmarks array (usually 68 points)
    # We only need enough to drive the bounding box logic in _define_control_points
    # We'll construct points that form a bounding box
    face_landmarks = np.array([
        [200, 200], # Top-Left of bbox
        [400, 200], # Top-Right of bbox
        [400, 450], # Bottom-Right
        [200, 450], # Bottom-Left
        [300, 450]  # Chin
    ], dtype=np.int32)

    # 3. Initialize Warper
    print("Initializing HairstyleWarper...")
    warper = HairstyleWarper()

    # 4. Warp
    print("Warping hairstyle...")
    try:
        warped_rgb, warped_alpha = warper.warp_hairstyle(
            template_rgb,
            template_alpha,
            face_landmarks,
            output_shape=(512, 512)
        )
        
        # 5. Visualization
        print("Saving visualization...")
        # Concatenate for comparison
        # Add alpha to warped RGB for visualization
        warped_rgba = cv2.merge([warped_rgb, warped_alpha])
        
        # Combine side-by-side
        # Create a blank canvas to hold both
        comparison = np.zeros((512, 1024, 3), dtype=np.uint8)
        
        # Original (blended on checkerboard or white)
        comparison[0:512, 0:512] = template_rgb
        # Draw source bbox visualization on original
        # (Optional: call internal method to get points for viz, but private)
        
        # Warped
        comparison[0:512, 512:1024] = warped_rgb
        
        # Draw target landmarks on warped side to see alignment
        lx, ly, lw, lh = cv2.boundingRect(face_landmarks)
        # Shift x by 512 for the right side image
        cv2.rectangle(comparison, (lx + 512, ly), (lx + lw + 512, ly + lh), (0, 255, 0), 2)
        
        cv2.imwrite("test_images/validation_warp.png", comparison)
        print("Validation result saved to test_images/validation_warp.png")
        print("Check if the red 'wig' has moved/stretched to align with the green box on the right.")

    except Exception as e:
        print(f"Error during warping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
