import os
import sys
import argparse

# Ensure repo root on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from tools.benchmark_face_shape import evaluate_dataset


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Benchmark face shape classifier on a labeled folder structure (4-class).')
    parser.add_argument('--root', required=True, help='Root folder with subfolders per label (e.g., Oval, Round, Oblong, Diamond).')
    parser.add_argument('--labels', default='Oval,Round,Oblong,Diamond', help='Comma-separated labels to include. Default: Oval,Round,Oblong,Diamond')
    parser.add_argument('--limit', type=int, default=20, help='Max images per label to evaluate.')
    parser.add_argument('--out_csv', default='results/face_shape_benchmark.csv', help='Output CSV file path.')
    parser.add_argument('--out_summary', default='results/face_shape_benchmark.txt', help='Output summary text file path.')
    args = parser.parse_args()

    labels = [s.strip() for s in args.labels.split(',') if s.strip()] if args.labels else None
    evaluate_dataset(args.root, labels=labels, limit=args.limit, out_csv=args.out_csv, out_summary=args.out_summary)

