"""False-positive investigation: classifier thresholds and risk-rule variants.

    python src/eval_risk_rules.py              # dev report only (choose here)
    python src/eval_risk_rules.py --holdout    # ALSO the untouched India holdout half (report once)

Data
- 2011 val.csv: in-domain dev (already used for C/threshold selection; not test, which is spent).
- CloveAI India SMS, split BY TEMPLATE (first 6 tokens, digits/URLs masked) into dev / holdout
  halves, stratified so each half gets ~half the scam templates. Rules are compared on dev; the
  holdout is reported once, after choosing.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from sentinel.classifier import SpamClassifier  # noqa: E402
from sentinel.tactics import detect  # noqa: E402

SEED = 0
THRESHOLDS = [0.2, 0.3, 0.353, 0.5, 0.6, 0.7, 0.8, 0.9]

CATEGORIES = {  # first match wins; for legitimate messages only
    "bank": r"\b(bank|a/c|acct|debited|credited|avl bal|upi|neft|imps|credit card|sbi|hdfc|icici|axis|kotak)\b",
    "delivery": r"\b(deliver\w*|order|shipped|dispatched|out for delivery|courier|parcel|package|track\w*|return)\b",
    "otp/login": r"\b(otp|verification code|one[- ]time|login|password)\b",
    "gov/utility": r"\b(aadhaar|pan|epfo|passport|income tax|gst|electricity|gas|water bill|pension)\b",
    "telecom": r"\b(jio|airtel|vi|bsnl|recharge|data|validity|balance)\b",
}


def template_key(t: str) -> str:
    t = re.sub(r"\d+", "0", t.lower())
    t = re.sub(r"https?://\S+|\S+\.(com|in|net|org)\S*", "<url>", t)
    return " ".join(t.split()[:6])


def category(t: str) -> str:
    for name, rx in CATEGORIES.items():
        if re.search(rx, t, re.I):
            return name
    return "personal/other"


def score_frame(df: pd.DataFrame, text_col: str, clf: SpamClassifier) -> pd.DataFrame:
    out = df.copy()
    out["p"] = clf.proba(out[text_col].tolist())
    tac = [detect(t) for t in out[text_col]]
    out["n_tac"] = [sum(v.detected for v in d.values()) for d in tac]
    return out


# ---------- risk rules: each returns "high" / "medium" / "low" arrays ----------
def rule_current(p, n, thr):
    """Shipped rule: classifier spam alone OR >= 2 tactics -> High."""
    high = (p >= thr) | (n >= 2)
    med = (n == 1) | (p >= 0.2)
    return np.where(high, "high", np.where(med, "medium", "low"))


def rule_threshold(t_spam):
    def r(p, n, thr):
        return rule_current(p, n, t_spam)
    r.__doc__ = f"Shipped rule with the classifier threshold raised to {t_spam}."
    return r


def rule_two_signals(p, n, thr):
    """High needs two independent signals: (classifier spam AND >= 1 tactic) OR >= 2 tactics.
    Classifier alone, or one tactic alone -> Medium."""
    spam = p >= thr
    high = (spam & (n >= 1)) | (n >= 2)
    med = spam | (n == 1) | (p >= 0.2)
    return np.where(high, "high", np.where(med, "medium", "low"))


def rule_two_signals_confident(t_conf):
    def r(p, n, thr):
        base = rule_two_signals(p, n, thr)
        return np.where(p >= t_conf, "high", base)
    r.__doc__ = f"Two signals, but a very confident classifier (p >= {t_conf}) still counts as High alone."
    return r


def rule_two_signals_strict_medium(p, n, thr):
    """Two signals for High; Medium needs a real signal (classifier spam or 1 tactic),
    not merely p >= 0.2."""
    spam = p >= thr
    high = (spam & (n >= 1)) | (n >= 2)
    med = spam | (n == 1)
    return np.where(high, "high", np.where(med, "medium", "low"))


def rule_tactics_gate(p, n, thr):
    """The classifier only counts when a tactic corroborates it: classifier alone -> Low."""
    spam = p >= thr
    high = (spam & (n >= 1)) | (n >= 2)
    med = n == 1
    return np.where(high, "high", np.where(med, "medium", "low"))


RULES = {
    "R0 current (spam OR >=2 tactics)": rule_current,
    "R1 raise threshold to 0.7": rule_threshold(0.7),
    "R2 raise threshold to 0.9": rule_threshold(0.9),
    "R3 two signals": rule_two_signals,
    "R4 two signals + p>=0.9 alone": rule_two_signals_confident(0.9),
    "R5 two signals + p>=0.97 alone": rule_two_signals_confident(0.97),
    "R6 two signals, Medium needs a signal": rule_two_signals_strict_medium,
    "R7 classifier only counts with a tactic": rule_tactics_gate,
}


def threshold_table(df: pd.DataFrame, name: str) -> pd.DataFrame:
    y = df.label.to_numpy()
    rows = []
    for t in THRESHOLDS:
        pred = df.p.to_numpy() >= t
        tp, fp = (pred & (y == 1)).sum(), (pred & (y == 0)).sum()
        rows.append({"set": name, "thr": t, "precision": tp / max(1, tp + fp), "recall": tp / max(1, (y == 1).sum()),
                     "ham_flagged": fp / max(1, (y == 0).sum())})
    return pd.DataFrame(rows)


def rule_table(df: pd.DataFrame, name: str, thr: float, by_category: bool) -> pd.DataFrame:
    rows = []
    for rname, rule in RULES.items():
        lvl = rule(df.p.to_numpy(), df.n_tac.to_numpy(), thr)
        spam, ham = df.label.to_numpy() == 1, df.label.to_numpy() == 0
        row = {"set": name, "rule": rname,
               "scam→High": (lvl[spam] == "high").mean(),
               "scam→≥Medium": (lvl[spam] != "low").mean(),
               "legit→High": (lvl[ham] == "high").mean(),
               "legit→≥Medium": (lvl[ham] != "low").mean()}
        if by_category:
            for c in ["bank", "delivery"]:
                m = ham & (df.cat.to_numpy() == c)
                row[f"{c}→High"] = (lvl[m] == "high").mean() if m.any() else np.nan
                row[f"{c}→≥Med"] = (lvl[m] != "low").mean() if m.any() else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--holdout", action="store_true")
    a = ap.parse_args()
    pd.set_option("display.width", 200, "display.max_columns", 20, "display.precision", 3)

    clf = SpamClassifier.load()
    thr = clf.threshold

    val = score_frame(pd.read_csv("data/processed/val.csv"), "text", clf)

    india = pd.read_parquet("data/ood/india_spam.parquet").drop_duplicates("text").reset_index(drop=True)
    india["group"] = india.text.map(template_key)
    india["cat"] = np.where(india.label == 0, india.text.map(category), "scam")
    rng = np.random.default_rng(SEED)
    groups = india.groupby("group").label.max()  # a template is "scam" if any member is
    dev_groups = set()
    for lab in (0, 1):
        g = groups[groups == lab].index.to_numpy()
        rng.shuffle(g)
        dev_groups |= set(g[: len(g) // 2])
    india["split"] = np.where(india.group.isin(dev_groups), "dev", "holdout")
    india = score_frame(india, "text", clf)
    dev, hold = india[india.split == "dev"], india[india.split == "holdout"]
    print(f"classifier threshold (chosen on 2011 val): {thr:.3f}")
    print(f"India dev: {len(dev)} msgs ({dev.label.sum()} scam, {dev.group[dev.label == 1].nunique()} scam templates) | "
          f"holdout: {len(hold)} msgs ({hold.label.sum()} scam, {hold.group[hold.label == 1].nunique()} scam templates)\n")

    print("=== A. Classifier alone: threshold sweep ===")
    print(pd.concat([threshold_table(val, "2011 val"), threshold_table(dev, "India dev")]).to_string(index=False))

    print("\n=== B. Where the false positives are (India dev, legit messages, classifier at shipped threshold) ===")
    ham = dev[dev.label == 0]
    fp = (ham.groupby("cat").apply(lambda g: pd.Series({"n": len(g), "flagged_spam": (g.p >= thr).mean(),
                                                         "≥1 tactic": (g.n_tac >= 1).mean(), "≥2 tactics": (g.n_tac >= 2).mean()}),
                                   include_groups=False))
    print(fp.sort_values("n", ascending=False).to_string())
    print("\nexample flagged legit messages:")
    for c in ["bank", "delivery"]:
        for t in ham[(ham.cat == c) & (ham.p >= thr)].text.head(3):
            print(f"  [{c}] {t[:100]}")

    print("\n=== C. Risk rules (dev) ===")
    print(rule_table(val, "2011 val", thr, False).to_string(index=False))
    print()
    print(rule_table(dev, "India dev", thr, True).to_string(index=False))

    if a.holdout:
        print("\n=== D. India HOLDOUT (untouched templates; report once) ===")
        print(threshold_table(hold, "India holdout").to_string(index=False))
        print()
        print(rule_table(hold, "India holdout", thr, True).to_string(index=False))


if __name__ == "__main__":
    main()
