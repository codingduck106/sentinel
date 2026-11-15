"""Headline numbers for the generalization study (docs/generalization_study.md).

    python src/generalization_report.py

Confidence intervals:
- 2011 val F1: message-level bootstrap (2,000 resamples).
- India ROC-AUC / detection rate: TEMPLATE-level (cluster) bootstrap. Messages generated from
  one template are not independent, so resampling messages would overstate certainty.
- Zero/near-zero false-positive counts: exact Clopper-Pearson 95% upper bound, at message
  level and at template level.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta
from sklearn.metrics import f1_score, roc_auc_score

sys.path.insert(0, str(Path(__file__).parent))
from sentinel.classifier import SpamClassifier  # noqa: E402
from sentinel.tactics import detect  # noqa: E402

B, SEED = 2000, 0


def template_key(t: str) -> str:
    t = re.sub(r"\d+", "0", t.lower())
    t = re.sub(r"https?://\S+|\S+\.(com|in|net|org)\S*", "<url>", t)
    return " ".join(t.split()[:6])


def cp_upper(k: int, n: int, a: float = 0.05) -> float:
    return 1.0 if k == n else float(beta.ppf(1 - a / 2, k + 1, n - k))


def cp_interval(k: int, n: int, a: float = 0.05) -> tuple[float, float]:
    lo = 0.0 if k == 0 else float(beta.ppf(a / 2, k, n - k + 1))
    return lo, cp_upper(k, n, a)


def main() -> None:
    rng = np.random.default_rng(SEED)
    clf = SpamClassifier.load()

    # --- 1. historical, in-domain (2011 UK) ---
    val = pd.read_csv("data/processed/val.csv")
    pv = clf.proba(val.text.tolist())
    yv, yhat = val.label.to_numpy(), (pv >= clf.threshold).astype(int)
    f1 = f1_score(yv, yhat)
    boots = [f1_score(yv[i], yhat[i]) for i in (rng.integers(0, len(yv), len(yv)) for _ in range(B))]
    print(f"[1] 2011 val: n={len(yv)} ({yv.sum()} spam) F1={f1:.3f} 95% CI [{np.percentile(boots, 2.5):.3f}, {np.percentile(boots, 97.5):.3f}]")

    # --- 2/3/4. modern (CloveAI India, synthetic-looking) ---
    d = pd.read_parquet("data/ood/india_spam.parquet").drop_duplicates("text").reset_index(drop=True)
    d["tpl"] = d.text.map(template_key)
    d["p"] = clf.proba(d.text.tolist())
    d["n_tac"] = [sum(v.detected for v in detect(t).values()) for t in d.text]
    d["ge2"] = d.n_tac >= 2
    scam, legit = d[d.label == 1], d[d.label == 0]
    print(f"    India: n={len(d)} unique msgs; scam {len(scam)} msgs / {scam.tpl.nunique()} templates; "
          f"legit {len(legit)} msgs / {legit.tpl.nunique()} templates")

    auc = roc_auc_score(d.label, d.p)
    tpls = {lab: d[d.label == lab].tpl.unique() for lab in (0, 1)}
    by_tpl = {k: g.index.to_numpy() for k, g in d.groupby("tpl")}
    aucs, dets = [], []
    for _ in range(B):
        idx = np.concatenate([by_tpl[t] for lab in (0, 1) for t in rng.choice(tpls[lab], len(tpls[lab]))])
        s = d.loc[idx]
        aucs.append(roc_auc_score(s.label, s.p))
        dets.append(s[s.label == 1].ge2.mean())
    print(f"[2] classifier ROC-AUC={auc:.3f} template-bootstrap 95% CI [{np.percentile(aucs, 2.5):.3f}, {np.percentile(aucs, 97.5):.3f}]")

    k_s, n_s = int(scam.ge2.sum()), len(scam)
    tpl_caught = scam.groupby("tpl").ge2.mean()
    print(f"[3] >=2 tactics on scams: {k_s}/{n_s} msgs = {k_s / n_s:.1%} "
          f"(template-bootstrap 95% CI [{np.percentile(dets, 2.5):.1%}, {np.percentile(dets, 97.5):.1%}]); "
          f"templates with >=50% of msgs caught: {(tpl_caught >= 0.5).sum()}/{len(tpl_caught)}")

    k_l, n_l = int(legit.ge2.sum()), len(legit)
    t_flag = legit.groupby("tpl").ge2.any()
    print(f"[4] >=2 tactics on legit: {k_l}/{n_l} msgs; 95% upper bound {cp_upper(k_l, n_l):.3%} (message-level, optimistic) | "
          f"templates with any flagged msg: {int(t_flag.sum())}/{len(t_flag)}; 95% upper bound {cp_upper(int(t_flag.sum()), len(t_flag)):.2%} (template-level)")
    for t in legit[legit.ge2].text.head(5):
        print("      flagged legit:", t[:110])

    # also on the historical legit messages (different distribution, real messages)
    tr = pd.read_csv("data/processed/train.csv")
    h = [sum(v.detected for v in detect(t).values()) >= 2 for t in tr[tr.label == 0].text]
    print(f"    2011 train legit >=2 tactics: {sum(h)}/{len(h)}; 95% upper bound {cp_upper(sum(h), len(h)):.2%}")


if __name__ == "__main__":
    main()
