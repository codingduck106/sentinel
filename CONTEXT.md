# CONTEXT.md — Veritas project handoff

_Last updated 2026-11-15 (AI layer deployed and verified). This is a compressed summary of the whole development history, written so another coding assistant can continue the work._

## 1. What Veritas is
A public web app. You paste a suspicious SMS and get:
- a plain-language verdict (Low / Medium / High risk);
- the exact manipulative words, highlighted by tactic;
- advice on what to do.

**Live (production):** https://veritas-nine-gamma.vercel.app. Vercel project `veritas`, team `codingduck106s-projects`.

## 2. Architecture
```
Browser (Next.js 16, web/) ── POST /api/analyze ──► FastAPI (main.py → src/veritas/api.py)
                                                    ├─ classifier.py  normalize → TF-IDF (word 1–2 + char 3–5) → LogisticRegression → P(spam)
                                                    ├─ tactics.py     rule-based: urgency, fear, authority_impersonation, reward (+ exact evidence spans)
                                                    └─ explain.py     risk engine + plain-language copy
                           ── POST /api/contextual (OPT-IN, LIVE) ──► contextual.py → Claude Haiku 5.5 (informational only)
```
- **Deployment:** one Vercel project using **services** (`vercel.json`). The `frontend` service is `web/`. The `backend` service has root `.` and entrypoint `main:app`. `/api/*` goes to the backend; everything else goes to the frontend.
- **Risk rule** (`explain.py`, "two signals for High"):
  - **High** = (classifier says spam AND ≥ 1 tactic) OR ≥ 2 tactics.
  - **Medium** = classifier spam alone, OR 1 tactic, OR p ≥ 0.2.
  - **Low** = none of these.
  - Never present Low as "safe".

## 3. Key files
| path | role |
|---|---|
| `src/veritas/preprocess.py` | Normalization. Placeholders AND real values map to shared tokens (`num`, `urltok`, `emailtok`, `timetok`, `moneytok`). **Phone numbers and short codes must stay `num`**: separate tokens were an anonymization artifact that broke out-of-domain performance. |
| `src/veritas/classifier.py` | `build_pipeline`, `SpamClassifier` (joblib load = pickle: only load our own model) |
| `src/veritas/tactics.py` | Weighted regex cues; `score = min(1, Σweights)`, detected if score ≥ 0.5. Brand names that are common words (EE, UPS, Apple, …) only match when capitalized as the brand. |
| `src/veritas/explain.py` | `risk_level`, `risk_score` (detected tactics only), `TACTIC_INFO` copy |
| `src/veritas/api.py` | FastAPI routes and hardening (16 KB body cap, 413/411, generic error bodies, docs off unless `VERITAS_ENABLE_DOCS=1`, CORS closed unless `VERITAS_CORS_ORIGINS`). Converts evidence offsets to UTF-16 (emoji-safe). |
| `src/veritas/contextual.py` | Opt-in Claude layer (see §6) |
| `main.py` | Vercel Python entrypoint; sets `JOBLIB_MULTIPROCESSING=0` |
| `models/spam_lr.joblib` | Trained model: C=30, threshold 0.353 (chosen on val) |
| `src/prepare_data.py`, `src/train.py`, `src/eval_ood.py`, `src/eval_risk_rules.py`, `src/generalization_report.py` | Data prep, training and evaluation scripts |
| `web/src/app/page.tsx`, `web/src/app/check/CheckClient.tsx`, `web/src/components/*` | Landing page, check page, Results, RiskAssessment, AnnotatedMessage, ExplanationCard, ContextualCard |
| `web/src/lib/api.ts`, `web/src/lib/spans.ts` | API client; merges overlapping evidence spans |
| `docs/phase1_research.md`, `docs/phase2_classifier.md`, `docs/false_positives.md`, `docs/generalization_study.md` | Research write-ups (keep their caveats) |
| `.superdesign/design-system.md` | Design tokens and rules |
| `README.md` | User-facing docs, security notes, settings |

## 4. Run and test
```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -e . -r requirements-dev.txt
uvicorn veritas.api:app --port 8000 --app-dir src        # API
cd web && npm install && npm run dev                      # http://localhost:3000 (proxies /api → :8000 in dev)
python -m pytest                                          # 94 tests (Claude always mocked; includes tests/test_lockfile.py)
cd web && npx playwright test                             # 60 E2E (desktop, Pixel 7, iPhone-size via Chromium); AI endpoint mocked
E2E_BASE_URL=https://veritas-nine-gamma.vercel.app npx playwright test --project desktop   # against prod, one project at a time
```
- **Vercel CLI:** `vercel deploy --prod` from the repo root.
- **Local build:** `vercel build` needs `uv` on PATH (installed in `.venv`).

## 5. Data, model and results (keep these honest)
- **Data:** Kaggle `uciml/sms-spam-collection-dataset` (2011 UK).
  - Mojibake repaired, 414 exact duplicates removed, giving 5,158 messages.
  - Near-duplicate grouping (cosine ≥ 0.8 + template keys) before a `StratifiedGroupKFold` split of 70/15/15.
  - Files: `data/processed/`, with `manifest.json` holding hashes.
