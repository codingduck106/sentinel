"""Phase 1 data prep: clean the Kaggle SMS Spam Collection and make leakage-safe splits.

Usage:  python src/prepare_data.py [--raw data/raw/spam.csv] [--out data/processed] [--seed 42]

Steps
  1. Rejoin text that the CSV export spilled into the `Unnamed: 2..4` columns at commas.
  2. Repair the mojibake (the original was double-encoded; ftfy does not catch these).
  3. Drop exact duplicate texts (after repair, so repaired copies collapse together).
  4. Group near-duplicates (same text once digits/URLs/amounts are masked, OR char-ngram
     TF-IDF cosine >= --sim) so spam templates never straddle train/val/test.
  5. StratifiedGroupKFold into 20 folds -> 14 train / 3 val / 3 test  (~70/15/15).
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedGroupKFold

# Ordered: longer sequences first so prefixes don't pre-empt them.
MOJIBAKE = [
    ("\x89Û÷", "'"), ("\x89ÛÏ", '"'), ("\x89ÛÒ", "–"), ("\x89Û_", "…"), ("\x89Ûª", "'"),
    ("å£", "£"), ("åÕ", "'"), ("åÐ", "–"), ("åÓ", '"'), ("åÔ", '"'),
    ("ÌÏ", "Ü"), ("Ì_", "ü"), ("Ì©", "é"), ("Ì¼", "¼"), ("Ì¬", "ñ"), ("Ìä", "ä"),
]


def repair(text: str) -> str:
    for bad, good in MOJIBAKE:
        text = text.replace(bad, good)
    text = html.unescape(text)                   # &lt;#&gt; -> <#>, &amp; -> &
    text = text.replace('\\"', '"').replace("\\", '"')  # export turned quotes into \ and \"
    return re.sub(r"\s+", " ", text).strip()


def template_key(text: str) -> str:
    t = text.lower()
    t = re.sub(r"(https?://|www\.)\S+", " <url> ", t)
    t = re.sub(r"[£$€]\s?[\d,.]+", " <amt> ", t)
    t = re.sub(r"\d+", "0", t)
    t = re.sub(r"[^a-z0<>]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def near_duplicate_groups(texts: pd.Series, threshold: float) -> list[int]:
    """Union-find over (a) identical template keys and (b) char-ngram TF-IDF cosine >= threshold."""
    parent = list(range(len(texts)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        parent[find(i)] = find(j)

    first: dict[str, int] = {}
    for i, k in enumerate(texts.map(template_key)):
        union(i, first.setdefault(k, i))

    X = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)).fit_transform(texts)
    S = (X @ X.T).tocoo()
    for i, j, s in zip(S.row, S.col, S.data):
        if i < j and s >= threshold:
            union(i, j)
    return [find(i) for i in range(len(texts))]


def load_raw(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="latin-1")
    extra = [c for c in df.columns if c.startswith("Unnamed")]
    df["text"] = df[["v2", *extra]].apply(
        lambda r: ",".join(str(x) for x in r if pd.notna(x)), axis=1
    )
    df["label"] = (df["v1"] == "spam").astype(int)
    return df[["text", "label"]]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw/spam.csv", type=Path)
    ap.add_argument("--out", default="data/processed", type=Path)
    ap.add_argument("--seed", default=42, type=int)
    ap.add_argument("--sim", default=0.8, type=float, help="near-duplicate cosine threshold")
    a = ap.parse_args()

    df = load_raw(a.raw)
    n_raw = len(df)
    df["text"] = df["text"].map(repair)

    # Same text with conflicting labels would be noise; report the count (first occurrence is kept).
    conflicts = df.groupby("text")["label"].nunique().gt(1).sum()
    df = df.drop_duplicates("text").reset_index(drop=True)
    df.insert(0, "id", [hashlib.md5(t.encode()).hexdigest()[:12] for t in df["text"]])
    df["group_id"] = near_duplicate_groups(df["text"], a.sim)
    gid = set(df["group_id"])

    sgkf = StratifiedGroupKFold(n_splits=20, shuffle=True, random_state=a.seed)
    fold = pd.Series(-1, index=df.index)
    for k, (_, idx) in enumerate(sgkf.split(df, df["label"], df["group_id"])):
        fold.iloc[idx] = k
    df["split"] = fold.map(lambda k: "test" if k < 3 else "val" if k < 6 else "train")

    # Hard guarantee: no template group appears in more than one split.
    assert df.groupby("group_id")["split"].nunique().max() == 1

    a.out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": "kaggle:uciml/sms-spam-collection-dataset (spam.csv)",
        "raw_sha256": sha256(a.raw),
        "seed": a.seed,
        "near_duplicate_threshold": a.sim,
        "raw_rows": n_raw,
        "exact_duplicates_removed": n_raw - len(df),
        "texts_with_conflicting_labels": int(conflicts),
        "rows_after_dedup": len(df),
        "template_groups": len(gid),
        "groups_with_multiple_members": int((df["group_id"].value_counts() > 1).sum()),
        "rows_in_multi_member_groups": int(df["group_id"].map(df["group_id"].value_counts()).gt(1).sum()),
        "splits": {},
    }
    for s in ["train", "val", "test"]:
        part = df[df["split"] == s][["id", "text", "label", "group_id"]]
        p = a.out / f"{s}.csv"
        part.to_csv(p, index=False)
        manifest["splits"][s] = {
            "rows": len(part),
            "spam": int(part["label"].sum()),
            "spam_ratio": round(part["label"].mean(), 4),
            "sha256": sha256(p),
        }
    (a.out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
