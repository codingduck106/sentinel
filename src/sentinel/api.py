"""HTTP API: User input -> analyze() -> JSON for the results dashboard.

Run locally:  uvicorn sentinel.api:app --reload --port 8000
"""
from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field, field_validator

from sentinel.analyze import analyze
from sentinel.settings import env
from sentinel.explain import GENERAL_ADVICE, TACTIC_INFO, VERDICTS, risk_level, risk_score
from sentinel.tactics import TACTICS

MAX_CHARS = 2000  # code points; the frontend counts the same way ([...text].length)

# Every detector needs plain-language copy, or every request would fail with a KeyError.
assert set(TACTICS) == set(TACTIC_INFO), f"tactics/explain mismatch: {set(TACTICS) ^ set(TACTIC_INFO)}"

# Interactive docs are off unless explicitly enabled (e.g. locally): SENTINEL_ENABLE_DOCS=1
_docs = env("ENABLE_DOCS") == "1"
app = FastAPI(
    title="Veritas API", version="0.3.0",
    docs_url="/api/docs" if _docs else None, redoc_url=None,
    openapi_url="/api/openapi.json" if _docs else None,
)

# ---- Hardening: bounded bodies, generic errors, nothing echoed back ----
MAX_BODY_BYTES = 16_384  # a 2,000-character message is < 8 KB even as 4-byte UTF-8 + JSON


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    """Reject oversized bodies before they are read or parsed."""
    length = request.headers.get("content-length")
    if length is not None:
        try:
            too_big = int(length) > MAX_BODY_BYTES
        except ValueError:
            return JSONResponse({"error": "Invalid request."}, status_code=400)
        if too_big:
            return JSONResponse({"error": "Message too long."}, status_code=413)
    elif request.method == "POST":
        return JSONResponse({"error": "Invalid request."}, status_code=411)  # no chunked/unknown-length bodies
    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
    # FastAPI's default body echoes the user's input and pydantic internals; return a fixed message instead.
    return JSONResponse({"error": f"Paste a message between 1 and {MAX_CHARS} characters."}, status_code=422)


@app.exception_handler(StarletteHTTPException)
async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse({"error": "Not found." if exc.status_code == 404 else "Request not allowed."}, status_code=exc.status_code)


@app.exception_handler(Exception)
async def unexpected_error(_: Request, __: Exception) -> JSONResponse:
    # No stack trace, exception text or message content in the response.
    return JSONResponse({"error": "Veritas couldn't check this message right now."}, status_code=500)


# The frontend calls the API same-origin (Vercel services; Next dev proxy locally), so CORS is
# closed by default. Allow-list other origins only if you really need them: SENTINEL_CORS_ORIGINS=a,b
_origins = [o.strip() for o in (env("CORS_ORIGINS") or "").split(",") if o.strip()]
if _origins:
    app.add_middleware(CORSMiddleware, allow_origins=_origins, allow_methods=["POST", "GET"], allow_headers=["content-type"])


class AnalyzeRequest(BaseModel):
    text: str = Field(..., max_length=MAX_CHARS)

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Paste the text message you received.")
        return v


class Evidence(BaseModel):
    cue: str
    text: str
    start: int
    end: int


class Tactic(BaseModel):
    id: str
    name: str
    detected: bool
    score: float
    what: str
    advice: str
    evidence: list[Evidence]


class AnalyzeResponse(BaseModel):
    text: str
    verdict: str
    risk_level: str
    risk_score: float
    scam_probability: float
    classifier_label: str
    tactics: list[Tactic]
    tactics_detected: list[str]
    advice: str


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# ---- Opt-in AI context (informational only; cannot change the risk rating) ----
class ContextualRequest(AnalyzeRequest):
    # The browser sends consent=true only after the user ticks the disclosure checkbox.
    consent: bool


@app.post("/api/contextual")
def contextual_endpoint(req: ContextualRequest) -> JSONResponse:
    from sentinel.contextual import analyze_context  # lazy: keeps /api/analyze free of the LLM dependency

    if req.consent is not True:
        return JSONResponse({"error": "Turn on the AI explanation to use this."}, status_code=400)
    return JSONResponse(analyze_context(req.text), headers={"Cache-Control": "no-store"})


def _utf16_offsets(text: str):
    """Map Python code-point indices to UTF-16 code-unit indices (what JS string indexing uses).

    Without this, every highlight after an emoji or other astral character lands in the wrong place.
    """
    table, pos = [0], 0
    for ch in text:
        pos += 2 if ord(ch) > 0xFFFF else 1
        table.append(pos)
    return lambda i: table[i]


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze_endpoint(req: AnalyzeRequest) -> AnalyzeResponse:
    r = analyze(req.text)
    js = _utf16_offsets(req.text)
    tactics = [
        Tactic(
            id=k, detected=v["detected"], score=v["score"], **TACTIC_INFO[k],
            evidence=[{**e, "start": js(e["start"]), "end": js(e["end"])} for e in v["evidence"]],
        )
        for k, v in r["tactics"].items()
    ]
    level = risk_level(r["scam_probability"], r["label"] == "spam", len(r["tactics_detected"]))
    return AnalyzeResponse(
        text=req.text,
        verdict=VERDICTS[level],
        risk_level=level,
        risk_score=risk_score(r["scam_probability"], [t.score for t in tactics if t.detected]),
        scam_probability=r["scam_probability"],
        classifier_label=r["label"],
        tactics=tactics,
        tactics_detected=r["tactics_detected"],
        advice=GENERAL_ADVICE,
    )
