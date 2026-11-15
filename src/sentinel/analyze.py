"""Top-level entry: analyze(text) -> scam probability, spam/legit label, manipulation tactics.

CLI:  python -m sentinel.analyze "URGENT! Your account is suspended, call 0800..."
      echo "msg" | python -m sentinel.analyze
"""
from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

from sentinel.classifier import DEFAULT_MODEL, SpamClassifier
from sentinel.tactics import detect_dict


@lru_cache(maxsize=1)
def _model(path: str = str(DEFAULT_MODEL)) -> SpamClassifier:
    return SpamClassifier.load(Path(path))


def analyze(text: str, model: SpamClassifier | None = None) -> dict:
    clf = model or _model()
    p = float(clf.proba([text])[0])
    tactics = detect_dict(text)
    return {
        "text": text,
        "scam_probability": round(p, 4),          # P(spam) from TF-IDF + LR
        "label": "spam" if p >= clf.threshold else "legitimate",
        "threshold": round(clf.threshold, 4),
        "tactics": tactics,                        # independent rule-based component
        "tactics_detected": [k for k, v in tactics.items() if v["detected"]],
    }


def main() -> None:
    text = " ".join(sys.argv[1:]) or sys.stdin.read()
    print(json.dumps(analyze(text.strip()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
