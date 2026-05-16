import os
import sys
import cv2
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.face_analysis import FaceAnalyzer
from app.core.face_shape_classifier import FaceShapeClassifier


def draw_line(img, p1, p2, color, thickness=2):
    cv2.line(img, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), color, thickness)


def draw_point(img, p, color, r=3):
    cv2.circle(img, (int(p[0]), int(p[1])), r, color, -1)


def visualize_face_shape(image_path, output_path="results/face_shape_debug.jpg"):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Failed to load image: {image_path}")
        return False

    analyzer = FaceAnalyzer()
    classifier = FaceShapeClassifier()

    res = analyzer.detect_landmarks(img)
    if not res or not res.get('face_detected'):
        print("No face detected.")
        return False

    landmarks = res['landmarks_pixel']
    metrics = classifier.compute_metrics(landmarks)
    shape = classifier.classify(metrics)

    # Points (updated to use temples for forehead width and forehead top for length)
    fhl = landmarks[classifier.IDX_TEMPLE_LEFT]
    fhr = landmarks[classifier.IDX_TEMPLE_RIGHT]
    cbl = landmarks[classifier.IDX_CHEEKBONE_LEFT]
    cbr = landmarks[classifier.IDX_CHEEKBONE_RIGHT]
    jl = landmarks[classifier.IDX_JAW_LEFT]
    jr = landmarks[classifier.IDX_JAW_RIGHT]
    chin = landmarks[classifier.IDX_CHIN]
    forehead_top = landmarks[classifier.IDX_FOREHEAD_TOP]

    overlay = img.copy()
    # Forehead width
    draw_line(overlay, fhl, fhr, (0, 255, 0), 2)
    # Cheekbone width
    draw_line(overlay, cbl, cbr, (255, 0, 0), 2)
    # Jaw width
    draw_line(overlay, jl, jr, (0, 0, 255), 2)
    # Face length (chin to forehead top)
    draw_line(overlay, chin, forehead_top, (0, 255, 255), 2)

    # Mark key points
    for p in [fhl, fhr, cbl, cbr, jl, jr, chin, forehead_top]:
        draw_point(overlay, p, (255, 255, 255), 3)

    # Text annotations
    cv2.putText(overlay, f"Shape: {shape}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (50, 200, 50), 2)
    cv2.putText(overlay, f"L: {metrics['face_length']:.2f}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.putText(overlay, f"FW: {metrics['forehead_width']:.2f}", (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(overlay, f"CBW: {metrics['cheekbone_width']:.2f}", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    cv2.putText(overlay, f"JW: {metrics['jaw_width']:.2f}", (20, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.putText(overlay, f"Chin ∠: {metrics['chin_angle']:.1f}°", (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    ok = cv2.imwrite(output_path, overlay)
    if ok:
        print(f"Saved visualization to {output_path}")
    else:
        print("Failed to save visualization.")
    return ok


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate geometry-based face shape classification")
    parser.add_argument("image", help="Path to input image")
    parser.add_argument("--out", default="results/face_shape_debug.jpg", help="Output image path")
    args = parser.parse_args()

    visualize_face_shape(args.image, args.out)
