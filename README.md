# Veritas

**Live:** https://veritas-nine-gamma.vercel.app

Paste a suspicious text message. Veritas tells you, in plain language, whether it looks like a scam, highlights the exact words trying to rush, scare or bribe you, and says what to do next.

## How it works: a hybrid, not just a spam classifier

```
                          USER MESSAGE
                               |
            +------------------+-------------------+
            |                                      |
   TEXT PREPROCESSING                              |  (original text, so evidence
   numbers/links/amounts -> tokens                 |   shows the real words)
            |                                      |
      ML CLASSIFIER                         TACTIC DETECTOR
   TF-IDF + logistic regression       rules: urgency, fear, authority,
   (learned from 2011 UK spam)          too-good-to-be-true reward
            |                                      |
       SPAM SCORE                   DETECTED TACTICS + EXACT PHRASES
            |                                      |
            +------------------+-------------------+
                               |
                          RISK ENGINE
         High   = spam score + >= 1 tactic,  or >= 2 tactics
         Medium = spam score alone, or 1 tactic   (two signals for High)
         Low    = neither
                               |
              +----------------+----------------+
              |                |                |
           VERDICT        EXPLANATION         ACTION
       "This looks     highlighted words,   "Don't tap the link.
        like a scam"   one card per tactic   Call your bank on the
                                             number on your card."
              |                |                |
              +----------------+----------------+
                               |
                         RESULTS PAGE
```

- **Why two paths:** the classifier is strong on the spam it was trained on but weak on modern scams. The tactic detector carries over to new data better and explains itself. See the [study](docs/generalization_study.md).
- **Code:**
  - `src/veritas/preprocess.py`: preprocessing
  - `classifier.py`: classifier
  - `tactics.py`: tactic detector
  - `explain.py`: risk engine and explanation text
  - `api.py`: the endpoint
  - `web/`: results page
- **Deployment:** one Vercel project, where `/api/*` goes to Python (FastAPI) and everything else goes to Next.js.


