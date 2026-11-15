# Do traditional SMS spam detectors generalize to modern social-engineering scams?

_Veritas generalization study, 2026-11-14. Reproduce: `python src/generalization_report.py`._

**Question.** A spam classifier trained on historical UK SMS (2011) looks excellent in-domain. How well does it carry over to modern-style scam messages from a different region and time? Does detecting *manipulation tactics* (urgency, fear, impersonation, reward) generalize better than learning spam vocabulary?

## Results

| Experiment | Data | Result (95% CI) |
|---|---|---|
| Historical SMS classification (TF-IDF + logistic regression) | 2011 UK validation split: 774 messages, **96 spam** | **F1 = 0.92** (0.87–0.96) |
| Same classifier on modern-style Indian SMS | 19,230 messages: **5,558 scam from 41 templates**, 13,672 legitimate | **ROC-AUC = 0.79** (0.66–0.91) |
| Modern scams detected by "≥ 2 manipulation tactics" (rule-based) | same 5,558 scam messages | **40.0%** (2,225 messages; 21–60%); ≥ half the messages caught in 20 of 41 scam templates |
| Legitimate messages flagged by "≥ 2 tactics" | same 13,672 legitimate messages (1,782 templates) | **1 observed** (0.007%). 95% upper bound 0.31% (template level) |

- **CIs for the modern dataset:** resampled by message template, not by message. Messages from one template aren't independent, so the real sample size is closer to **41 scam templates** than 5,558 messages.
- **Upper bound:** exact Clopper–Pearson bound over 1,782 templates. The bound over individual messages, 0.04%, is too optimistic for the same reason.
- **The one legitimate message flagged:** "URGENT: Your SBI credit card payment of INR 15000 is due tomorrow. Pay now to avoid late fees." It is genuine and does use urgency and fear. Tactic language describes *how* a message pushes you, not *who* sent it.

## What it shows
1. **A large in-domain to out-of-domain gap.**
   - **In-domain:** an F1 of 0.92 and a ROC-AUC of 0.98 on 2011 validation.
   - **Out of domain:** a ROC-AUC of only 0.79.
   - **The failure is specific.** The classifier learned the *surface form* of 2011 UK spam: premium-rate numbers, short codes, "txt", "claim", £ amounts. It flags modern *legitimate* transactional texts with links and order numbers (72% of legitimate delivery texts in one half of the data). And it misses scams that read like normal notices.
2. **Tactic detection transfers better than vocabulary, but covers only part of the threat.**
   - **Precise:** "≥ 2 tactics" almost never fires on legitimate messages, in either era (1 of 13,672 modern; 0 of 3,160 historical).
   - **Partial recall:** it catches only 40% of modern scams (21–60%).
   - **Misses:** scams that use no pressure language, such as fake-sale links, dating lures and "get rich quick".
3. **The two signals fail differently, so neither should decide alone.** This led the app's risk rule to require two signals for "High" ([`false_positives.md`](false_positives.md)).

## Limitations (read before citing any number)
- **The modern dataset is undocumented and appears synthetic.**
  - **Source:** `CloveAI/india-spam-sms` on Hugging Face (MIT license, 20,010 rows, 19,230 after removing duplicates). Its card describes no source, collection method or labelling process.
  - **Evidence it was generated:** it is generated from templates (1,823 templates, only 41 for scams), and it shows slot-filling artifacts: "Avl Bal INR *Natarajan*", "Bill amount: INR *Khare LLC*", "₹*HDFC* cashback".
  - **Labels:** presumably assigned by the generator's templates, not by human annotators.
  - **What this means:** the results measure generalization to *template-generated, modern-style Indian scam and notice texts*, not to real messages collected from phones. A real-world modern corpus is the obvious next step.
- **Few distinct scams.** 41 scam templates is the effective sample size, hence the wide intervals. One template more or less moves the detection rate by several points.
- **"1 observed" does not mean "almost never".**
  - It applies to *this* synthetic set, whose legitimate messages are mostly calm transactional notices.
  - Real legitimate traffic contains more urgent-sounding messages (payment reminders, school alerts, a friend saying "urgent, call me").
  - The 95% upper bound (0.31% of templates) is a bound for this dataset only. It is not a guarantee in general.
- **Different distributions, by design.** These are differences in kind, not just in sample:
  - **Era:** 2011 versus modern-style.
  - **Region:** UK versus India.
  - **Collection:** crowdsourced real messages versus apparently synthetic ones.
  - **Spam share:** 12.4% versus 28.9%.
  - **Currency and payments:** £ and premium-rate numbers versus ₹, UPI and URLs.
  - **Anonymization:** the 2011 legitimate messages had numbers masked as `<#>`, which the pipeline neutralizes.
- **Some modern numbers are tuning numbers, not clean holdout results.**
  - **Classifier:** the modern set motivated one preprocessing change. Phone numbers and short codes were collapsed into a generic number token, because the old tokens were an anonymization artifact; that change raised ROC-AUC from 0.39 to 0.79.
  - **Tactic rules:** the rules were fixed after reading misclassified modern messages. Examples include the inflections "expire" and "you are selected", and a bare "refund" no longer counting as a reward lure.
  - **No clean holdout remains:** no untouched modern holdout is left. A held-out pass done *before* the rule fixes is in [`false_positives.md`](false_positives.md) §D.
- **Historical figure:** F1 0.92 is on validation. The 2011 test split scored higher (F1 0.99), but it was evaluated twice during development and looks easier than validation, so validation is the figure to report.
- **Two small held-out checks, both synthetic:**
  - **OTP templates** (`alusci/sms-otp-spam-dataset`, 10 templates): 0 of 5 legitimate rated High; 3 of 5 scams rated High.
  - **Phone-scam dialogues** (`BothBosu/scam-dialogue`): the detectors find the tactic each scam type is built around, for example fear in 95% of SSN-threat calls ([`phase2_classifier.md`](phase2_classifier.md) §5).

## Next steps
1. **Real modern messages:** evaluate on SMS collected from real phones (for example user reports with consent, or a published modern corpus), with labels documented.
2. **Retraining:** retrain the classifier on modern data, keeping a held-out modern test set that no one looks at during development.
3. **Wider tactic coverage:** add fake-sale lures, dating and romance lures, lookalike URLs and money requests from "family", and measure them on that clean set.
