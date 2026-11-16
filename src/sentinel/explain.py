"""Overall risk level + plain-language explanations for the UI.

Risk rule "two signals for High" (docs/false_positives.md, src/eval_risk_rules.py):
    high   : (classifier says spam AND >= 1 tactic) OR >= 2 tactics
    medium : classifier says spam alone, OR exactly 1 tactic, OR scam_probability >= 0.2
    low    : otherwise
Why: the classifier alone was enough for High, and out of domain it is confidently wrong on
legitimate delivery/bank texts. Requiring two signals cut legitimate->High from 36.6% to 2.9%
(India dev) / 12.2% to 2.6% (India holdout). Cost: fewer scams reach High (they land on Medium,
never Low): 2011 val 87.5% -> 41%, India holdout 74% -> 30% (pre cue-fix numbers).
The two signals are not fully independent (words like "claim", "urgent" feed both).
The UI must never present "low" as "safe".
"""
from __future__ import annotations

MEDIUM_PROBABILITY = 0.2

TACTIC_INFO: dict[str, dict[str, str]] = {
    "urgency": {
        "name": "Urgency",
        "what": "Rushes you so you act before you stop to think or check.",
        "advice": "Slow down. Real organisations give you time. Nothing you have to do in the next hour is worth skipping a check.",
    },
    "fear": {
        "name": "Fear",
        "what": "Threatens a loss or punishment — a blocked account, a fine, legal trouble — to make you panic.",
        "advice": "Don't use any number or link in the text. Contact the company yourself using a number you already trust, like the one on your card.",
    },
    "authority_impersonation": {
        "name": "Pretending to be official",
        "what": "Claims to be a bank, delivery company, phone network or government body so you'll trust it.",
        "advice": "Anyone can type a company's name into a text. Check by logging in through the official app or website, not the text.",
    },
    "reward": {
        "name": "Too-good-to-be-true reward",
        "what": "Dangles a prize, refund or free gift to get you to call, click or pay a 'small fee'.",
        "advice": "If you didn't enter, you didn't win. Never pay or share details to receive a prize or refund.",
    },
}

VERDICTS = {
    "high": "This looks like a scam",
    "medium": "This could be a scam",
    "low": "This looks like a normal message",
}

GENERAL_ADVICE = "If in doubt, contact the company using a number you already trust."


def risk_level(scam_probability: float, is_spam: bool, n_tactics: int, is_marketing: bool = False) -> str:
    if is_marketing and n_tactics <= 1:
        return "low"
    if (is_spam and n_tactics >= 1) or n_tactics >= 2:
        return "high"
    if is_spam or n_tactics == 1 or scam_probability >= MEDIUM_PROBABILITY:
        return "medium"
    return "low"


def risk_score(scam_probability: float, tactic_scores: list[float], is_marketing: bool = False) -> float:
    """0–1 position on the UI's risk scale. Display only — the level comes from risk_level().

    Pass only DETECTED tactics' scores, or sub-threshold cues can push the marker toward a
    level that risk_level() did not assign.
    """
    strongest = sorted(tactic_scores, reverse=True)
    tactic_part = min(1.0, sum(strongest[:2]) / 1.5)
    classifier_part = min(scam_probability, 0.2) if is_marketing else scam_probability
    return round(max(classifier_part, tactic_part), 3)
