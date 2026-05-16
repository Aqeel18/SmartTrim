import cv2
import numpy as np
from typing import Dict, Tuple

class HairColorExtractor:
    """
    Extracts dominant hair color and statistics from an image using a segmentation mask.
    Operates in LAB color space for better perceptual accuracy and color transfer suitability.
    """

    def extract_color_stats(self, image_bgr: np.ndarray, hair_mask: np.ndarray) -> Dict[str, Tuple[float, float, float]]:
        """
        Extracts color statistics (median and std dev) from hair pixels.

        Args:
            image_bgr (np.ndarray): Original BGR image.
            hair_mask (np.ndarray): Binary mask (255=hair, 0=background).

        Returns:
            dict: Dictionary containing:
                - 'lab_median': (L, A, B) median values
                - 'lab_std': (L_std, A_std, B_std) standard deviation values
                - 'pixel_count': Number of pixels used for calculation
        
        Raises:
            ValueError: If inputs are invalid or dimensions mismatch.
        """
        # 1. Validate inputs
        if image_bgr is None or hair_mask is None:
            raise ValueError("Input image and mask cannot be None.")
        
        if image_bgr.shape[:2] != hair_mask.shape[:2]:
            raise ValueError(f"Image shape {image_bgr.shape[:2]} and mask shape {hair_mask.shape[:2]} must match.")

        # Ensure mask is single channel and binary
        if len(hair_mask.shape) == 3:
            mask_gray = cv2.cvtColor(hair_mask, cv2.COLOR_BGR2GRAY)
        else:
            mask_gray = hair_mask
            
        # 2. Extract Hair Pixels
        # Get coordinates of hair pixels
        hair_indices = np.where(mask_gray >= 127)
        
        if len(hair_indices[0]) == 0:
            # No hair detected, return default neutral values
            return {
                'lab_median': (0.0, 0.0, 0.0),
                'lab_std': (0.0, 0.0, 0.0),
                'pixel_count': 0
            }

        # Extract BGR values of hair pixels
        hair_pixels_bgr = image_bgr[hair_indices]

        # 3. Convert to LAB Color Space
        # Reshape to (N, 1, 3) because cv2.cvtColor expects an image-like shape
        # Or simply convert the whole image first and then index (usually faster for Python loops, but slower for memory)
        # Here we convert only the extracted pixels to save computation if N is small, 
        # but cv2.cvtColor requires (height, width, channels).
        # So it's easier to reshape to (1, N, 3).
        hair_pixels_bgr_reshaped = hair_pixels_bgr.reshape(1, -1, 3)
        hair_pixels_lab = cv2.cvtColor(hair_pixels_bgr_reshaped, cv2.COLOR_BGR2LAB)
        
        # Flatten back to (N, 3)
        hair_pixels_lab = hair_pixels_lab.reshape(-1, 3)

        # 4. Compute Statistics
        # We use median for robustness against outliers (e.g., highlights, shadows, segmentation errors)
        # We use float64 for precision during calculation
        l_vals = hair_pixels_lab[:, 0].astype(np.float64)
        a_vals = hair_pixels_lab[:, 1].astype(np.float64)
        b_vals = hair_pixels_lab[:, 2].astype(np.float64)

        lab_median = (
            float(np.median(l_vals)),
            float(np.median(a_vals)),
            float(np.median(b_vals))
        )

        # Standard deviation is useful for color transfer (reinhard method)
        lab_std = (
            float(np.std(l_vals)),
            float(np.std(a_vals)),
            float(np.std(b_vals))
        )

        return {
            'lab_median': lab_median,
            'lab_std': lab_std,
            'pixel_count': len(l_vals)
        }
