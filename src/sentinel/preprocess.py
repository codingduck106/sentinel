"""Text normalization shared by training and inference.

Key goal: the corpus anonymization placeholders (`<#>`, `<DECIMAL>`, `<TIME>`, ...) occur
only in ham. If they survive (or map to a token only they produce) the model learns
"placeholder -> ham". So placeholders AND the real-world strings they stand for are
mapped to the *same* tokens:

    <#>, <DECIMAL>, 42, 3.5      -> num
    <URL>, http://..., www.x.com -> urltok
    <EMAIL>, a@b.com             -> emailtok
    <TIME>, 10:30                -> timetok
    <UKP>2000, £2000, $350       -> moneytok
    phone numbers, short codes   -> num

Phone numbers and short codes deliberately do NOT get their own token. The ham
sub-corpus anonymized every number as <#>, so in training *any* long digit string
is ~100% spam. A dedicated token learned that artifact and flagged OTPs, order IDs
and bank alerts as spam (OOD India-SMS ROC-AUC 0.39 -> 0.79 after collapsing;
val PR-AUC change -0.002). The phone regex still runs first so that
"0800 123 4567" becomes a single `num`, not three.

Tokens are plain words (no angle brackets) so word and char n-grams treat them uniformly.
"""
from __future__ import annotations

import re
import unicodedata

_SUBS: list[tuple[re.Pattern, str]] = [
    # corpus placeholders first
    (re.compile(r"<UKP>\s?[\d,.]*", re.I), " moneytok "),
    (re.compile(r"<(#|DECIMAL)>", re.I), " num "),
    (re.compile(r"<URL>", re.I), " urltok "),
    (re.compile(r"<EMAIL>", re.I), " emailtok "),
    (re.compile(r"<TIME>", re.I), " timetok "),
    # real-world equivalents
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), " emailtok "),
    (re.compile(r"(https?://|www\.)\S+|\b[\w-]+\.(com|co\.uk|net|org|biz|info|ly)(/\S*)?\b", re.I), " urltok "),
    (re.compile(r"[£$€]\s?\d[\d,]*(\.\d+)?|\b\d[\d,]*(\.\d+)?\s?(pounds|gbp|usd|dollars)\b", re.I), " moneytok "),
    (re.compile(r"\b\d{1,2}[:.]\d{2}\s?(am|pm)?\b|\b\d{1,2}\s?(am|pm)\b", re.I), " timetok "),
    (re.compile(r"(\+?44\s?|\b0)[789]\d{2}\s?\d{3}\s?\d{3,5}\b"), " num "),
    (re.compile(r"\d+(\.\d+)?"), " num "),
]

TOKENS = ("num", "urltok", "emailtok", "timetok", "moneytok")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text))
    for rx, rep in _SUBS:
        text = rx.sub(rep, text)
    return re.sub(r"\s+", " ", text).strip().lower()


def normalize_many(texts) -> list[str]:
    """Vectorized form for sklearn's FunctionTransformer."""
    return [normalize(t) for t in texts]
