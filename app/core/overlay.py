"""
Deterministic hairstyle overlay and alpha blending engine for SmartTrim_360.
"""

import cv2
import numpy as np
from typing import Optional, Tuple

class FinalOverlayEngine:
    """
    Composites the prepared hairstyle onto the hair-removed face image.
    Uses clean alpha blending with soft edge feathering for a natural result.
    """

    def overlay(
        self,
        original_face: np.ndarray,
        hair_removed_img: np.ndarray,
        warped_hair_rgb: np.ndarray,
        warped_alpha: np.ndarray,
        hair_region_mask: np.ndarray
    ) -> np.ndarray:
        """
        Perform final alpha blending.

        Args:
            original_face: Original input image (H, W, 3).
            hair_removed_img: Image with hair removed (H, W, 3).
            warped_hair_rgb: Warped hairstyle image (H, W, 3).
            warped_alpha: Alpha mask of the warped hairstyle (H, W).
            hair_region_mask: BiSeNet hair segmentation mask (H, W).

        Returns:
            np.ndarray: Final composited image (H, W, 3).
        """
        if hair_removed_img is None:
            raise ValueError("hair_removed_img cannot be None")

        h, w = hair_removed_img.shape[:2]

        # Resize all inputs to match the target dimensions
        if warped_hair_rgb.shape[:2] != (h, w):
            warped_hair_rgb = cv2.resize(warped_hair_rgb, (w, h))
        if warped_alpha.shape[:2] != (h, w):
            warped_alpha = cv2.resize(warped_alpha, (w, h))
        if hair_region_mask is not None and hair_region_mask.shape[:2] != (h, w):
            hair_region_mask = cv2.resize(hair_region_mask, (w, h))

        # --- Build the compositing alpha ---
        # Use the warped template's own alpha as the primary mask.
        # This is the most reliable signal for where the new hair should appear.
        alpha_f = warped_alpha.astype(np.float32) / 255.0

        # Feather the edges with a small Gaussian blur to avoid hard edges
        alpha_feathered = cv2.GaussianBlur(alpha_f, (15, 15), 0)

        # Clamp
        alpha_feathered = np.clip(alpha_feathered, 0.0, 1.0)

        # Expand to 3 channels
        alpha_3c = np.stack([alpha_feathered] * 3, axis=2)

        # --- Composite ---
        # New hair on top of the hair-removed base (clean plate)
        hair_float = warped_hair_rgb.astype(np.float32)
        base_float = hair_removed_img.astype(np.float32)

        final = hair_float * alpha_3c + base_float * (1.0 - alpha_3c)
        final = np.clip(final, 0, 255).astype(np.uint8)

        return final
