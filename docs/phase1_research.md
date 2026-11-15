# Phase 1 — Research & Data

_Last updated 2026-11-14_

## 1. Dataset acquisition (Kaggle)

| | |
|---|---|
| Source | Kaggle `uciml/sms-spam-collection-dataset` → `data/raw/spam.csv` (downloaded via kagglehub, no credential needed) |
| Original | Almeida & Gómez Hidalgo (2011), UCI SMS Spam Collection v.1 |
| Raw size | 5,572 rows, 4,825 ham / 747 spam, binary labels only |
| License | Unclear. HF `ucirvine/sms_spam` says "unknown" and `codesignal/sms-spam-collection` says CC-BY-4.0. Cite the original paper and check before any redistribution. |

To reproduce:
```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -e . -r requirements-dev.txt
python src/download_data.py        # raw sha256 should be 440e6ea9…1dfc2 (also in manifest.json)
python src/prepare_data.py          # -> data/processed/{train,val,test}.csv + manifest.json
python src/weak_labels.py --sample 12
```

### Cleaning problems found and fixed (`src/prepare_data.py`)
1. **Text split across columns.** 50 rows had commas that pushed text into `Unnamed: 2..4`. These pieces are rejoined, not dropped.
2. **Mojibake (garbled characters).** The text was double-encoded, and `ftfy` does not repair it. A hand-built map fixes `å£`→`£` (about 330 cases), `åÕ`/`‰Û÷`→`'`, `Ì_`→`ü` and `ÌÏ`→`Ü` (SMS shorthand for "you"), `‰Û_`→`…`, and `\"` export artifacts. HTML entities are unescaped as well (`&lt;#&gt;` becomes `<#>`).
3. **Exact duplicates.** 414 removed, giving **5,158 rows (4,516 ham / 642 spam)**. No duplicate text had conflicting labels. Cross-check: the independent dedupe `jngb-labs/sms-spam` ends with 5,159 / 4,517 / 642.

## 2. Splits (leakage-safe)

Spam in this corpus is mostly templates: the same message is sent with different phone numbers, claim codes or prize amounts. A plain stratified split put **22 of the 96 test spam** messages next to a near-copy in train (char-ngram cosine ≥ 0.8), which would inflate any reported score.

**Method.** Messages are grouped with union-find when either (a) their text matches once digits, URLs and amounts are masked, or (b) their char-3–5-gram TF-IDF cosine is ≥ 0.8. The groups go into `StratifiedGroupKFold(20, seed=42)`: 14 folds for train, 3 for val, 3 for test. The script asserts that no group spans two splits.

| split | rows | spam | spam ratio |
|---|---:|---:|---:|
| train | 3,610 | 450 | 12.5% |
| val | 774 | 96 | 12.4% |
| test | 774 | 96 | 12.4% |

There are 4,966 groups, of which 135 have more than one member (327 rows), and the largest has 10. Residual similarity to train, measured with TF-IDF fit on the full corpus as the script does:

| | cosine ≥ 0.8 | cosine ≥ 0.7 |
|---|---:|---:|
| val | 0 | 21 |
| test | 0 (was 22 spam before grouping) | 22 |

With TF-IDF fit on train alone, 4 test rows cross 0.8, which are borderline pairs. The 0.7 band is the honest remaining overlap. If Phase 2 sees a large gap between val and OOD scores, rerun with `--sim 0.7`. File hashes are in `data/processed/manifest.json`.

### ⚠️ Known label shortcut: anonymization placeholders
223 rows contain `<#>`, `<DECIMAL>`, `<TIME>`, `<URL>` or `<EMAIL>`, and **all 223 are ham**. The single `<UKP>` row is spam. These tokens record how one source sub-corpus was anonymized; they say nothing about content. A model can learn "contains `<#>` → ham", so **mask or strip these tokens before training** — done in Phase 2 by `src/sentinel/preprocess.py`, which maps each placeholder *and* the real value it replaced to one shared token (`<#>` and `42` both become `num`). A placeholder-only token such as `<num>` would keep the shortcut. The splits keep them untouched so that this stays a training-time choice.

**Rule:** `test.csv` is for final reporting only. (In Phase 2 it was evaluated twice; see `phase2_classifier.md` §2.) Use `val.csv` for model selection and threshold tuning.

## 3. Hugging Face survey

### Models
| Model | Params | Notes |
|---|---:|---|
| `mrm8488/bert-tiny-finetuned-sms-spam-detection` | 4.4M | 3.2M downloads, the most-used SMS spam model. **Trained on sms_spam.** |
| `mariagrandury/roberta-base-…` / `distilbert-base-uncased-…-sms-spam-detection` | 125M / 66M | **Trained on sms_spam.** |
| `hari-krishna-ai/sms-spam-minilm-l6` | 22.7M | sms_spam + india-spam-sms; has ONNX/transformers.js exports. **Trained on sms_spam.** |
| `hamadurrehman62/sms-scam-distilroberta`, `bthomas279/scam-detector` | ~82M | **Trained on sms_spam** (plus phishing data). |
| `Horizon-Labs/phishing-scam-detector-base` | 307M | mmBERT (multilingual ModernBERT), covers phishing, smishing and scams in about 35 languages, Apache-2.0. Training data not stated, and it is tagged spam-detection and smishing. **Assume contaminated until verified.** |
| `cybersectony/phishing-email-detection-distilbert_v2.4.1` | 66M | Email phishing (312K downloads). Different domain, useful only as a feature or transfer source. |
| `DaniilOr/multilingual_persuasion_techniques`, `jrc-ai/emm-persuasion-techniques` | DeBERTa / XLM-R | Persuasion-technique classifiers from news propaganda (SemEval-2023 Task 3 lineage). Relevant to the *manipulation-category* goal, but the domain is far from SMS. |

