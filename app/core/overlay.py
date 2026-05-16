"""
Deterministic hairstyle overlay and alpha blending engine for SmartTrim_360.
"""

import cv2
import numpy as np
from typing import Optional


class FinalOverlayEngine:
    """
    Composites the prepared hairstyle onto the hair-removed face image.

    Pipeline (in priority order):
      1. Poisson Seamless Clone  — eliminates colour seams at the hair boundary
         using gradient-domain blending (cv2.seamlessClone).
      2. Alpha-blend fallback    — used when the Poisson mask is too small or
         seamlessClone raises an error (e.g. degenerate mask).
    """

    _MIN_POISSON_PIXELS = 400   # minimum non-zero mask pixels to attempt Poisson

    def overlay(
        self,
        original_face: np.ndarray,
        hair_removed_img: np.ndarray,
        warped_hair_rgb: np.ndarray,
        warped_alpha: np.ndarray,
        hair_region_mask: np.ndarray
    ) -> np.ndarray:
        """
        Composite the new hairstyle onto the face.

        Args:
            original_face:    Original input image (H, W, 3) — kept for reference.
            hair_removed_img: Image with hair removed (H, W, 3).
            warped_hair_rgb:  Warped hairstyle image (H, W, 3).
            warped_alpha:     Alpha mask of the warped hairstyle (H, W).
            hair_region_mask: BiSeNet hair segmentation mask (H, W).

        Returns:
            np.ndarray: Final composited image (H, W, 3).
        """
        if hair_removed_img is None:
            raise ValueError("hair_removed_img cannot be None")

        h, w = hair_removed_img.shape[:2]

        # --- Resize all inputs to match the target canvas ---
        def _resize(arr, interp=cv2.INTER_LINEAR):
            return cv2.resize(arr, (w, h), interpolation=interp) if arr.shape[:2] != (h, w) else arr

        warped_hair_rgb  = _resize(warped_hair_rgb)
        warped_alpha     = _resize(warped_alpha, cv2.INTER_NEAREST)
        if hair_region_mask is not None:
            hair_region_mask = _resize(hair_region_mask, cv2.INTER_NEAREST)

        # Build binary mask: union of warp alpha + BiSeNet region
        _, binary_mask = cv2.threshold(warped_alpha, 10, 255, cv2.THRESH_BINARY)
        if hair_region_mask is not None:
            binary_mask = cv2.bitwise_or(binary_mask, hair_region_mask)

        # 1. Try Poisson blending first
        result = self._poisson_blend(hair_removed_img, warped_hair_rgb, binary_mask)
        if result is not None:
            return result

        # 2. Fallback: feathered alpha blend
        return self._alpha_blend(hair_removed_img, warped_hair_rgb, warped_alpha)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _poisson_blend(
        self,
        base: np.ndarray,
        src: np.ndarray,
        mask: np.ndarray,
    ) -> Optional[np.ndarray]:
        """
        Attempt Poisson seamless cloning (gradient-domain blending).

        cv2.seamlessClone places *src* pixels (where mask=255) onto *base*,
        solving the Poisson equation so colour and lighting transitions are
        smooth and invisible — far superior to a plain alpha blend.

        Returns the blended image, or None if the attempt fails.
        """
        if int(np.count_nonzero(mask)) < self._MIN_POISSON_PIXELS:
            return None

        try:
            # seamlessClone expects a uint8 3-channel mask
            if mask.ndim == 2:
                mask_3c = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            else:
                mask_3c = mask

            # Centre of the bounding rect of the masked region
            ys, xs = np.nonzero(mask)
            cx = int((int(xs.min()) + int(xs.max())) // 2)
            cy = int((int(ys.min()) + int(ys.max())) // 2)

            blended = cv2.seamlessClone(
                src=src,
                dst=base,
                mask=mask_3c,
                p=(cx, cy),
                flags=cv2.NORMAL_CLONE,
            )
            return blended
        except cv2.error:
            return None

    def _alpha_blend(
        self,
        base: np.ndarray,
        src: np.ndarray,
        alpha: np.ndarray,
    ) -> np.ndarray:
        """
        Classic feathered alpha blend — used as a fallback when Poisson fails.
        """
        alpha_f = alpha.astype(np.float32) / 255.0
        alpha_feathered = cv2.GaussianBlur(alpha_f, (15, 15), 0)
        alpha_feathered = np.clip(alpha_feathered, 0.0, 1.0)
        alpha_3c = np.stack([alpha_feathered] * 3, axis=2)

        final = src.astype(np.float32) * alpha_3c + base.astype(np.float32) * (1.0 - alpha_3c)
        return np.clip(final, 0, 255).astype(np.uint8)
