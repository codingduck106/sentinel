"""Train the spam classifier on train.csv, select C and threshold on val.csv.

Usage:
    python src/train.py              # fit + val report, saves models/spam_lr.joblib
    python src/train.py --final-test # ALSO report on test.csv. Do this once, at the end.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import (average_precision_score, brier_score_loss, confusion_matrix,
                             f1_score, precision_recall_curve, precision_score, recall_score,
                             roc_auc_score)

sys.path.insert(0, str(Path(__file__).parent))
from veritas.classifier import DEFAULT_MODEL, SpamClassifier, build_pipeline  # noqa: E402

DATA = Path("data/processed")


def report(name: str, y, p, thr) -> dict:
    yhat = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, yhat).ravel()
    r = {"split": name, "n": len(y), "threshold": round(thr, 3),
         "precision": round(precision_score(y, yhat), 4), "recall": round(recall_score(y, yhat), 4),
         "f1": round(f1_score(y, yhat), 4), "pr_auc": round(average_precision_score(y, p), 4),
         "roc_auc": round(roc_auc_score(y, p), 4), "brier": round(brier_score_loss(y, p), 4),
         "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}}
    print(json.dumps(r))
    return r


def best_threshold(y, p) -> float:
    prec, rec, thr = precision_recall_curve(y, p)
    f1 = 2 * prec[:-1] * rec[:-1] / np.clip(prec[:-1] + rec[:-1], 1e-9, None)
    return float(thr[int(np.argmax(f1))])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--final-test", action="store_true")
    a = ap.parse_args()

    tr, va = pd.read_csv(DATA / "train.csv"), pd.read_csv(DATA / "val.csv")

    print("C sweep (val PR-AUC):")
    results = {}
    for C in [0.3, 1, 3, 10, 30, 100]:
        pipe = build_pipeline(C).fit(tr.text.tolist(), tr.label)
        results[C] = average_precision_score(va.label, pipe.predict_proba(va.text.tolist())[:, 1])
        print(f"  C={C:<5} pr_auc={results[C]:.4f}")
    C = max(results, key=results.get)

    pipe = build_pipeline(C).fit(tr.text.tolist(), tr.label)
    clf = SpamClassifier(pipe)
    p_va = clf.proba(va.text.tolist())
    clf.threshold = best_threshold(va.label, p_va)
    manifest = json.loads((DATA / "manifest.json").read_text())
    clf.meta = {"C": C, "threshold_rule": "max F1 on val", "sklearn": sklearn.__version__,
                "train_sha256": manifest["splits"]["train"]["sha256"], "trained_on": "train.csv only"}

    print(f"\nchosen C={C}, threshold={clf.threshold:.3f}")
    metrics = {"val@0.5": report("val@0.5", va.label, p_va, 0.5),
               "val": report("val", va.label, p_va, clf.threshold)}

    spam_f, ham_f = clf.top_features(25)
    print("\ntop spam features:", spam_f)
    print("top ham features: ", ham_f)

    if a.final_test:
        te = pd.read_csv(DATA / "test.csv")
        p_te = clf.proba(te.text.tolist())
        metrics["test"] = report("test", te.label, p_te, clf.threshold)
        miss = te.assign(p=p_te)[(p_te >= clf.threshold) != te.label.astype(bool)]
        print("\ntest errors:")
        for _, r in miss.sort_values("p").iterrows():
            print(f"  [{'SPAM' if r.label else 'ham '} p={r.p:.2f}] {r.text[:120]}")

    clf.meta["metrics"] = metrics
    clf.save(DEFAULT_MODEL)
    Path("models/metrics.json").write_text(json.dumps(clf.meta, indent=2))
    print(f"\nsaved {DEFAULT_MODEL}")


if __name__ == "__main__":
    main()
