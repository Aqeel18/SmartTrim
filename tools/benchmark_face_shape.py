import os
import sys
import csv
import random
import argparse
import cv2

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.face_analysis import FaceAnalyzer
from app.core.face_shape_classifier import FaceShapeClassifier


def canonical_label(name: str) -> str:
    """Map folder names to classifier's canonical labels."""
    n = (name or '').strip().lower().replace('-', ' ').replace('_', ' ')
    n = ' '.join(n.split())
    mapping = {
        'oval': 'Oval',
        'round': 'Round',
        'square': 'Square',
        'heart': 'Heart',
        'oblong': 'Oblong',
        'rectangle': 'Oblong',
        'rectangular': 'Oblong',
        'long': 'Oblong',
        'diamond': 'Diamond',
        'triangular': 'Triangle',
        'triangle': 'Triangle',
    }
    return mapping.get(n, name.strip())


def list_images(root_dir, label_filter=None, limit_per_label=None):
    """
    Scans `root_dir` for subfolders (each treated as a label) and collects images.
    - label_filter: optional set of label names to include (case-insensitive)
    - limit_per_label: optional int limit per label
    Returns dict: { label: [image_paths...] }
    """
    data = {}
    if not os.path.isdir(root_dir):
        raise FileNotFoundError(f"Root dir not found: {root_dir}")

    # Normalize filter to canonical labels if provided
    canonical_filter = None
    if label_filter:
        canonical_filter = {canonical_label(l) for l in label_filter}

    for entry in os.listdir(root_dir):
        sub = os.path.join(root_dir, entry)
        if not os.path.isdir(sub):
            continue
        label = canonical_label(entry)
        if canonical_filter and label not in canonical_filter:
            continue
        imgs = []
        for fname in os.listdir(sub):
            if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                imgs.append(os.path.join(sub, fname))
        random.shuffle(imgs)
        if limit_per_label is not None:
            imgs = imgs[:limit_per_label]
        if imgs:
            data[label] = imgs
    return data


def evaluate_dataset(root, labels=None, limit=10, out_csv="results/face_shape_benchmark.csv", out_summary="results/face_shape_benchmark.txt"):
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    os.makedirs(os.path.dirname(out_summary), exist_ok=True)

    # Prepare data
    label_filter = labels if labels else None
    data = list_images(root, label_filter=label_filter, limit_per_label=limit)
    if not data:
        print("No data found. Ensure directory structure: root/<Label>/*.jpg|png")
        return False

    analyzer = FaceAnalyzer()
    classifier = FaceShapeClassifier()

    # Tracking
    rows = []
    confusion = {}
    totals = {}
    corrects = {}

    # Flatten
    for gt_label, paths in data.items():
        for p in paths:
            img = cv2.imread(p)
            if img is None:
                print(f"[WARN] Failed to read: {p}")
                continue
            res = analyzer.detect_landmarks(img)
            if not res or not res.get('face_detected'):
                pred = 'NO_FACE'
                metrics = {}
            else:
                try:
                    metrics = classifier.compute_metrics(res['landmarks_pixel'])
                    pred = classifier.classify(metrics)
                except Exception as e:
                    print(f"[WARN] Metrics failed for {p}: {e}")
                    pred = 'ERROR'
                    metrics = {}

            # Update stats
            totals[gt_label] = totals.get(gt_label, 0) + 1
            if gt_label not in confusion:
                confusion[gt_label] = {}
            confusion[gt_label][pred] = confusion[gt_label].get(pred, 0) + 1
            if pred == gt_label:
                corrects[gt_label] = corrects.get(gt_label, 0) + 1

            rows.append({
                'image': p,
                'ground_truth': gt_label,
                'predicted': pred,
                'face_shape': pred,
                'face_length': metrics.get('face_length'),
                'forehead_width': metrics.get('forehead_width'),
                'cheekbone_width': metrics.get('cheekbone_width'),
                'jaw_width': metrics.get('jaw_width'),
                'chin_angle': metrics.get('chin_angle'),
            })

    # Write CSV
    fieldnames = ['image', 'ground_truth', 'predicted', 'face_shape', 'face_length', 'forehead_width', 'cheekbone_width', 'jaw_width', 'chin_angle']
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # Build summary
    lines = []
    total = sum(totals.values())
    total_correct = sum(corrects.values())
    overall_acc = (total_correct / total) if total else 0.0
    lines.append(f"Total images: {total}")
    lines.append(f"Overall accuracy: {overall_acc:.3f}")
    lines.append("")
    lines.append("Per-class accuracy:")
    for lbl in sorted(totals.keys()):
        acc = (corrects.get(lbl, 0) / totals[lbl]) if totals[lbl] else 0.0
        lines.append(f"  - {lbl}: {acc:.3f} ({corrects.get(lbl, 0)}/{totals[lbl]})")
    lines.append("")
    lines.append("Confusion matrix (counts):")
    # Determine column labels
    pred_labels = set()
    for d in confusion.values():
        pred_labels.update(d.keys())
    pred_labels = sorted(pred_labels)
    header = ['GT\\Pred'] + pred_labels
    widths = [max(len(h), 8) for h in header]
    # header line
    hdr = "  ".join(h.ljust(w) for h, w in zip(header, widths))
    lines.append(hdr)
    for gt in sorted(confusion.keys()):
        row = [gt.ljust(widths[0])]
        for j, pred in enumerate(pred_labels, start=1):
            row.append(str(confusion[gt].get(pred, 0)).ljust(widths[j]))
        lines.append("  ".join(row))

    with open(out_summary, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print(f"Saved CSV to {out_csv}")
    print(f"Saved summary to {out_summary}")
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Benchmark face shape classifier on a labeled folder structure.')
    parser.add_argument('--root', required=True, help='Root folder with subfolders per label (e.g., Oval, Round, Square, Heart, Oblong).')
    parser.add_argument('--labels', default='', help='Comma-separated labels to include (e.g., Oval,Round,Square,Heart,Oblong). If empty, include all.')
    parser.add_argument('--limit', type=int, default=10, help='Max images per label to evaluate.')
    parser.add_argument('--out_csv', default='results/face_shape_benchmark.csv', help='Output CSV file path.')
    parser.add_argument('--out_summary', default='results/face_shape_benchmark.txt', help='Output summary text file path.')
    args = parser.parse_args()

    labels = [s.strip() for s in args.labels.split(',') if s.strip()] if args.labels else None
    evaluate_dataset(args.root, labels=labels, limit=args.limit, out_csv=args.out_csv, out_summary=args.out_summary)
