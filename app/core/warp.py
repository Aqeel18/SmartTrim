import cv2
import numpy as np
from typing import Tuple, List, Optional

class HairstyleWarper:
    """
    Handles geometric warping of hairstyle templates to fit the user's head shape.
    Uses Thin Plate Spline (TPS) for smooth non-rigid deformation based on landmarks.
    """

    def __init__(self):
        pass

    def warp_hairstyle(
        self,
        template_rgb: np.ndarray,
        template_alpha: np.ndarray,
        face_landmarks: np.ndarray,
        template_landmarks: Optional[np.ndarray] = None,
        hair_region_polygon: Optional[np.ndarray] = None,
        output_shape: Tuple[int, int] = (512, 512)
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Warps the hairstyle template to align with the face landmarks.

        Args:
            template_rgb: (H, W, 3) Template hairstyle image.
            template_alpha: (H, W) Template alpha mask.
            face_landmarks: (N, 2) Target face landmarks.
            template_landmarks: (N, 2) Optional template face landmarks for better alignment.
            hair_region_polygon: (K, 2) Optional target hair region polygon (not used much in TPS, but kept for interface).
            output_shape: (H, W) Dimensions of the output image.

        Returns:
            warped_rgb: (H, W, 3) Warped hairstyle.
            warped_alpha: (H, W) Warped alpha mask.
        """
        # 1. Define Control Points
        source_points, target_points = self._define_control_points(
            template_alpha, face_landmarks, template_landmarks, hair_region_polygon
        )

        # 2. Apply TPS Warp
        warped_rgb, warped_alpha = self._apply_tps_warp(
            template_rgb, template_alpha, source_points, target_points, output_shape
        )

        return warped_rgb, warped_alpha

    def _define_control_points(
        self,
        template_alpha: np.ndarray,
        face_landmarks: np.ndarray,
        template_landmarks: Optional[np.ndarray],
        hair_region_polygon: Optional[np.ndarray]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Selects corresponding control points on the template and the target face.
        """
        
        # Strategy 1: Landmark-based Alignment (if template landmarks provided)
        if template_landmarks is not None and len(template_landmarks) > 0:
            # Key indices from MediaPipe Face Mesh (468 points)
            # We use a denser set of points to ensure the hairline curves correctly.
            
            # Midline
            # 10: Top Center Forehead
            # 168: Nose Bridge (Anchor)
            # 152: Chin (Anchor)
            
            # Right Side (User's Right, Image Left)
            # 127: Right Temple
            # 54: Right Forehead/Hairline
            # 21: Right Brow Outer
            # 162: Right Sideburn area

            # Left Side (User's Left, Image Right)
            # 356: Left Temple
            # 284: Left Forehead/Hairline
            # 251: Left Brow Outer
            # 389: Left Sideburn area

            # Upper Hairline Curve (Approximate indices)
            # 103, 67, 109 (Left Side Hairline)
            # 338, 297, 332 (Right Side Hairline)
            
            # Full list of control points
            key_indices = [
                10, 168, 152,          # Center Vertical
                127, 234,              # Right Temple/Ear
                356, 454,              # Left Temple/Ear
                54, 68, 103,           # Right Hairline Curve
                284, 298, 332,         # Left Hairline Curve
                21,                    # Right Brow
                251                    # Left Brow
            ]
            
            src_pts = []
            dst_pts = []
            
            # 1. Add key facial landmarks
            for idx in key_indices:
                if idx < len(template_landmarks) and idx < len(face_landmarks):
                    src_pts.append(template_landmarks[idx])
                    dst_pts.append(face_landmarks[idx])
            
            # 2. Add "Top of Hair" Control Point
            # Source: Top of the hair mask
            ys, xs = np.nonzero(template_alpha > 0)
            if len(ys) > 0:
                # Find bounding box of source hair
                tx, ty, tw, th = cv2.boundingRect(template_alpha)
                # Source Top: Top center of the bounding box
                src_top = np.array([tx + tw // 2, ty], dtype=np.float32)
                
                # Target Top: Estimate based on face geometry
                # Vector from Chin(152) to Forehead(10)
                if 152 < len(face_landmarks) and 10 < len(face_landmarks):
                    chin = face_landmarks[152]
                    forehead = face_landmarks[10]
                    
                    face_vec = forehead - chin
                    face_height = np.linalg.norm(face_vec)
                    
                    # Normalize vector
                    if face_height > 0:
                        face_dir = face_vec / face_height
                    else:
                        face_dir = np.array([0, -1]) # Default up
                        
                    # Estimate hair top as roughly 0.6 * face_height above forehead
                    # Adjust this factor based on desired hair volume
                    # Using a slightly higher factor for volume
                    target_top = forehead + face_dir * (face_height * 0.75)
                    
                    # Also add side top points for better volume shape
                    # Perpendicular vector
                    perp_dir = np.array([-face_dir[1], face_dir[0]])
                    
                    # Top Left and Top Right
                    width_factor = 0.6 * face_height
                    
                    src_top_left = np.array([src_top[0] - tw//3, src_top[1] + th//5], dtype=np.float32)
                    src_top_right = np.array([src_top[0] + tw//3, src_top[1] + th//5], dtype=np.float32)
                    
                    target_top_left = target_top - perp_dir * width_factor * 0.8
                    target_top_right = target_top + perp_dir * width_factor * 0.8
                    
                    # Estimate hair top based on width ratio (Scale-based)
                    # This preserves the aspect ratio of the hairstyle.
                    
                    # Source Width (Temple to Temple)
                    src_temple_width = np.linalg.norm(template_landmarks[127] - template_landmarks[356])
                    
                    # Target Width (Temple to Temple)
                    dst_temple_width = np.linalg.norm(face_landmarks[127] - face_landmarks[356])
                    
                    # Scale Factor
                    scale = dst_temple_width / src_temple_width if src_temple_width > 0 else 1.0
                    
                    # Source Hair Height (from Forehead to Top)
                    # We use the source top point and project it relative to the forehead
                    src_vec = src_top - template_landmarks[10] # Vector from Forehead to Top
                    
                    # Target Hair Height Vector
                    # We rotate the source vector to match the face orientation if needed, 
                    # but for now assume vertical alignment or just scale the magnitude along face up direction.
                    
                    # Face Up Direction (Forehead - Chin)
                    if face_height > 0:
                         face_up = (forehead - chin) / face_height
                    else:
                         face_up = np.array([0, -1])
                    
                    # Original height magnitude
                    src_h_mag = np.linalg.norm(src_vec)
                    
                    # Target height magnitude scaled
                    target_h_mag = src_h_mag * scale
                    
                    # Target Top Point
                    target_top = forehead + face_up * target_h_mag
                    
                    # Add side volume points similarly scaled
                    # Source vector for side
                    src_vec_tl = src_top_left - template_landmarks[10]
                    src_vec_tr = src_top_right - template_landmarks[10]
                    
                    # Project to target
                    # We approximate this by scaling the x and y components relative to the face frame
                    # But simpler is to just use the face_up and perp directions
                    
                    # Decompose source vector into (Up, Right) components relative to template face?
                    # Too complex. Let's just scale the offset from the top point.
                    
                    src_offset_tl = src_top_left - src_top
                    src_offset_tr = src_top_right - src_top
                    
                    target_offset_tl = src_offset_tl * scale
                    target_offset_tr = src_offset_tr * scale
                    
                    target_top_left = target_top + target_offset_tl
                    target_top_right = target_top + target_offset_tr

                    src_pts.append(src_top)
                    dst_pts.append(target_top)
                    
                    src_pts.append(src_top_left)
                    dst_pts.append(target_top_left)
                    
                    src_pts.append(src_top_right)
                    dst_pts.append(target_top_right)

            
            # If we have points, return them
            if len(src_pts) >= 5:
                return np.array(src_pts, dtype=np.float32), np.array(dst_pts, dtype=np.float32)
            # Fallback if not enough points
        
        # Strategy 2: Bounding Box Heuristic (Fallback)
        # --- Target Points (Face) ---
        # Assuming 68-point dlib format or MediaPipe mesh.
        # For simplicity/robustness, let's assume we have specific indices or rough regions.
        # If input is MediaPipe Face Mesh (468/478 points), we map specific indices.
        # If input is generic list, we might need heuristics.
        
        # Let's assume input is a standard set of landmarks. 
        # Ideally, this method receives labeled points or we infer them.
        # For this implementation, let's select a few key points based on standard face bounding box logic
        # if specific indices aren't guaranteed.
        
        # However, to be precise, let's extract:
        # 1. Left Temple
        # 2. Right Temple
        # 3. Forehead Center
        
        # Calculate bounding box of face landmarks
        lx, ly, lw, lh = cv2.boundingRect(face_landmarks.astype(np.int32))
        
        # Heuristic Target Points:
        # P1: Left Temple (approx left side of forehead)
        target_p1 = (lx, ly + lh // 4)
        # P2: Right Temple
        target_p2 = (lx + lw, ly + lh // 4)
        # P3: Top Center (Forehead/Hairline) - slightly above the bounding box top
        target_p3 = (lx + lw // 2, ly - lh // 6) 
        
        # P4: Center of face (reference)
        target_p4 = (lx + lw // 2, ly + lh // 2)

        target_points = np.array([target_p1, target_p2, target_p3, target_p4], dtype=np.float32)

        # --- Source Points (Template) ---
        # Find bounding box of the hairstyle in the template
        ys, xs = np.nonzero(template_alpha > 0)
        if len(ys) == 0:
             # Fallback if empty mask
             h, w = template_alpha.shape
             tx, ty, tw, th = 0, 0, w, h
        else:
            ty, tx = np.min(ys), np.min(xs)
            th, tw = np.max(ys) - ty, np.max(xs) - tx

        # Map corresponding points on the template relative to its bbox
        # These ratios must align with the heuristic target points
        
        # Source P1: Left Temple (Left side, ~middle-top)
        source_p1 = (tx, ty + th // 2) 
        # Source P2: Right Temple (Right side, ~middle-top)
        source_p2 = (tx + tw, ty + th // 2)
        # Source P3: Top Center (Top of hair)
        source_p3 = (tx + tw // 2, ty)
        # Source P4: Center of mass/gravity (approx)
        source_p4 = (tx + tw // 2, ty + th // 2)

        # Refinement: The "Temple" on a wig is usually the sideburns area.
        # The "Top Center" is the top edge.
        # Let's adjust to match standard wig alignment.
        # P1 (Left Sideburn): Left-bottomish of the top half
        source_p1 = (tx + tw * 0.1, ty + th * 0.6)
        # P2 (Right Sideburn): Right-bottomish of the top half
        source_p2 = (tx + tw * 0.9, ty + th * 0.6)
        # P3 (Forehead Center): Middle, somewhat down from top
        source_p3 = (tx + tw * 0.5, ty + th * 0.3)
        # P4 (Top of Head): Top center
        source_p4 = (tx + tw * 0.5, ty)

        # Corresponding Target Points need to match these semantic locations
        # Target P1 (Left Sideburn area):
        target_p1 = (lx, ly + lh // 3)
        # Target P2 (Right Sideburn area):
        target_p2 = (lx + lw, ly + lh // 3)
        # Target P3 (Forehead Center):
        target_p3 = (lx + lw // 2, ly) # Top of detected face bbox is usually brow/forehead
        # Target P4 (Top of Head):
        # Estimate top of head based on face height (usually 1/3 to 1/2 face height above brow)
        target_p4 = (lx + lw // 2, ly - int(lh * 0.4))

        source_points = np.array([source_p1, source_p2, source_p3, source_p4], dtype=np.float32)
        target_points = np.array([target_p1, target_p2, target_p3, target_p4], dtype=np.float32)

        return source_points, target_points

    def _apply_tps_warp(
        self,
        img: np.ndarray,
        mask: np.ndarray,
        src_points: np.ndarray,
        dst_points: np.ndarray,
        output_shape: Tuple[int, int]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Applies Thin Plate Spline (TPS) warping via a dense NumPy remap.

        We solve TPS in the inverse direction (DST → SRC) so that every output
        pixel can look up its source coordinate in the input image, which is
        what cv2.remap requires.

        Using pure NumPy for the TPS solve avoids the awkward Python bindings of
        cv2.createThinPlateSplineShapeTransformer (which is designed for shape
        matching, not dense image warping).
        """
        h, w = output_shape

        map_x, map_y = self._numpy_tps_map(dst_points, src_points, h, w)

        # INTER_CUBIC gives a good sharpness / speed trade-off.
        warped_img  = cv2.remap(img,  map_x, map_y, cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_CONSTANT)
        warped_mask = cv2.remap(mask, map_x, map_y, cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_CONSTANT)

        return warped_img, warped_mask

    def _numpy_tps_map(self, dst_pts, src_pts, h, w):
        """
        Compute TPS mapping from dst_pts to src_pts.
        Returns map_x, map_y for cv2.remap.
        """
        # Number of control points
        N = dst_pts.shape[0]
        
        # 1. Construct L matrix
        # K = U(||P_i - P_j||)
        # L = [K  P]
        #     [P^T 0]
        
        # Pairwise distances between destination points (control points)
        # dst_pts: (N, 2)
        diff = dst_pts[:, None, :] - dst_pts[None, :, :] # (N, N, 2)
        sq_dists = np.sum(diff**2, axis=2) # (N, N)
        r = np.sqrt(sq_dists)
        
        # U(r) = r^2 * log(r^2)
        # Handle r=0 to avoid log(0)
        K = np.zeros_like(r)
        mask = r > 1e-6
        K[mask] = r[mask]**2 * np.log(r[mask]**2)
        
        # P matrix: (N, 3) -> [1, x, y]
        P = np.hstack((np.ones((N, 1)), dst_pts))
        
        # L matrix: (N+3, N+3)
        L = np.zeros((N + 3, N + 3))
        L[:N, :N] = K
        L[:N, N:] = P
        L[N:, :N] = P.T
        
        # 2. Solve for weights W and affine coefficients A
        # Target values V are the source coordinates (x, y) we want to map to
        # We augment V with zeros for the affine constraints
        # V: (N+3, 2)
        V = np.zeros((N + 3, 2))
        V[:N, :] = src_pts
        
        # Solve L * [W; A] = V
        # Add regularization to diagonal of K to improve stability
        L[:N, :N] += np.eye(N) * 1e-6
        
        try:
            coeffs = np.linalg.solve(L, V)
        except np.linalg.LinAlgError:
            # Fallback to least squares if singular
            coeffs = np.linalg.lstsq(L, V, rcond=None)[0]
            
        weights = coeffs[:N, :] # (N, 2)
        affine = coeffs[N:, :]  # (3, 2)
        
        # 3. Generate dense map
        # Grid points (destination pixels)
        # We need to compute f(x,y) for every pixel
        
        # To make this fast in NumPy, we broadcast
        # Memory warning: Creating full (H*W, N) matrices can be heavy for large images.
        # 512*512 = 262k pixels. 262k * 4 points * 8 bytes ~ 8MB. Totally fine.
        
        grid_y, grid_x = np.mgrid[0:h, 0:w]
        grid_pts = np.vstack((grid_x.ravel(), grid_y.ravel())).T # (H*W, 2)
        
        # Compute distances from every grid point to every control point
        # grid_pts: (M, 2), dst_pts: (N, 2)
        # dists: (M, N)
        # Optimization: process in chunks if needed, but 512x512 is small enough.
        
        # Calculate U(r) for grid
        # dist_sq = (x-xi)^2 + (y-yi)^2
        # Let's use simpler expansion: sum((A-B)^2) = sum(A^2) + sum(B^2) - 2AB
        
        # This part can be slow in pure python/numpy loop. Vectorized:
        diff_grid = grid_pts[:, None, :] - dst_pts[None, :, :] # (M, N, 2)
        sq_dists_grid = np.sum(diff_grid**2, axis=2) # (M, N)
        r_grid = np.sqrt(sq_dists_grid)
        
        U_grid = np.zeros_like(r_grid)
        mask_g = r_grid > 1e-6
        U_grid[mask_g] = r_grid[mask_g]**2 * np.log(r_grid[mask_g]**2)
        
        # f(p) = affine + sum(weights * U)
        # affine part: [1, x, y] @ affine
        P_grid = np.hstack((np.ones((grid_pts.shape[0], 1)), grid_pts))
        affine_part = P_grid @ affine # (M, 2)
        
        non_rigid_part = U_grid @ weights # (M, 2)
        
        transformed_pts = affine_part + non_rigid_part
        
        map_x = transformed_pts[:, 0].reshape(h, w).astype(np.float32)
        map_y = transformed_pts[:, 1].reshape(h, w).astype(np.float32)
        
        return map_x, map_y





