import numpy as np
import cv2
import torch
import torch.nn.functional as F
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import os
from typing import Dict, Optional, Tuple

class FaceShapeClassifier:
    """
    ML-based face shape classifier using ResNet18, with a geometry-based fallback
    using MediaPipe FaceMesh landmarks if the model isn't trained yet.
    """
    
    IDX_TEMPLE_LEFT = 356
    IDX_TEMPLE_RIGHT = 127
    IDX_FOREHEAD_TOP = 10
    IDX_CHEEKBONE_LEFT = 234
    IDX_CHEEKBONE_RIGHT = 454
    IDX_JAW_LEFT = 172
    IDX_JAW_RIGHT = 397
    IDX_CHIN = 152

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = "app/models/face_shape_model.pth"
        self.ml_model = None
        self.class_names = ['Heart', 'Oblong', 'Oval', 'Round', 'Square']
        
        # Transforms for ML model
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                model = models.resnet18(weights=None)
                num_ftrs = model.fc.in_features
                model.fc = torch.nn.Linear(num_ftrs, len(self.class_names))
                model.load_state_dict(torch.load(self.model_path, map_location=self.device))
                model.to(self.device)
                model.eval()
                self.ml_model = model
                print("Face Shape ML Model loaded successfully.")
            except Exception as e:
                print(f"Failed to load Face Shape ML Model: {e}")
        else:
            print("Face Shape ML Model not found. Using Geometric Fallback.")

    def _dist(self, p1, p2):
        p1 = np.array(p1, dtype=np.float32)
        p2 = np.array(p2, dtype=np.float32)
        return float(np.linalg.norm(p1 - p2))

    def _angle(self, a, b, c):
        a = np.array(a, dtype=np.float32)
        b = np.array(b, dtype=np.float32)
        c = np.array(c, dtype=np.float32)
        ba = a - b
        bc = c - b
        denom = (np.linalg.norm(ba) * np.linalg.norm(bc))
        if denom == 0:
            return 0.0
        cos_angle = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
        angle = np.degrees(np.arccos(cos_angle))
        return float(angle)

    def compute_metrics(self, landmarks_pixel):
        if landmarks_pixel is None or len(landmarks_pixel) < 468:
            raise ValueError("Insufficient landmarks for face shape analysis.")

        tl = landmarks_pixel[self.IDX_TEMPLE_LEFT]
        tr = landmarks_pixel[self.IDX_TEMPLE_RIGHT]
        cbl = landmarks_pixel[self.IDX_CHEEKBONE_LEFT]
        cbr = landmarks_pixel[self.IDX_CHEEKBONE_RIGHT]
        jl = landmarks_pixel[self.IDX_JAW_LEFT]
        jr = landmarks_pixel[self.IDX_JAW_RIGHT]
        chin = landmarks_pixel[self.IDX_CHIN]
        forehead_top = landmarks_pixel[self.IDX_FOREHEAD_TOP]

        forehead_width = self._dist(tl, tr)
        cheekbone_width = self._dist(cbl, cbr)
        jaw_width = self._dist(jl, jr)
        face_length = self._dist(chin, forehead_top)
        chin_angle = self._angle(jl, chin, jr)

        norm = cheekbone_width if cheekbone_width > 1e-6 else 1.0

        return {
            'face_length': float(face_length / norm),
            'forehead_width': float(forehead_width / norm),
            'cheekbone_width': float(cheekbone_width / norm if norm != 0 else 0.0),
            'jaw_width': float(jaw_width / norm),
            'chin_angle': float(chin_angle)
        }

    def classify_geometric(self, metrics: dict) -> Tuple[str, float]:
        """
        Rule-based geometric classifier with a confidence score.

        Confidence is estimated by how decisively the face satisfies one shape's
        primary criterion versus the others. Returns (shape_label, confidence 0-1).
        """
        fl = metrics['face_length']        # normalized by cheekbone width
        fw = metrics['forehead_width']
        jw = metrics['jaw_width']
        ca = metrics['chin_angle']

        # Each candidate is scored by how strongly it satisfies its criteria.
        # Margin > 0 means the criterion is met; larger margin = higher confidence.
        candidates = {
            'Oblong':  fl - 1.25,                                 # longer face
            'Square':  min(jw - 0.88, (ca - 115) / 30),          # wide jaw + obtuse angle
            'Heart':   min(fw - 1.02, (105 - ca) / 30),          # wide forehead + acute chin
            'Diamond': min(0.75 - jw, (100 - ca) / 30),          # narrow jaw + acute chin
            'Round':   1.12 - fl,                                  # short face
            'Oval':    0.05,                                       # weakest default
        }

        # Pick the highest-scoring candidate
        best_shape = max(candidates, key=lambda k: candidates[k])
        best_score = candidates[best_shape]

        # Compute second-best to measure separation
        sorted_scores = sorted(candidates.values(), reverse=True)
        margin = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else best_score

        # Map margin to a [0.5, 0.95] confidence range
        confidence = float(np.clip(0.55 + margin * 2.0, 0.50, 0.95))

        return best_shape, confidence

    def classify_ml(self, face_bgr: np.ndarray) -> Optional[Tuple[str, float, Dict[str, float]]]:
        """
        ML-based classifier. Returns (label, confidence, per_class_scores) or None.
        """
        if self.ml_model is None or face_bgr is None:
            return None
            
        try:
            face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(face_rgb)
            img_t = self.transform(img).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                logits = self.ml_model(img_t)                    # (1, num_classes)
                probs  = F.softmax(logits, dim=1)[0]             # (num_classes,)
                pred_idx = int(torch.argmax(probs).item())
                label    = self.class_names[pred_idx]
                confidence = float(probs[pred_idx].item())
                scores = {
                    name: round(float(probs[i].item()), 4)
                    for i, name in enumerate(self.class_names)
                }
            return label, confidence, scores
        except Exception as e:
            print(f"ML classification failed: {e}")
            return None

    def analyze(self, landmarks_pixel, face_bgr=None) -> dict:
        """
        Run face shape classification, preferring the ML model when available.

        Returns a dict with:
          - face_shape (str)
          - confidence (float, 0-1)
          - scores (dict mapping each shape to its probability/score)
          - method ('ml' or 'geometric')
          - metrics (raw geometric measurements)
        """
        metrics = self.compute_metrics(landmarks_pixel)

        # --- Try ML first ---
        ml_result = None
        if self.ml_model is not None and face_bgr is not None:
            ml_result = self.classify_ml(face_bgr)

        if ml_result is not None:
            face_shape, confidence, scores = ml_result
            method = 'ml'
        else:
            # --- Geometric fallback ---
            face_shape, confidence = self.classify_geometric(metrics)
            # Build a pseudo-scores dict so the API response is consistent
            scores = {s: round(confidence if s == face_shape else (1 - confidence) / (len(self.class_names) - 1), 4)
                      for s in self.class_names}
            method = 'geometric'

        return {
            'face_shape':  face_shape,
            'confidence':  round(confidence, 4),
            'scores':      scores,
            'method':      method,
            'metrics':     metrics,
        }