- **Test split rule:** `test.csv` has already been evaluated **twice**. Don't run `train.py --final-test` again without telling the user. **Val F1 ≈ 0.92 is the honest in-domain number.**
- **Results table** (`docs/generalization_study.md`):
  - Historical F1 0.92 (CI 0.87–0.96, val, 96 spam).
  - Modern-style Indian SMS ROC-AUC 0.79 (CI 0.66–0.91; 5,558 scams from only **41 templates**).
  - "≥ 2 tactics" catches 40% of scams (CI 21–60%), with **1** of 13,672 legitimate messages flagged.
- **Caveats to keep in any write-up:**
  - The Indian dataset (`CloveAI/india-spam-sms`) is undocumented and appears **synthetic/template-generated**.
  - Indian numbers are tuning numbers, because design decisions were made while looking at them.
- **Known weakness:** 28–57% of legitimate modern transactional SMS get **Medium** from the classifier alone. The fix is retraining on modern data.
- **Held-out sets:** `alusci/sms-otp-spam-dataset` (10 templates) and `BothBosu/scam-dialogue` (phone transcripts). OOD data lives in `data/ood/` (git-ignored).

## 6. LLM layer — `/api/contextual` (LIVE in production since 2026-11-15)
Requirements set by the user, which must be preserved:
- **Untouched components:** the existing classifier and rule engine stay as they are, and the LLM lives in its own endpoint.
- **Opt-in with disclosure:** the checkbox is unticked by default and the disclosure names Anthropic. The server requires `consent: true`.
- **Informational only:** the response has **no risk/verdict/probability fields**, and the AI can never change ratings. A test confirms `/api/analyze` output is unchanged.
- **Strict server-side validation:** Pydantic `AIReport` checks types, enums, length limits and that there are no extra fields. Invalid output is **rejected, not repaired**. Quotes not found exactly in the (redacted) message are dropped.
- **Redaction before sending:** recognized digit runs, phone/account-like numbers, emails and labeled PIN/OTP/CVV codes are masked **with the label kept** ("OTP 482913" → "OTP [number]", so the model still knows a code is being requested); names, postal addresses and other words are not masked; unlabeled short numbers may remain; link domains are kept.
- **Message encoding:** the redacted message is sent as JSON (`{"message": ...}`), not inside tags, so `</message>`-style break-outs can't inject instructions.
- **Graceful failure:** every failure returns `{"status":"unavailable","reason":...}`, with reason `disabled | daily_limit | timeout | busy | refused | invalid | error`. A missing `anthropic` package also returns `error` (the SDK is imported **before** budget is reserved).
- **Daily spending cap:** reserve worst-case cost, then settle. ⚠️ **It is per server instance**, so it is not a hard global financial ceiling; also set a workspace-level monthly spend limit in the Anthropic Console.
- **No paid fallbacks, and keys stay server-side.**

Model choice:
- **Model:** `claude-haiku-5-5` (cheapest current; Haiku 3.5 is retired), `effort: low`, `thinking: disabled`, `max_tokens` 1024, structured output via `output_config.format` json_schema. Length keywords are unsupported by the API, so they're stated in the prompt and enforced by Pydantic.
- **Measured (re-measured 2026-11-15 after the prompt/encoding/redaction changes):** 16/16 strict-valid live answers, 10/10 scams caught, bank and delivery notices clean, median 3.2 s, about $0.0003 per check. It flags the genuine "URGENT: card payment due" reminder (urgency/fear), which the rules already rate High anyway. Romance message tactic set varied between runs (7/8 repeatable).

Settings (env vars): `VERITAS_LLM_ENABLED=1`, `ANTHROPIC_API_KEY` (workspace-scoped; locally in `.env.anthropic`, which is git- and Vercel-ignored — **never print or commit it**), optional `ANTHROPIC_WORKSPACE_ID`, `VERITAS_LLM_MODEL`, `VERITAS_LLM_EFFORT`, `VERITAS_LLM_TIMEOUT_S` (8), `VERITAS_LLM_DAILY_BUDGET_USD` (1.00), and price overrides.

**Safeguards in place:**
- **Anthropic workspace spend limit:** set by the user in the Anthropic Console. This is the hard global cost ceiling. Workspace rate limits are also set there.
- **In-app daily budget:** `VERITAS_LLM_DAILY_BUDGET_USD`, per server instance only.
- **Vercel env vars (Production only, encrypted):** `ANTHROPIC_API_KEY`, `VERITAS_LLM_ENABLED`, `VERITAS_LLM_DAILY_BUDGET_USD`, `VERITAS_LLM_MODEL`, `VERITAS_LLM_EFFORT`, `VERITAS_LLM_TIMEOUT_S`.

