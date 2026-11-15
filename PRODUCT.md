# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Members of the public (global, English-speaking) who have just received a text message (SMS) that feels off and want to know, quickly and in plain language, whether it is a scam and what to do. They are often non-technical, sometimes anxious, and usually on a phone. They are not security professionals.

## Product Purpose
Sentinel checks a pasted text message and returns:
- a plain-language verdict: Low, Medium or High risk, never "safe";
- the exact words that are trying to rush, scare, impersonate or bribe the reader;
- concrete next steps.

Success means a person decides what to do in under a minute, avoids the scam if it is one, and isn't needlessly alarmed by a genuine message.

Sentinel is both a research-backed project being submitted now and a tool intended to keep running for real public users afterwards. Honesty about its limits is part of the product, not a disclaimer.

## Positioning
Sentinel is a hybrid. A spam classifier and a separate rule-based manipulation-tactic detector each read the message, and a risk rule needs two signals before it says "High".
- **Shows its evidence:** it highlights the exact manipulative phrases instead of only giving a score.
- **Optional AI explanation:** with the user's consent, an AI explanation (Claude) adds context. It is informational only and never changes the rating.
- **Honest about limits:** it is open about what it can't know, such as who actually sent a message.

## Operating Context
- **The scene:** someone receives a suspicious SMS (bank alert, parcel fee, prize, "Hi Mum, new number", one-time-code request), copies it, pastes it into Sentinel on their phone or laptop, and reads the result, often before deciding whether to tap a link, call back or reply.
- **Usage pattern:** one message at a time. There are no accounts, no history and no saved messages.

## Capabilities and Constraints
- **Main check:** `POST /api/analyze`, which needs no account. It runs a TF-IDF + logistic regression spam classifier trained on 2011 UK SMS, plus rule-based detection of urgency, fear, pretending to be official, and too-good-to-be-true rewards, with exact evidence spans.
- **Risk rule:** High = (spam-like wording AND ≥ 1 tactic) OR ≥ 2 tactics; Medium = one signal; Low = neither. Low is never presented as safe.
- **Optional AI explanation:** `POST /api/contextual` with Claude Haiku 5.5.
  - Off by default and opt-in, with explicit disclosure that the message goes to Anthropic.
  - Personal details are masked first.
  - Strictly validated output that cannot change the rating, with graceful failure.
- **Privacy:** Sentinel does not store messages. Input is limited to 2,000 characters.
- **Known weaknesses:**
  - The classifier is weak on modern transactional texts: 28–57% of legitimate bank and delivery messages get Medium from the classifier alone.
  - The rules miss scams with no pressure wording (fake sales, romance, "Hi Mum"). The optional AI explanation catches many of these.
- **Hosting:** Vercel Hobby plan, with a Next.js frontend and a FastAPI backend. The plan's firewall allows one rate-limit rule. AI spend is capped by an Anthropic workspace spend limit.
- **Open decision:** the user has chosen a global English-speaking audience, but some advice is UK-specific today (for example "forward it to 7726", £ examples). Region-neutral wording, or region-aware tips, is still to be decided.
- **Open decision:** the AI explanation can disagree with the rating (for example "This looks like a normal message" plus an AI card explaining a scam). How to present that disagreement hasn't been decided.

## Brand Commitments
- **Name:** Sentinel (renamed from Veritas on 2026-11-15). The wordmark is lowercase `sentinel_`.
- **Voice:** a level-headed friend who knows about scams. Plain verbs, sentence case, never alarmist and never cute.
- **Never says "safe" or "100% safe".**
- **Always offers a trustworthy fallback:** "If in doubt, contact the company using a number you already trust."
- **Required verdict wording:** "This looks like a scam" / "This could be a scam" / "This looks like a normal message".
- **AI-generated content** is always labelled as such and as informational.

## Evidence on Hand
- **Measured results:** historical SMS F1 0.92 (2011 UK validation set). Modern-style Indian SMS ROC-AUC 0.79 (wide CI, 41 scam templates; the dataset appears synthetic). "≥ 2 tactics" detects 40% of modern scams, with 1 of 13,672 legitimate messages flagged. Sources: `docs/generalization_study.md`, `docs/false_positives.md`, `docs/phase1_research.md`, `docs/phase2_classifier.md`.
- **AI explanation:** benchmark of 8 hand-written realistic messages: 10/10 scam runs caught, 16/16 schema-valid, median about 3 s, about $0.0003 per check.
- **Live product:** https://sentinel-scam-checker.vercel.app
- **Absent, so never fabricate:** user counts, testimonials, press, partnerships, accuracy claims beyond the documented measurements, and any certification.

## Product Principles
1. **Explain, don't just score.** Every judgment points to the exact words that caused it.
2. **Calm over alarm.** Help the person act wisely without inducing panic, and never imply certainty Sentinel doesn't have.
3. **Honest limits are a feature.** State what Sentinel can't know, and keep measured claims tied to their caveats.
4. **The person stays in control of their data.** Nothing is stored, and anything sent to a third party is opt-in and disclosed.
5. **Two signals before High.** No single signal, including the AI, decides alone.

## Accessibility & Inclusion
WCAG 2.2 AA is the required standard: contrast, full keyboard use, screen-reader labels for highlighted evidence, visible focus, reduced motion respected, and no information conveyed by colour alone. Plain language for a general, often anxious audience.
