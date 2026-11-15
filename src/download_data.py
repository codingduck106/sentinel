"""Download the Kaggle SMS Spam Collection (public; no Kaggle credential needed).

Usage:  python src/download_data.py [--out data/raw]
"""
import argparse
import hashlib
from pathlib import Path

import kagglehub

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="data/raw")
a = ap.parse_args()

path = kagglehub.dataset_download("uciml/sms-spam-collection-dataset", output_dir=a.out)
csv = Path(path) / "spam.csv"
print(f"{csv}  sha256={hashlib.sha256(csv.read_bytes()).hexdigest()}")