**Open items (optional):**
1. **UX decision:** the AI card can contradict the rating. For example, the "Hi Mum" scam is rated Low by the rules while the AI explains it's a scam. The user hasn't decided whether to change this.
2. **Per-IP limit on `/api/contextual`:** Vercel Hobby allows only **1 rate-limit rule per project** (verified in Vercel docs), and it's used for `/api/analyze`. That **one rule can match both paths** (edit its path condition in the dashboard; the two endpoints then share 30/min/IP). For an exact per-IP limit plus a global budget across instances, the option is Upstash Redis from the Vercel Marketplace (atomic counters, keyed on Vercel's spoof-proof client IP via `vercel.functions.ip_address`), failing closed. Neither is done yet; the spend limit is the cost ceiling.

Alternatives investigated and rejected (don't re-investigate without reason):
- **OpenRouter `:free`:** 50 requests/day. NVIDIA-served free models are under NVIDIA trial terms that prohibit production use and train on inputs. `nemotron-3.5-lightning:free` lacks `response_format`; `nemotron-3-ultra-550b-a55b:free` scored best of the free models.
- **NVIDIA NIM trial:** no production use.
- **Hugging Face Inference Providers:** no free credits for free accounts.
- **Hugging Face ZeroGPU:** account not eligible.
- **Local llama.cpp on this laptop:** only about 3 GB of RAM free.
- **Oracle Always Free:** now 2 OCPU / 12 GB, and idle instances can be reclaimed.
- **DeepSeek:** no free endpoints.

## 7. Deployment and security state
- **Prod:** passes all E2E. Headers (CSP, nosniff, X-Frame-Options DENY, Referrer-Policy, Permissions-Policy) are set in `vercel.json`.
- **Verified on prod:** oversized bodies give 413, error bodies are generic, and no message text appears in the logs (canary test).
- **Firewall:** the rule "Rate limit message checks" (POST /api/analyze, 30/min/IP, 429) is **published and live**. Nothing in the firewall covers `/api/contextual` (see §6). The Vercel CLI refuses to publish firewall changes for agents, so the user publishes. Running the full prod E2E from one IP can trip the limit: use `--project desktop`.
- **Production deployment history (2026-11-14/15):**
  - `5e47794` → `rbduoqnk7`: AI shipped but crashed (`ModuleNotFoundError: anthropic`), because `uv.lock`, which Vercel installs from, lacked `anthropic`.
  - `d3ea7d7` → `d5snvs30u`: an `import anthropic` workaround in `main.py`. It was **rolled back** and then reverted in git.
  - `595c669` fixed `uv.lock`.
  - **Current production: `veritas-qbxstnwqb` (`dpl_443gk991P2MPaM4Dj6mkyfVdNqsD`)** = `595c669` plus the import, redaction and lockfile-test fixes, verified live (AI explanation working, 20/20 desktop E2E, no log errors), then **promoted**.
  - The rollback had turned off auto-promotion (`autoAssignCustomDomains: false`). `vercel promote` turned it back on.
- **Excluded files:** `vercel.json` `excludeFiles` keeps data, docs, tests, web and `.env*` out of the Python bundle (≤ 256 characters). `.vercelignore` excludes `.venv`, `data` and `.env*`.
- **Git:** local repo on `main`, **no remote**, so nothing has been pushed. Deploys are made from the CLI. No secrets are tracked (`.env*` is ignored). If the repo is ever published, note that the committed SMS dataset has unclear redistribution rights.
- **Account:** the Vercel account was advised to enable 2FA.

## 8. Conventions and gotchas
- **Process:**
  - Don't modify the classifier or rule engine without being asked.
  - Ask before deploying, publishing firewall rules, or spending money.
  - Report numbers honestly, with confidence intervals and caveats.
- **Frontend:**
  - Next.js 16 has breaking changes; read `web/node_modules/next/dist/docs/` before using unfamiliar APIs.
  - The design uses separate **wash** colours (highlighter) and **mark** colours (bars and dots, validated for colour-blind readers in light and dark mode), plus status colours kept distinct from the marks. Text never uses series colours. See `.superdesign/design-system.md`.
  - Use a `<mark>` reset (`background-color: transparent`), or the browser's yellow shows through the highlights.
- **Dependencies:** Vercel installs the Python backend from **`uv.lock`**, not from `pyproject.toml`. After changing dependencies, run `uv lock` and commit `uv.lock`. `tests/test_lockfile.py` fails if they drift.
- **Rollbacks:** after an instant rollback, new production deploys are **not** auto-assigned to the domain until `vercel promote <deployment-url>`. Check with `vercel api /v9/projects/veritas` (`autoAssignCustomDomains`).
- **Shell:** `pkill -f "pattern"` matches its own shell. Use a pattern like `"uvicorn veritas[.]api"`.
- **Superdesign:** the project canvas has only the landing draft (credits ran out). Other screens were built in code.
- **Scratch files are temporary:** the benchmark scripts and results were in a temporary scratch folder and may be gone. The key findings are recorded in this file and in `docs/`.
