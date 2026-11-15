# False positives on legitimate bank and delivery texts

_2026-11-14. Reproduce with `python src/eval_risk_rules.py [--holdout]`._

## The problem
- **What the old rule did:** a "spam" verdict from the classifier was enough on its own for **High risk** ("This looks like a scam").
- **Why that went wrong:** the classifier learned UK SMS spam from 2011. Out of domain it is *confidently* wrong on modern transactional texts.
- **Scale:** depending on which message templates are sampled, **12–37% of legitimate Indian SMS** were rated High, including **72% of legitimate delivery texts**.

## Method
- **Data:**
  - 2011 `val.csv`: the in-domain dev set. `test.csv` is not used, because it has already been evaluated twice.
  - CloveAI Indian SMS, split **by template** (first six tokens, with digits and URLs masked) into a dev half and a holdout half. Scams come from only **41 templates**, so results swing a lot with the split.
- **Process:** I compared the rules on dev and picked one, then evaluated the holdout once.
- **Messages by category:** legitimate messages are tagged by keyword as bank, delivery, OTP/login, government/utility, telecom or personal.

## A. Changing the classifier threshold doesn't fix it

| threshold | 2011 val precision / recall | India dev precision / recall | India dev legitimate flagged |
|---|---|---|---|
| 0.353 (shipped) | 0.97 / 0.88 | 0.45 / 0.80 | 36.7% |
| 0.5 | 0.98 / 0.85 | 0.56 / 0.68 | 19.7% |
| 0.7 | 0.99 / 0.81 | 0.52 / 0.54 | 18.2% |
| 0.9 | 1.00 / 0.78 | 0.50 / 0.36 | 13.2% |

Delivery texts (links, "track", order numbers) score as confidently as 2011 spam. At a threshold of 0.9, half of them are still High, while scam recall has collapsed.

## B. Where the false positives come from (India dev, legitimate messages, shipped threshold)

| category | n | classifier says spam | ≥ 1 tactic | ≥ 2 tactics |
|---|---:|---:|---:|---:|
| delivery | 2,301 | 72% | 26% | 0% |
| gov/utility | 1,442 | 40% | 12% | 0% |
| telecom | 1,487 | 25% | 0% | 0% |
| personal | 1,323 | 24% | 0% | 0% |
| bank | 2,239 | 14% | 14% | 0% |

Almost no legitimate message shows two tactics: 0.01% of 13,672. The false positives are **single-signal** verdicts.

## C. Rules compared (dev)

| rule | 2011 scam→High | India scam→High | India legit→High | India legit→≥Medium |
|---|---:|---:|---:|---:|
| R0 classifier spam OR ≥ 2 tactics (old) | 87.5% | 89.0% | 36.6% | 57.2% |
| R1/R2 R0 with threshold 0.7 / 0.9 | 81% / 78% | 76% / 68% | 18.2% / 13.2% | 57.2% |
| **R3 two signals:** (spam AND ≥ 1 tactic) OR ≥ 2 tactics | 40.6% | 76.2% | **2.9%** | 57.2% |
| R4/R5 R3, but p ≥ 0.9 / 0.97 alone still High | 80% / 74% | 76% | 16.1% / 12.6% | 57.2% |
| R6 R3, and Medium needs a signal (drops p ≥ 0.2) | 40.6% | 76.2% | 2.9% | 46.1% |
| R7 classifier counts only with a tactic | 40.6% | 76.2% | 2.9% | 12.3% |

- **R4/R5:** exempting "confident" classifier verdicts brings the delivery false positives back, because the confidence itself is wrong out of domain.
- **R7:** fixes Medium, but **58% of 2011 spam becomes "This looks like a normal message"**, including ringtone subscription traps. Rejected.
- **Dev pick:** R6.
- **The 2011 High drop under R3/R6 is mostly not scams.** The 45 spam messages that move from High to Medium are mostly ringtone subscriptions, adult chat lines and marketing. None of them move to Low.

## D. Holdout (one look, before any further change)

| rule | scam→High | scam→≥Medium | legit→High | legit→≥Medium |
|---|---:|---:|---:|---:|
| R0 (old) | 74.4% | 85.5% | 12.2% | 28.4% |
| R3 | 29.8% | 85.5% | 2.6% | 28.4% |
| R6 | 29.8% | **74.4%** | 2.6% | 28.4% |

- **The two-signal High rule replicated:** legitimate → High fell by about 80% on both halves.
- **R6's Medium change did not:** on the holdout it moved 11% of scams to Low and helped no legitimate message.
- **Shipped: R3**, the smaller change.
- **The scam→High cost is larger on the holdout.** Reading those scams showed tactic-rule gaps, several of them bugs.

## E. Tactic-cue fixes (general bugs, not tuned to particular messages)
- **Fixed:**
  - `expire` was not matched, only `expires` and `expiry`.
  - "you **are** selected" was not matched, only "you have been selected".
  - A bare "refund" counted as a reward lure ("Your refund … has been processed"). Now only "you're owed/entitled/eligible", "unclaimed refund" or "claim your refund" count; a bare "refund" is a weak cue.
  - "Bank of X" counted as an official claim, which flagged genuine "-State Bank of India" signatures. Now it is a weak cue.
- **Not added:** a ₹/INR money cue (legitimate INR refund notices would then trigger two tactics), and new categories for fake-sale and dating lures (found by reading holdout scams; left for later).
- **Effect:** legitimate Indian messages with ≥ 1 tactic fell from 14.6% to **3.6%**, and scams with ≥ 1 tactic rose from 56.7% to 65.9%. The ≥ 2 tactics rate is unchanged: 0.01% legitimate, 40.0% scam. 2011 rates are unchanged.

## Result (shipped rule R3 with cue fixes; every India number is now a **dev** number)

| | scam→High | scam→≥Medium | legit→High |
|---|---:|---:|---:|
| 2011 val | 87.5% → **40.6%** | 89.6% → 89.6% | 0.4% → **0%** |
| India dev | 89.0% → **79.1%** | 89.0% → 89.0% | 36.6% → **1.4%** (delivery 72% → 0%, bank 14% → 0%) |
| India holdout | 74.4% → **47.6%** | 85.5% → 85.5% | 12.2% → **2.6%** |

## Not solved
- **Medium is still noisy:** 28–57% of legitimate Indian messages are rated Medium, almost all because of the classifier alone. Removing that would hide 2011 spam (R7). The fix is **retraining the classifier on modern SMS**, with a held-out modern set kept clean.
- **Signals aren't fully independent:** words like "claim", "won" and "urgent" feed both the classifier and the tactic rules.
- **Small sample:** 41 scam templates in total, so treat each percentage above as roughly ±10 points.