## Run locally
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e . -r requirements-dev.txt
uvicorn veritas.api:app --port 8000 --app-dir src     # API (set VERITAS_ENABLE_DOCS=1 for /api/docs)
cd web && npm install && npm run dev                  # http://localhost:3000 (proxies /api to :8000)
```

## Data & model
```bash
python src/download_data.py && python src/prepare_data.py   # Kaggle SMS Spam Collection → leakage-safe splits
python src/train.py                                         # fit + select on val → models/spam_lr.joblib
python src/eval_ood.py                                      # out-of-distribution report
```
The research and evaluation write-ups are [`docs/phase1_research.md`](docs/phase1_research.md) and [`docs/phase2_classifier.md`](docs/phase2_classifier.md).

## Research finding: does a traditional spam detector generalize?
Full write-up with methods and limitations: [`docs/generalization_study.md`](docs/generalization_study.md).

| Experiment | Result (95% CI) |
|---|---|
| Historical SMS classification (2011 UK validation, 96 spam / 774) | F1 = 0.92 (0.87–0.96) |
| Same classifier on modern-style Indian SMS (5,558 scam from 41 templates; 13,672 legitimate) | ROC-AUC = 0.79 (0.66–0.91) |
| Modern scams detected by "≥ 2 manipulation tactics" | 40.0% (21–60%) |
| Legitimate messages flagged by "≥ 2 tactics" | 1 of 13,672 observed (95% upper bound 0.31% by template) |

- **Dataset:** the modern set is undocumented and appears **template-generated (synthetic)**.
- **Tuning:** some of its numbers informed design fixes.
- **What "1 observed" means:** it is an observation on that dataset, not a general false-positive rate.

- **Risk rule — two signals for High:** (classifier says spam AND ≥ 1 pressure tactic) OR ≥ 2 tactics. The classifier alone gives Medium at most, because out of domain it is confidently wrong on legitimate delivery and bank texts. This cut legitimate messages rated High from 12–37% to 1–3% on modern Indian SMS. The cost: fewer scams reach High (2011 validation 87.5% → 41%, Indian holdout 74% → 48%), though none drop to Low. Details: [`docs/false_positives.md`](docs/false_positives.md).
- **⚠️ Remaining weakness:** 28–57% of legitimate modern transactional SMS still get **Medium** ("This could be a scam") from the classifier alone. The fix is retraining on modern data.

## Optional AI explanation (`/api/contextual`)
An **opt-in**, **informational-only** third layer. Ticking "Also get an AI explanation" sends the message to **Claude Haiku 5.5** (Anthropic), which explains implicit manipulation and requests for sensitive information. The classifier, the tactic rules and the risk rating are untouched: the endpoint returns no risk fields, and the UI labels the card "doesn't change the risk rating above".

- **Privacy:**
  - **Off by default:** the browser sends `consent: true` only after the box is ticked, and the server rejects requests without it.
  - **Redaction:** recognized digit sequences, phone/account-like numbers, email addresses, and labeled PIN/OTP/CVV codes are masked before sending.
    Names, postal addresses, link domains, and other words are not removed; unlabeled short numbers may remain; link domains are kept as evidence.
  - **No storage:** nothing is stored, and the disclosure names Anthropic and links its privacy policy.
- **Strict validation:**
  - **Schema:** structured output, then Pydantic checks types, enums, length limits and that there are no extra fields. Invalid output is **rejected**, not repaired.
  - **Quotes:** any quote not found word for word in the message is dropped.
  - **Rendering:** AI text is rendered as plain text, never HTML.
- **Failures degrade to a note:** disabled, daily limit, timeout (8 s), busy/429/5xx, refusal or invalid output all return `{"status": "unavailable", "reason": ...}`. The main result is unaffected.
- **Daily spending cap:** each call reserves its worst-case cost before it's made and settles the actual cost after. ⚠️ The cap is **per server instance**, so on Vercel several warm instances each have their own. It is not a hard global financial ceiling. Set a workspace-level monthly spend limit in the [Claude Console](https://platform.claude.com/settings/spend-limits) as the global backstop.
- **Cost (measured):** about $0.0003 per check, median latency about 3 s (`docs/` benchmark notes).

Configuration (server-side environment variables; the key never reaches the browser):

| variable | default | |
|---|---|---|
| `VERITAS_LLM_ENABLED` | off | `1` to enable (also requires the key) |
| `ANTHROPIC_API_KEY` | none | workspace-scoped API key |
| `ANTHROPIC_WORKSPACE_ID` | none | only for keys that need the `anthropic-workspace-id` header |
| `VERITAS_LLM_MODEL` | `claude-haiku-5-5` | |
| `VERITAS_LLM_EFFORT` | `low` | thinking is off |
| `VERITAS_LLM_TIMEOUT_S` | `8` | |
| `VERITAS_LLM_DAILY_BUDGET_USD` | `1.00` | per instance |

Local: put the key in `.env.anthropic` (git- and Vercel-ignored), then `set -a; . ./.env.anthropic; set +a; VERITAS_LLM_ENABLED=1 uvicorn veritas.api:app --app-dir src`.

## Tests
```bash
python -m pytest                                   # 89 tests: preprocessing, tactics, model, risk rule, API hardening, AI endpoint (mocked)
cd web && npx playwright test                      # 54 E2E tests (18 × desktop, Android, iPhone-size); AI endpoint mocked
E2E_BASE_URL=https://<deployment> npx playwright test   # against a deployed URL
```

## Security notes
All of the following were verified against the live production deployment on 2026-11-14.

- **Input limits:** more than 2,000 characters gives 422. Bodies over 16 KB are rejected with 413 before parsing; Vercel itself rejects anything over 4.5 MB with 413. Bodies without a declared length get 411.
- **Errors reveal nothing:**
  - **Generic bodies:** every error is a fixed `{"error": "..."}` (422, 404, 405, 413, 500). FastAPI's default 422, which echoed the user's text and pydantic internals, is replaced.
  - **No stack traces:** nothing internal is ever returned.
  - **Docs off:** `/api/docs` and `/api/openapi.json` return 404 unless `VERITAS_ENABLE_DOCS=1`.
- **No message logging:**
  - **Code:** the served code has no logging or print calls.
  - **Canary test:** a unique string was sent to production, then the runtime logs were searched; 0 hits.
  - **Vercel request logs:** they record only method and path.
- **XSS:** user text is only ever rendered as text, never as HTML; an end-to-end test covers this.
- **Headers:** CSP, `nosniff`, `X-Frame-Options: DENY`, Referrer-Policy and Permissions-Policy. API responses are `no-store`. CORS is closed by default.
- **Rate limit:** the Vercel Firewall rule "Rate limit message checks" covers `POST /api/analyze`, 30 per minute per IP, returning 429. The UI turns 429 into "Too many checks… wait a minute". The current Vercel plan does not support a separate firewall rate limit for `POST /api/contextual`; its application budget is per instance, not a global spending ceiling.
  - **Publishing:** the CLI only publishes it with a person's confirmation (`vercel firewall publish`).
  - **Testing note:** once it's live, running the full Playwright suite against production from one IP sends over 30 checks a minute and will trip it. Run one project at a time (`--project desktop`) or wait between runs.
- **Model file:** `models/spam_lr.joblib` is a pickle, so only load model files you built yourself.
- **Secrets:** `.env*` is excluded from the upload and from the function bundle.
- **Mobile:** tested at Android (Pixel 7) and iPhone 13 sizes with touch, using Chromium. Real Safari/WebKit couldn't be installed here, so check it on an actual iPhone.

## Design
`.superdesign/design-system.md`: cool mist paper, slate ink, Bricolage Grotesque with Atkinson Hyperlegible, and one highlighter colour per tactic. The landing page was designed on the Superdesign canvas; the check and results screens were built directly in code from the approved plan.
