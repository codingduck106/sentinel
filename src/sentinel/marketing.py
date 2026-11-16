"""Conservative detection of legitimate-looking promotional SMS.

The legacy spam model includes ordinary marketing in its spam class. This
detector only provides context for risk presentation; it never changes the
classifier probability or label.
"""
from __future__ import annotations

import re


_OPT_OUT = re.compile(
    r"\b(?:txt|text)\s+(?:help|stop)\b"
    r"|\bhelp\s+for\s+help\b"
    r"|\bstop\s+to\s+(?:cancel|end|unsubscribe)\b"
    r"|\bunsubscribe\b"
    r"|\bmsg\s*&?\s*data\s*rate(?:s)?\s*may\s*apply\b",
    re.I,
)
_COMMERCIAL = re.compile(
    r"\b(?:deal(?:s)?|offer(?:s)?|promo(?:tion)?s?|shop|sale|price|games?|"
    r"trade[- ]?in|qualifying|discount|stores?|mobile|phone|5g|on us|"
    r"bring the crew|half[- ]price)\b",
    re.I,
)
_NON_MARKETING_TACTICS = {"fear", "authority_impersonation", "reward"}


def is_likely_marketing(text: str, tactics_detected: list[str]) -> bool:
    """Return true only for opt-out-enabled commercial wording without scam cues."""
    return (
        not _NON_MARKETING_TACTICS.intersection(tactics_detected)
        and bool(_OPT_OUT.search(text))
        and bool(_COMMERCIAL.search(text))
    )
