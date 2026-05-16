import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os

class FaceAnalyzer:
    """
    Handles face detection and landmark extraction using MediaPipe Face Landmarker (New Tasks API).
    Designed for academic MVP: simple, readable, and efficient.
    """
    def __init__(self, model_path=None):
        if model_path is None:
             # Assume model is in ../models/face_landmarker.task relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, '..', 'models', 'face_landmarker.task')
            model_path = os.path.normpath(model_path)
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Face Landmarker model not found at: {model_path}")

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=1)
        self.detector = vision.FaceLandmarker.create_from_options(options)

    def detect_landmarks(self, image_bgr):
        """
        Detects facial landmarks from an input image (BGR numpy array).
        
        Args:
            image_bgr (numpy.ndarray): Input image in BGR format (OpenCV standard).
            
        Returns:
            dict: A dictionary containing:
                - 'landmarks_pixel': List of (x, y) tuples in pixel coordinates.
                - 'landmarks_normalized': List of (x, y, z) tuples in normalized coordinates [0, 1].
                - 'face_detected': Boolean indicating if a face was found.
        """
        if image_bgr is None:
            return {'face_detected': False}

        height, width, _ = image_bgr.shape
        
        # Convert BGR to RGB as MediaPipe expects RGB
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        
        # Create MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        # Detect landmarks
        # The detect method returns a FaceLandmarkerResult object
        detection_result = self.detector.detect(mp_image)
        
        if not detection_result.face_landmarks:
            return {'face_detected': False}
        
        # We assume only one face (num_faces=1)
        face_landmarks = detection_result.face_landmarks[0]
        
        landmarks_pixel = []
        landmarks_normalized = []
        
        for landmark in face_landmarks:
            # Normalized coordinates (0.0 to 1.0)
            landmarks_normalized.append((landmark.x, landmark.y, landmark.z))
            
            # Convert to pixel coordinates
            x_px = int(landmark.x * width)
            y_px = int(landmark.y * height)
            landmarks_pixel.append((x_px, y_px))
            
        return {
            'face_detected': True,
            'landmarks_pixel': landmarks_pixel,      # Useful for drawing/overlaying on the image
            'landmarks_normalized': landmarks_normalized # Useful for geometric calculations independent of resolution
        }

# Global instance for easy import and reuse
try:
    face_analyzer = FaceAnalyzer()
except FileNotFoundError as e:
    print(f"Warning: {e}. Face detection will fail until model is downloaded.")
    face_analyzer = None

def detect_face_landmarks(image_path_or_array):
    """
    Wrapper function to detect landmarks from a file path or numpy array.
    Used by API routes.
    """
    if face_analyzer is None:
        return {'face_detected': False, 'error': 'Model not loaded'}

    if isinstance(image_path_or_array, str):
        image = cv2.imread(image_path_or_array)
    else:
        image = image_path_or_array
        
    return face_analyzer.detect_landmarks(image)
