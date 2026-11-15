# Phase 2 — Classification pipeline & manipulation-tactic detection

_Last updated 2026-11-14_

```
                    ┌──────────────────────── classifier (src/sentinel/classifier.py) ───────────────────────┐
Input text ──┬────► │ normalize() → TF-IDF [word 1–2 + char_wb 3–5] → LogisticRegression(C=30) → P(spam)   │ ──► scam_probability, label
             │      └────────────────────────────────────────────────────────────────────────────────────────┘
             └────► tactics.detect()  (src/sentinel/tactics.py — independent, rule-based)                     ──► urgency / fear /
                                                                                                                 authority_impersonation / reward
```

## Usage
```bash
. .venv/bin/activate && pip install -e . -r requirements-dev.txt
python src/train.py                         # fit on train, select C + threshold on val
python src/eval_ood.py                      # OOD report (needs data/ood/*.parquet — see §5)
python -m sentinel.analyze "Final notice: your account will be suspended. Call 0800 123 4567 now"
python -m pytest                            # 37 tests
```
`analyze(text)` returns `{scam_probability, label, threshold, tactics: {name: {detected, score, evidence[]}}, tactics_detected}`.

## 1. Preprocessing (`preprocess.py`)
The pipeline runs this as its own first step, so training and inference can't drift apart.

Each corpus placeholder **and** the real-world value it replaced map to the same token:

| becomes | from |
|---|---|
| `num` | `<#>`, `<DECIMAL>`, any number, phone numbers, short codes |
| `urltok` | `<URL>`, real URLs and domains |
| `emailtok` | `<EMAIL>`, real email addresses |
| `timetok` | `<TIME>`, `10:30`, `5pm` |
| `moneytok` | `<UKP>2000`, `£2000`, `$350` |

**Why phone numbers and short codes have no token of their own.** The ham half of the corpus replaced *every* number with `<#>`. So in training, any long digit string is about 100% spam (a separate `phonetok` was 218 spam / 0 ham, and `shortcodetok` 191 / 4). The first model learned that artifact:
- It scored a plain OTP message ("Your verification code is 482913") at 0.38.
- On Indian SMS (§5), where legitimate bank alerts and order updates are full of digits, it did **worse than random** (ROC-AUC 0.39).

Collapsing both tokens into `num` cost −0.002 val PR-AUC and raised OOD ROC-AUC to 0.79. That is the shipped model. A variant that also collapsed `timetok` scored slightly higher OOD; I rejected it to avoid selecting on the OOD set.

## 2. Spam/legitimate classifier
- **Training and selection.** Trained on `train.csv`. **C** chosen by val PR-AUC, giving 30 (anything from 3 to 100 is within 0.002). **Threshold** set to max F1 on val, giving **0.353**. Both are saved in `models/spam_lr.joblib`, with metadata in `models/metrics.json`.
- **No class weighting**, which keeps `scam_probability` roughly calibrated (val Brier 0.018).
- **`scam_probability` = P(spam)** under the 2011 labels. "Spam" there includes legal marketing (ringtones, chat lines), so this is not literally the probability of fraud.

| split | precision | recall | F1 | PR-AUC | ROC-AUC | Brier | TN / FP / FN / TP |
|---|---:|---:|---:|---:|---:|---:|---|
| val | 0.966 | 0.875 | **0.918** | 0.955 | 0.983 | 0.018 | 675 / 3 / 12 / 84 |
| test | 0.990 | 0.990 | **0.990** | 0.998 | 1.000 | 0.006 | 677 / 1 / 1 / 95 |

⚠️ **The test set was evaluated twice:**
1. With the first model (`phonetok`/`shortcodetok`), giving F1 0.957.
2. With this model, after the token change that the OOD result motivated.

Nothing was tuned on test either time. Test has scored above val both times, so this test split looks easier than val. With 96 spam per split, **treat val (F1 ≈ 0.92) as the honest in-domain estimate**. The real limitation is OOD (§5), not in-domain accuracy.

**Top features.** The spam side is "call num", "num num", "to num", "txt", "text", `moneytok`, `urltok`, "free", "reply", "stop", "you have". The ham side is "i", "me", "my", "u", "at", "ok", "...". No placeholder-derived features remain.

