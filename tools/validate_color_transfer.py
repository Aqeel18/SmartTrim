import cv2
import numpy as np
import os
import sys

# Ensure we can import from app
sys.path.append(os.getcwd())

from app.core.color_transfer import HairColorTransfer

def main():
    # 1. Create a dummy "Warped" Hairstyle (Simulating a Blonde Wig)
    print("Creating dummy blonde hairstyle...")
    h, w = 512, 512
    warped_rgb = np.zeros((h, w, 3), dtype=np.uint8)
    # Background (irrelevant)
    warped_rgb[:] = (50, 50, 50)
    
    # Draw "Blonde" Hair (High L, Yellowish)
    # BGR: Yellow is (0, 255, 255). Blonde is lighter/paler, e.g., (150, 220, 240)
    center = (256, 256)
    axes = (100, 150)
    
    # We want some texture/variation for the transfer to preserve
    # Gradient/Noise simulation
    # Simple solid ellipse for now, but let's add some noise
    cv2.ellipse(warped_rgb, center, axes, 0, 0, 360, (180, 230, 250), -1)
    
    # Add some "highlights" (lighter stripes)
    cv2.line(warped_rgb, (256, 150), (256, 350), (220, 250, 255), 20)
    
    # Create Alpha Mask
    warped_alpha = np.zeros((h, w), dtype=np.uint8)
    cv2.ellipse(warped_alpha, center, axes, 0, 0, 360, 255, -1)

    # 2. Define Target Color Stats (e.g., Dark Brown/Black User Hair)
    # From previous validation: Median (25, 128, 123), Std (50, 3, 4)
    print("Defining target color stats (Dark Hair)...")
    target_stats = {
        'lab_median': (25.0, 128.0, 123.0), # Dark/Black
        'lab_std': (50.0, 5.0, 5.0)         # Some lightness variation
    }
    
    # 3. Initialize Transfer
    print("Initializing HairColorTransfer...")
    transfer = HairColorTransfer()

    # 4. Perform Transfer
    print("Applying color transfer...")
    try:
        recolored_rgb = transfer.transfer_color(warped_rgb, warped_alpha, target_stats)
        
        # 5. Visualization
        print("Saving visualization...")
        # Concatenate: Original | Recolored
        comparison = np.hstack([warped_rgb, recolored_rgb])
        
        output_path = "test_images/validation_color_transfer.png"
        cv2.imwrite(output_path, comparison)
        print(f"Validation result saved to {output_path}")
        print("Check if the 'blonde' wig has turned 'dark' while keeping the highlight stripe visible.")

    except Exception as e:
        print(f"Error during color transfer: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
