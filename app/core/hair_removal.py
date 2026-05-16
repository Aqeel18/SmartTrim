import cv2
import numpy as np

class HairRemover:
    """
    Classical computer vision-based hair removal module.
    Uses inpainting to remove hair pixels identified by a segmentation mask,
    replacing them with plausible skin/background textures from the surrounding area.
    """

    def __init__(self, inpaint_radius: int = 9):
        """
        Initialize the HairRemover.

        Args:
            inpaint_radius (int): Radius of a circular neighborhood of each point inpainted
                                  that is considered by the algorithm. Default is 9.
        """
        self.inpaint_radius = inpaint_radius

    def remove_hair(self, face_image: np.ndarray, hair_mask: np.ndarray) -> np.ndarray:
        """
        Remove hair from the face image using the provided hair mask.

        Args:
            face_image (np.ndarray): Original face image (BGR).
            hair_mask (np.ndarray): Binary hair mask (255=hair, 0=non-hair).

        Returns:
            np.ndarray: The image with hair removed (inpainted).
        
        Raises:
            ValueError: If input dimensions do not match or inputs are invalid.
        """
        # 1. Validate inputs
        if face_image is None or hair_mask is None:
            raise ValueError("Input image and mask cannot be None.")
        
        if face_image.shape[:2] != hair_mask.shape[:2]:
            raise ValueError(f"Image shape {face_image.shape[:2]} and mask shape {hair_mask.shape[:2]} must match.")

        # Check if mask contains any hair pixels
        if np.sum(hair_mask) == 0:
            # No hair detected, return original image
            return face_image.copy()

        # 2. Prepare mask for inpainting
        # Ensure mask is single channel and uint8
        if len(hair_mask.shape) == 3:
            inpaint_mask = cv2.cvtColor(hair_mask, cv2.COLOR_BGR2GRAY)
        else:
            inpaint_mask = hair_mask.copy()
            
        # Ensure binary mask (strict 0 or 255)
        _, inpaint_mask = cv2.threshold(inpaint_mask, 127, 255, cv2.THRESH_BINARY)

        # --- ROOT PRESERVATION STRATEGY ---
        # Step 1: Erode the hair mask to preserve a thin band of roots
        # This shrinks the removal region inward so that 5-10 pixels of original hair remain.
        kernel_size = (9, 9)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, kernel_size)
        eroded_mask = cv2.erode(inpaint_mask, kernel, iterations=1)

        # 3. Apply Inpainting
        # We use cv2.INPAINT_TELEA (based on Fast Marching Method).
        # It propagates image information from the boundary inwards.
        # This is suitable for filling in the hair region with neighboring skin/background texture.
        # Limitations:
        # - Can produce blurriness in large hair regions.
        # - Does not hallucinate new features (e.g., ears covered by hair).
        # - Only uses local context.
        #
        # Step 2: Use ONLY the eroded mask for inpainting
        # The region (inpaint_mask - eroded_mask) remains untouched, preserving natural root texture.
        hair_removed_image = cv2.inpaint(
            src=face_image,
            inpaintMask=eroded_mask,
            inpaintRadius=7,
            flags=cv2.INPAINT_TELEA
        )
        
        # --- SEAM BLENDING ---
        # The transition between the preserved roots (original pixels) and the inpainted area
        # can be abrupt. We blur this specific boundary to reduce "hair removal marks".
        
        # 1. Identify the seam: The area just outside the eroded mask (the preserved root edge)
        # and just inside the eroded mask (the start of inpainting).
        # We dilate the eroded mask to cover the transition zone.
        blend_kernel_size = 21
        blend_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (blend_kernel_size, blend_kernel_size))
        
        # This band covers the boundary
        dilated_eroded = cv2.dilate(eroded_mask, blend_kernel, iterations=1)
        seam_mask = cv2.subtract(dilated_eroded, cv2.erode(eroded_mask, blend_kernel, iterations=1))
        
        if cv2.countNonZero(seam_mask) > 0:
            # 2. Create a blurred version of the result
            blurred_image = cv2.GaussianBlur(hair_removed_image, (21, 21), 0)
            
            # 3. Create a soft alpha mask for blending
            mask_float = seam_mask.astype(np.float32) / 255.0
            # Blur the mask to make the blending soft
            mask_soft = cv2.GaussianBlur(mask_float, (21, 21), 0)
            mask_soft = np.clip(mask_soft, 0, 1)
            mask_soft = np.repeat(mask_soft[:, :, np.newaxis], 3, axis=2)
            
            # 4. Blend: Result = Original * (1 - mask) + Blurred * mask
            # This blurs only the seam area
            hair_removed_image = (hair_removed_image.astype(np.float32) * (1 - mask_soft) + 
                                  blurred_image.astype(np.float32) * mask_soft).astype(np.uint8)

        return hair_removed_image