## 3. Manipulation-tactic detection (`tactics.py`) — separate component
Rule-based by necessity, since no tactic labels exist. Each tactic is a list of weighted regex cues:
- `score = min(1, Σ weights of matched cues)`, where each cue counts once. This is a strength, **not a probability**.
- `detected` means score ≥ 0.5. A single weak cue ("free", "now", "congrats", "police", "by tonight", a bare brand name) scores below that and never triggers alone.
- Every match is returned as `{cue, text, start, end}` evidence.
- Detection runs on the original text, so evidence shows the real numbers and amounts.

| Tactic | Main cues |
|---|---|
| **urgency** | urgent, immediately, act/call/verify now, "within 24 hours", expires / valid 12hrs, final notice / last chance, "trying to contact you", today only / limited / hurry |
| **fear** | account/card **suspended / locked / compromised**, "will be closed/disconnected", unauthorized/suspicious **activity**, legal action / warrant / "will be arrested", penalty / fine, unpaid bill / failed payment, "failure to respond", "to avoid suspension" |
| **authority_impersonation** | banks, carriers, couriers, HMRC/IRS/SSA, big tech (stronger as a "Brand:" sender prefix or next to account/delivery/payment words), "security/fraud team", "valued customer", "our records show", "we have detected", delivery-attempt notices. Brands that are also ordinary words (EE, UPS, Apple, Orange, Chase…) only match when capitalized as the brand. |
| **reward** | "you have won", winner, "win a/£…", prize / jackpot / prize draw, claim / redeem / unclaimed, awarded / bonus / voucher / gift card, £100+, guaranteed, "you are owed a refund", free and cash (weak) |

**Development data:** `train.csv` plus the hand-written cases in `tests/test_tactics.py`: 9 modern scams and 13 ham traps such as "I'm fine", "we won the match", "you won't", "got arrested", "I'll chase the delivery guy". The rules were revised until these passed, so **they are dev checks, not evidence of accuracy**. On train, the detectors fire on 43.8% of spam and 0.54% of ham. Fear fires on 0% of train spam, because the 2011 corpus contains almost no threats. The independent evidence is §5.

## 4. Why the two components are kept separate: they fail differently
Illustrative messages, written by hand and also used in development:

| message | scam_probability | label | tactics |
|---|---:|---|---|
| HSBC: unusual activity… verify immediately at hsbc-secure-login.com | 0.52 | spam | urgency, fear, authority |
| Your Netflix payment failed… account will be suspended… within 24 hours | 0.08 | legitimate ❌ | urgency, fear, authority |
| Hi mum, new number… send me £200 urgently | 0.09 | legitimate ❌ | urgency |
| Your verification code is 482913. Do not share it. | 0.01 | legitimate ✅ | — |
| URGENT! You have won a £2000 prize. Call 0906… | 1.00 | spam ✅ | urgency, reward |

## 5. Out-of-distribution evaluation (`src/eval_ood.py`)
Data, deduplicated, saved under `data/ood/` (git-ignored):
- `CloveAI/india-spam-sms`: 19,230 unique messages, label 1 = spam (5,558).
- `BothBosu/scam-dialogue`: 1,600 synthetic phone-call transcripts, eight `type`s, 200 each.

**How these numbers were produced:**
- **Tactic rules:** frozen and run once. The only later change was the capitalization fix for common-word brands, which changed no India or dialogue number.
- **Classifier:** the India set **motivated the token collapse in §1**, so the India classifier numbers below are *after* that decision and are partly a dev number.

### India SMS: classifier
| model | PR-AUC | ROC-AUC | precision @thr | recall @thr | ham flagged |
|---|---:|---:|---:|---:|---:|
| first model (`phonetok`) | 0.23 | 0.39 | 0.24 | 0.50 | 65% |
| **shipped** | **0.58** | **0.79** | 0.53 | 0.78 | 28% |

Out of domain the classifier is still weak. It flags 28% of legitimate Indian SMS (bank debits, Aadhaar updates, delivery notices), because 2011 UK ham never looks like transactional brand messages.

### India SMS: tactic detectors (frozen rules)
| tactic | spam | ham |
|---|---:|---:|
| urgency | 47.5% | 0.0% |
| fear | 19.6% | 3.6% |
| authority_impersonation | 4.6% | 2.3% |
| reward | 29.6% | 8.7% |
| any tactic | 56.7% | 14.6% |
| **≥ 2 tactics** | **40.0%** | **0.0%** |