> ⚠️ **Contamination.** Every model marked **Trained on sms_spam** saw some version of this corpus, very likely including our test rows. Their scores on our test split are **not** valid baselines. Use them only on the OOD sets below, if at all.

**Clean baselines for Phase 2:**
1. TF-IDF (word plus char n-grams) with logistic regression: fast, interpretable, and a strong baseline on this corpus.
2. Fine-tune a base encoder that has not seen this data: `distilbert-base-uncased`, `microsoft/MiniLM-L12-H384-uncased`, or `answerdotai/ModernBERT-base`.
3. Optionally, zero-shot an instruction LLM on the manipulation categories, to compare against the weak labels.

### Datasets (for out-of-distribution evaluation; do **not** merge into our splits)
| Dataset | Size | Use |
|---|---:|---|
| `jngb-labs/sms-spam` | 5,159 | Already-deduplicated copy of the same corpus. Useful only as a cross-check. |
| `CloveAI/india-spam-sms` | 20K | Indian SMS spam, MIT. A domain-shift test (2011 UK to modern Indian SMS). |
| `BothBosu/scam-dialogue` | 1.6K | Synthetic phone dialogues. **The only scam-type labels found**: scam types `ssn`, `refund`, `reward`, `support`, and non-scam types `delivery`, `insurance`, `telemarketing`, `wrong` (160 each). |
| `alusci/sms-otp-spam-dataset` | 10K | Synthetic OTP-style SMS. |
| `zefang-liu/phishing-email-dataset`, `ealvaradob/phishing-dataset` | 18K / 77K | Email and URL phishing. Different modality. |
| `dbarbedillo/SMS_Spam_Multilingual_Collection_Dataset` | ~5.5K × ~30 langs | Machine-translated copies of *this* corpus. Same leakage risk. |

## 4. Manipulation categories

**The corpus contains no category labels.** It only says ham or spam, so every category label below is something we create. Currently that is keyword weak-labeling (`src/weak_labels.py`), which serves as a seed for manual or LLM-assisted annotation in Phase 2.

The taxonomy is **multi-label**, since a message usually uses several levers at once. It draws on Cialdini's principles (scarcity, authority, reciprocity, liking) and on the scam types in `BothBosu/scam-dialogue`.

| Category | Lever exploited | Example (train) |
|---|---|---|
| `urgency` | Scarcity and time pressure | "Valid 12hrs only", "Final Chance!", "call … NOW" |
| `reward_lure` | Greed and reciprocity | "You have WON a guaranteed £1000 cash" |
| `authority_impersonation` | Trust in institutions | "As a valued Vodafone customer…", "Customer service announcement… delivery" |
| `fear_threat` | Loss aversion, fear of missing something | "We are trying to contact U", "final notice to collect", "still unclaimed" |
| `callback_cta` | Action funnel (premium-rate 09… numbers, short codes, links) | "Call 09061701461", "txt MUSIC to 87066" |
| `subscription_trap` | Hidden cost and obfuscation | "150p/msg", "£3 per week… send STOP" |
| `social_romance_lure` | Curiosity and loneliness | "Someone has contacted our dating service… they fancy you" |

### Weak-label prevalence (train only, n = 450 spam / 3,160 ham)
| category | spam % | ham % | lift | rough precision¹ |
|---|---:|---:|---:|---|
| urgency | 22.7 | 0.5 | 42× | high (~12/12) |
| reward_lure | 55.3 | 2.3 | 24× | high (~12/12) |
| authority_impersonation | 6.2 | 0.0 | ~197× | medium (~9/12; stock pump-and-dump and a prepaid-refill ham slip through) |
| fear_threat | 4.9 | 0.0 | — | low as *threat*: hits are missed-contact pressure, not threats |
| callback_cta | 74.2 | 0.2 | 335× | high (~12/12) |
| subscription_trap | 45.1 | 0.2 | 238× | high (~11/12) |
| social_romance_lure | 10.2 | 0.4 | 23× | medium (~8/12; affectionate ham like "hey sexy" matches) |

At least one category fires on 92.4% of spam and 3.6% of ham. Spam that matches averages 2.19 categories.

¹ From reading 12 random hits per category. This is indicative only. A proper precision and recall estimate needs a hand-labeled sample, planned for Phase 2.

### Findings that should shape the next phases
- **Callback and subscription mechanics dominate.** They are the strongest signals, but they are surface patterns (phone numbers, pricing strings) specific to 2011 UK premium SMS. A model that learns "09 + 9 digits = spam" will not generalize to modern smishing, which uses URLs, parcel-delivery lures, bank or OTP impersonation, and WhatsApp-style "Hi mum" scams.
- **The modern categories are nearly missing.** Fear/threat and authority impersonation, the main levers in today's smishing, are rare here: under 7% of spam each, and real threats are almost absent. Detecting them will need OOD data (`CloveAI/india-spam-sms`, `BothBosu/scam-dialogue`, `alusci/sms-otp-spam-dataset`) or synthetic augmentation.
- **Ham also uses manipulation vocabulary.** Friends write "urgent", "free" and "win" too. The lift column is the useful measure; raw keyword presence is not.
- **Open decision:** keep the category task multi-label with these 7 categories, or merge `fear_threat` into `urgency` given how little data it has. Decide after hand-labeling.

## 5. Phase 2 handoff checklist
- [ ] Hand-label about 300 train spam (plus about 100 ham) for the 7 categories to measure weak-label precision and recall
- [x] Mask the anonymization placeholders (done in `preprocess.py`; see phase2 doc)
- [ ] TF-IDF+LR binary baseline, tuned on val
- [ ] Fine-tune a non-contaminated encoder
- [ ] OOD evaluation on `CloveAI/india-spam-sms`
