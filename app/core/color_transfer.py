import cv2
import numpy as np
from typing import Dict, Tuple

class HairColorTransfer:
    """
    Transfers the user's hair color onto a hairstyle template using statistical color transfer.
    Operates in LAB color space to preserve texture while modifying color and lightness.
    """

    def transfer_color(
        self,
        warped_rgb: np.ndarray,
        warped_alpha: np.ndarray,
        hair_color_stats: Dict[str, Tuple[float, float, float]]
    ) -> np.ndarray:
        """
        Apply color transfer to the warped hairstyle.

        Args:
            warped_rgb (np.ndarray): Warped hairstyle RGB/BGR image (H, W, 3).
            warped_alpha (np.ndarray): Alpha mask (H, W).
            hair_color_stats (Dict): Source color stats with 'lab_median' and 'lab_std'.

        Returns:
            np.ndarray: Recolored RGB/BGR image (H, W, 3).
        """
        # 1. Validate inputs
        if warped_rgb is None or warped_alpha is None:
            raise ValueError("Input image and mask cannot be None.")
        
        if warped_rgb.shape[:2] != warped_alpha.shape[:2]:
            raise ValueError("Image and mask dimensions must match.")

        # 2. Extract Template Hair Pixels
        # We only want to process pixels that are part of the hairstyle (alpha > 0)
        # Using a threshold to avoid processing faint anti-aliased edges which might skew stats
        mask_indices = np.where(warped_alpha > 10)
        
        if len(mask_indices[0]) == 0:
            # No hair pixels, return original
            return warped_rgb.copy()

        # Extract pixels: (N, 3)
        # Note: warped_rgb is BGR if loaded via cv2.imread
        template_pixels_bgr = warped_rgb[mask_indices]

        # 3. Convert to LAB Color Space
        # Reshape for cv2.cvtColor: (1, N, 3)
        template_pixels_bgr_reshaped = template_pixels_bgr.reshape(1, -1, 3)
        template_pixels_lab = cv2.cvtColor(template_pixels_bgr_reshaped, cv2.COLOR_BGR2LAB)
        
        # Flatten: (N, 3) and convert to float for math
        template_pixels_lab = template_pixels_lab.reshape(-1, 3).astype(np.float32)

        # 4. Compute Template Statistics
        # We compute mean/std of the TEMPLATE hair to normalize it
        # We use mean here because standard Reinhard transfer uses mean/std.
        # However, if the template has strong highlights, median might be safer for the "center" 
        # but scaling is usually done around the mean.
        # Let's stick to mean/std for the template to standardize it.
        t_mean = np.mean(template_pixels_lab, axis=0)
        t_std = np.std(template_pixels_lab, axis=0) + 1e-5 # Avoid divide by zero

        # 5. Get User Hair Statistics
        # The user stats might be median/std as requested by the Extractor module.
        u_mean = np.array(hair_color_stats['lab_median'], dtype=np.float32)
        u_std = np.array(hair_color_stats['lab_std'], dtype=np.float32)

        # 6. Apply Color Transfer (Reinhard Method)
        # Formula: result = (template - t_mean) * (u_std / t_std) + u_mean
        # This shifts the template distribution to match the user's distribution.
        
        # Normalize (Center at 0 with unit variance)
        normalized = (template_pixels_lab - t_mean) / t_std
        
        # Scale and Shift to User's distribution
        # We can control the strength of transfer here. 
        # For now, full transfer.
        transferred_pixels_lab = (normalized * u_std) + u_mean

        # 7. Clip and Convert back
        # LAB ranges in OpenCV: L [0, 255], A [0, 255], B [0, 255] (for 8-bit)
        transferred_pixels_lab = np.clip(transferred_pixels_lab, 0, 255)
        
        # Convert back to uint8
        transferred_pixels_lab_uint8 = transferred_pixels_lab.astype(np.uint8)
        
        # Reshape for conversion: (1, N, 3)
        transferred_pixels_lab_reshaped = transferred_pixels_lab_uint8.reshape(1, -1, 3)
        transferred_pixels_bgr = cv2.cvtColor(transferred_pixels_lab_reshaped, cv2.COLOR_LAB2BGR)
        
        # Flatten: (N, 3)
        transferred_pixels_bgr = transferred_pixels_bgr.reshape(-1, 3)

        # 8. Reconstruct Image
        recolored_img = warped_rgb.copy()
        recolored_img[mask_indices] = transferred_pixels_bgr

        return recolored_img
