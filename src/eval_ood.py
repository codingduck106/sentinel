"""Out-of-distribution evaluation on data the model and rules were never developed on.

    python src/eval_ood.py            # needs data/ood/*.parquet (see docs/phase2_classifier.md)

- CloveAI/india-spam-sms (label 1 = spam): classifier metrics + tactic rates by class.
- BothBosu/scam-dialogue: tactic detection rate per dialogue `type` (classifier not
  applicable: multi-turn phone transcripts, not SMS).
Exact-duplicate texts are dropped first (both sets are heavily templated).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import average_precision_score, precision_score, recall_score, roc_auc_score

sys.path.insert(0, str(Path(__file__).parent))
from veritas.classifier import SpamClassifier  # noqa: E402
from veritas.tactics import TACTICS, detect  # noqa: E402

OOD = Path("data/ood")


def tactic_frame(texts) -> pd.DataFrame:
    return pd.DataFrame([{k: v.detected for k, v in detect(t).items()} for t in texts])


def main() -> None:
    clf = SpamClassifier.load()
    out = {}

    india = pd.read_parquet(OOD / "india_spam.parquet").drop_duplicates("text").reset_index(drop=True)
    p = clf.proba(india.text.tolist())
    yhat = p >= clf.threshold
    out["india_classifier"] = {
        "n": len(india), "spam": int(india.label.sum()),
        "pr_auc": round(average_precision_score(india.label, p), 4),
        "roc_auc": round(roc_auc_score(india.label, p), 4),
        "precision@thr": round(precision_score(india.label, yhat), 4),
        "recall@thr": round(recall_score(india.label, yhat), 4),
        "ham_fpr@thr": round(yhat[india.label == 0].mean(), 4),
    }
    T = tactic_frame(india.text)
    T["any"] = T.any(axis=1)
    T["ge2"] = T[list(TACTICS)].sum(axis=1) >= 2
    rates = pd.DataFrame({"spam_%": 100 * T[india.label == 1].mean(), "ham_%": 100 * T[india.label == 0].mean()}).round(1)
    out["india_tactics"] = rates.to_dict()
    # simple OR-rule, reported for information only (not part of the shipped pipeline)
    combo = yhat | T["ge2"].to_numpy()
    out["india_or_rule(classifier OR >=2 tactics)"] = {
        "recall": round(combo[india.label == 1].mean(), 4), "ham_fpr": round(combo[india.label == 0].mean(), 4)}

    sd = pd.read_parquet(OOD / "scam_dialogue.parquet").drop_duplicates("dialogue").reset_index(drop=True)
    D = tactic_frame(sd.dialogue)
    D["type"], D["label"] = sd["type"], sd["label"]
    out["dialogue_tactics_%_by_type"] = (100 * D.groupby(["label", "type"])[list(TACTICS)].mean()).round(1).reset_index().to_dict("records")

    print(json.dumps(out, indent=2))
    print("\nIndia tactic rates (%):\n", rates.to_string())
    print("\nScam-dialogue tactic rates (%) by type:\n",
          (100 * D.groupby(["label", "type"])[list(TACTICS)].mean()).round(1).to_string())
    print("\nIndia ham flagged by authority_impersonation (sample):")
    for t in india.text[(india.label == 0) & T["authority_impersonation"]].head(6):
        print("  ", t[:110])
    print("India ham flagged by classifier (sample):")
    for t in india.text[(india.label == 0) & yhat].head(6):
        print("  ", t[:110])
    print("India spam missed by classifier AND tactics (sample):")
    for t in india.text[(india.label == 1) & ~yhat & ~T["any"].to_numpy()].head(6):
        print("  ", t[:110])
    Path("models/ood_metrics.json").write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