- **"≥ 2 tactics" is a strong signal:** it catches 40% of spam with zero false positives on 13.7K ham.
- **Single-tactic false positives come from real transactional messages.** "Income Tax Dept: your refund has been processed" triggers reward, and "-State Bank of India" triggers authority. Wording alone can't tell a genuine sender from an impersonator; a sender ID would be needed.
- **Missed by both components:** offer spam with no pressure language ("Flipkart Big Billion Days! 90% OFF: http://flipkart-sale856.com"), get-rich-quick, and dating lures. Social and romance lures and lookalike URLs are not detected yet.
- **A simple OR rule** (classifier OR ≥ 2 tactics), shown for information and not shipped, raises recall to 82.9% with no added false positives.

### Scam dialogues: tactic detectors (frozen rules), % of dialogues per type
| | type | urgency | fear | authority | reward |
|---|---|---:|---:|---:|---:|
| scam | ssn | 90.5 | **95.0** | 29.5 | 5.5 |
| scam | refund | 59.0 | 32.0 | **99.5** | **99.5** |
| scam | reward | 59.3 | 0.5 | 67.8 | **100.0** |
| scam | support | 23.5 | 25.5 | 29.0 | 5.0 |
| non-scam | delivery | 0.5 | 0.0 | 4.5 | 2.5 |
| non-scam | insurance | 17.0 | 0.5 | 9.0 | 13.5 |
| non-scam | telemarketing | 19.0 | 1.5 | 6.0 | 17.0 |
| non-scam | wrong number | 0.0 | 0.0 | 0.0 | 0.0 |

The detectors find the tactic each scam type is built around: fear in SSN threats, reward in prize and refund scams, authority in refund calls. The weak spot is tech-support scams (about 25%), which rely on "your computer has a virus" language that no rule covers yet. Long dialogues saturate scores, so read these as detection rates, not strengths.

### Held-out check (Phase 5): `alusci/sms-otp-spam-dataset`, never used for any decision
- **What's in it:** 10,000 rows but only **10 distinct templates** with digits varied: 5 legitimate OTP texts and 5 scams.
- **Why the row labels weren't used:** `label` means OTP *validity*. About 10% of genuine OTPs are "not valid", which here means an expired code, not spam. `status` is random.
- **How it was scored:** once per template through the full API (`risk_level`), with the frozen model and rules.

| | low | medium | high |
|---|---:|---:|---:|
| 5 legit OTP texts | 4 | 1 (`Use … to verify your account`, p = 0.21) | 0 |
| 5 scam texts | 1 (`Get a loan approved instantly. Reply with …`) | 1 (`Your account will be locked…`: fear only, p = 0.04) | 3 |

- **No OTP false positive:** before the digit-token fix (§1), `Your verification code is 482913` scored 0.38.
- **Same failure pattern as before:** the model misses modern phishing, and the tactic rules catch part of it.
- **Small sample:** this is n = 10 templates, so read it as a sanity check, not a benchmark.

## 6. Known limitations / next steps
1. **Classifier domain shift** is the main weakness: 28% false positives on modern transactional SMS. Next step: retrain with modern data (India SMS train portion, `alusci/sms-otp-spam-dataset`), keeping a clean held-out OOD set.
2. **Combined verdict.** "Classifier OR ≥ 2 tactics" looks promising, but needs its own held-out evaluation before shipping.
3. **Missing tactic cues:** tech-support ("virus", "remote access"), lookalike URLs (`brand-secure-login.com`), social/romance lures, money requests from "family" ("Hi mum").
4. **Real tactic labels:** hand-label about 300 messages to measure precision and recall properly, then consider a learned multi-label tactic model.

## Files
| file | role |
|---|---|
| `src/sentinel/preprocess.py` | normalization and the shared-token mapping |
| `src/sentinel/classifier.py` | `build_pipeline`, `SpamClassifier` (proba / predict / save / load / top_features) |
| `src/sentinel/tactics.py` | `TACTICS` cue tables, `detect()`, `detect_dict()` |
| `src/sentinel/analyze.py` | `analyze(text)` and the CLI |
| `src/train.py` | training and model selection; `--final-test` for the test report |
| `src/eval_ood.py` | OOD report, writes `models/ood_metrics.json` |
| `models/spam_lr.joblib` | trained model. Loading uses pickle: only load files you produced yourself. |
