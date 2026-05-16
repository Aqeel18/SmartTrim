import cv2
import numpy as np

class HairRegionEstimator:
    """
    Estimates the hair/scalp region based on facial landmarks using geometric reasoning.
    
    This is a heuristic-based approach for the SmartTrim_360 MVP. 
    It does NOT use machine learning for hair segmentation.
    Instead, it extrapolates a 'hair dome' above the forehead landmarks.
    """
    
    def __init__(self, hair_height_ratio=0.5, hair_width_expansion=0.1):
        """
        Args:
            hair_height_ratio (float): Ratio of face height to use for hair height estimation.
                                       0.5 means hair height is roughly half the face height.
            hair_width_expansion (float): Percentage to expand the width beyond the temples.
        """
        self.hair_height_ratio = hair_height_ratio
        self.hair_width_expansion = hair_width_expansion
        
        # MediaPipe Face Mesh Indices (0-based)
        # 10: Top of forehead
        # 152: Chin
        # 234: Right cheek/ear (from viewer perspective: left side of image if selfie, right if mirrored)
        # 454: Left cheek/ear
        # 127: Right temple area
        # 356: Left temple area
        self.INDEX_FOREHEAD_TOP = 10
        self.INDEX_CHIN = 152
        self.INDEX_RIGHT_TEMPLE = 127 # Outer eye/temple region
        self.INDEX_LEFT_TEMPLE = 356  # Outer eye/temple region
        
        # Upper face boundary indices (Right to Left) for creating the bottom of the hair mask
        # These trace the hairline from right temple to left temple
        self.HAIRLINE_INDICES = [
            127, 162, 21, 54, 103, 67, 109, 10, 
            338, 297, 332, 284, 251, 389, 356
        ]

    def estimate_hair_region(self, landmarks_pixel, image_shape):
        """
        Generates a polygon and binary mask for the estimated hair region.
        
        Args:
            landmarks_pixel (list of tuple): List of (x, y) coordinates from FaceAnalyzer.
            image_shape (tuple): (height, width) or (height, width, channels) of the image.
            
        Returns:
            dict: {
                'polygon': np.array (N, 2) of points defining the hair region.
                'mask': np.array (height, width) binary mask (0 or 255).
                'success': bool
            }
        """
        height = image_shape[0]
        width = image_shape[1]
        
        # Basic validation
        if landmarks_pixel is None or len(landmarks_pixel) < 468:
            return {'success': False, 'error': 'Insufficient landmarks'}

        try:
            # 1. Calculate Face Geometry
            chin_pt = np.array(landmarks_pixel[self.INDEX_CHIN])
            forehead_pt = np.array(landmarks_pixel[self.INDEX_FOREHEAD_TOP])
            left_temple_pt = np.array(landmarks_pixel[self.INDEX_LEFT_TEMPLE])
            right_temple_pt = np.array(landmarks_pixel[self.INDEX_RIGHT_TEMPLE])
            
            # Face height (Euclidean distance between chin and forehead)
            face_height = np.linalg.norm(chin_pt - forehead_pt)
            
            # Face width (Horizontal distance between temples)
            face_width = np.linalg.norm(left_temple_pt - right_temple_pt)
            
            # 2. Estimate Hair Boundary Points
            # We construct a "dome" above the forehead.
            
            # Estimated Hair Top (Center)
            # Go up from the forehead point by (face_height * ratio)
            # Note: y-axis is inverted in images (0 is top), so we subtract
            estimated_hair_height = face_height * self.hair_height_ratio
            hair_top_y = forehead_pt[1] - estimated_hair_height
            hair_top_pt = np.array([forehead_pt[0], hair_top_y])
            
            # Expand width slightly for the sides of the hair
            expansion_pixels = face_width * self.hair_width_expansion
            
            # Top Left (extrapolated above left temple)
            # Move left and up
            hair_top_left = np.array([
                left_temple_pt[0] + expansion_pixels, # Assuming left temple is at higher x
                left_temple_pt[1] - (estimated_hair_height * 0.8)
            ])
            
            # Top Right (extrapolated above right temple)
            # Move right and up
            hair_top_right = np.array([
                right_temple_pt[0] - expansion_pixels, # Assuming right temple is at lower x
                right_temple_pt[1] - (estimated_hair_height * 0.8)
            ])
            
            # 3. Construct Polygon
            # Start from Right Temple -> Go along hairline to Left Temple -> Go up to Top Left -> Top Center -> Top Right -> Close
            
            polygon_points = []
            
            # A. Add hairline points (Right to Left)
            for idx in self.HAIRLINE_INDICES:
                polygon_points.append(landmarks_pixel[idx])
                
            # B. Add Upper Dome points (Left to Right)
            # We interpolate a curve for better visuals, but for MVP simple points suffice.
            # Order: Left Temple (last added) -> Top Left -> Top Center -> Top Right -> Right Temple (start)
            
            # Note: Determine left/right based on X coordinates to ensure correct winding order
            # Usually index 356 is left side of face (higher X in standard image) and 127 is right side (lower X)
            # If the user is facing the camera directly.
            
            polygon_points.append(hair_top_left)
            polygon_points.append(hair_top_pt)
            polygon_points.append(hair_top_right)
            
            # Convert to numpy array of type int32 for OpenCV
            polygon_np = np.array(polygon_points, dtype=np.int32)
            
            # 4. Create Mask
            mask = np.zeros((height, width), dtype=np.uint8)
            cv2.fillPoly(mask, [polygon_np], 255)
            
            return {
                'success': True,
                'polygon': polygon_np,
                'mask': mask
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Global instance
hair_estimator = HairRegionEstimator()

def estimate_hair(landmarks, image_shape):
    """
    Wrapper function to estimate hair region.
    """
    return hair_estimator.estimate_hair_region(landmarks, image_shape)

