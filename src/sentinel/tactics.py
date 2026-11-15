"""Manipulation-tactic detection — independent of the spam classifier.

Rule-based by necessity: the corpus has no tactic labels (see docs/phase1_research.md).
Each tactic is a list of weighted cues. `score` = min(1, sum of matched cue weights)
is a heuristic *strength*, NOT a probability. A tactic is `detected` when score >= 0.5,
so a single weak cue (e.g. "free", "now") never triggers on its own.

These detectors describe *language*, not intent: "urgent, call me" from a friend is
urgency language too. Combine with scam_probability for a verdict.

Run on the cleaned original text (not preprocess.normalize) so evidence shows real
numbers and amounts. Rules were developed on train.csv only — never tune on test.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass

DETECT_AT = 0.5


@dataclass(frozen=True)
class Cue:
    name: str
    rx: re.Pattern
    weight: float


def _c(name: str, pattern: str, weight: float) -> Cue:
    return Cue(name, re.compile(pattern, re.I), weight)


# Unambiguous names match in any case. Names that are also ordinary words ("chase the
# guy", "an apple", "ups and downs", "see ee") only match with brand capitalization.
_BRANDS = (r"((?:hmrc|irs|dvla|royal mail|dhl|fedex|usps|evri|hermes|parcelforce|amazon|paypal|"
           r"icloud|netflix|microsoft|whatsapp|vodafone|t-mobile|"
           r"barclays|hsbc|lloyds|natwest|santander|monzo|wells fargo|citibank|"
           r"social security( administration)?|medicare)"
           r"|(?-i:UPS|EE|O2|Apple|Google|Orange|Chase|Citi|Post Office|APPLE|GOOGLE|ORANGE|CHASE))")

TACTICS: dict[str, list[Cue]] = {
    "urgency": [
        _c("urgent", r"\burgent(ly)?\b", 0.5),
        _c("immediately", r"\bimmediately\b|\bat once\b|\bright away\b", 0.5),
        _c("act_now", r"\b(act|call|reply|respond|txt|text|claim|click|verify) (now|today|immediately)\b", 0.5),
        _c("deadline", r"\b(within|in the next) \d+ ?(min(ute)?s?|hrs?|hours?|days?)\b", 0.5),
        _c("deadline_weak", r"\bby (midnight|tonight|end of (the )?day)\b", 0.3),
        _c("expiry", r"\bexpir(e|es|ing|y|ed)\b|\bvalid (for )?(only )?\d+ ?(hrs?|hours?|days?)( only)?\b|\b\d+ ?hrs? only\b", 0.6),
        _c("last_chance", r"\b(last|final) (chance|notice|attempt|reminder|warning)\b|\b2nd attempt\b", 0.6),
        _c("repeated_contact", r"\b(trying|tried|attempt(ed|ing)) to (contact|reach) (u|you)\b|\b(2nd|second|third) time we have tried\b", 0.5),
        _c("scarcity", r"\b(today|tonight) only\b|\blimited (time|offer|places|stock)\b|\bwhile stocks last\b|\bonly \d+ (left|remaining)\b|\bhurry\b", 0.5),
        _c("now_weak", r"\bnow\b|\basap\b", 0.2),
    ],
    "fear": [
        _c("account_action", r"\b(account|card|number|service|sim|profile|benefits?)\b[^.!?]{0,30}\b(suspend(ed)?|lock(ed)?|block(ed)?|frozen|freez(e|ing)|deactivat(ed|ion)|disabled|terminated|restricted|compromised|closed)\b", 0.7),
        _c("will_lose", r"\bwill be (suspended|locked|blocked|closed|terminated|disconnected|deactivated|cancelled|deleted|lost)\b|\b(lose|losing) (access|your (account|money|savings|benefits|number|data))\b", 0.6),
        _c("security_alert", r"\b(unauthori[sz]ed|suspicious|unusual|fraudulent)\b[^.!?]{0,20}\b(activity|transaction|login|sign[- ]?in|payment|charge|access)\b", 0.7),
        _c("legal", r"\blegal (action|proceedings)\b|\b(arrest )?warrant\b|\b(will|could|may) be (arrested|prosecuted|sued)\b|\blawsuit\b", 0.6),
        _c("legal_weak", r"\b(court|police)\b", 0.3),
        _c("penalty", r"\bpenalt(y|ies)\b|\b(late|additional) fees?\b|\b(pay|issued) a fine\b|\bfined\b|\bdebt collect\w*", 0.5),
        _c("unpaid", r"\b(unpaid|overdue|outstanding) (bill|balance|payment|invoice|toll|tax|fee)s?\b|\bfailed (payment|delivery)\b|\bpayment (failed|declined)\b", 0.5),
        _c("if_not", r"\b(failure to|if (you )?(do not|don't|dont) (respond|reply|pay|verify|act|call))\b", 0.4),
        _c("to_avoid", r"\bto avoid (suspension|charges|penalt\w+|disconnection|closure|being (charged|suspended))\b", 0.5),
        _c("problem_framing", r"\b(problem|issue) with your\b|\byour (account|card|parcel|package) (has been|is) (on hold|held)\b", 0.4),
    ],
    "authority_impersonation": [
        _c("brand", rf"\b{_BRANDS}\b", 0.4),
        _c("official_team", r"\b(security|fraud|billing|support|verification|customer (service|care|support)) (team|department|dept|centre|center)\b|\bcustomer (service|care) (announcement|representative)\b", 0.6),
        _c("valued_customer", r"\b(valued|dear|loyal) ([a-z]+ )?(customer|subscriber|member|user)s?\b", 0.5),
        _c("institutional_voice", r"\bour (records|system)s? (show|indicate)s?\b|\bwe have (detected|noticed|identified)\b|\brecent review of your\b|\baccount statement\b", 0.5),
        _c("official_claim", r"\b(official|government|gov\.uk|tax (office|authority|refund)|your bank|federal|department of)\b", 0.5),
        _c("bank_name_weak", r"\bbank of [a-z]+\b", 0.3),
        _c("brand_context", rf"\b{_BRANDS}\b[^.!?]{{0,40}}\b(account|delivery|parcel|package|payment|refund|verify|customer)\b", 0.3),
        _c("brand_header", rf"^\W*{_BRANDS}\s*[:\-|]", 0.3),  # "HSBC: ..." sender-style prefix
        _c("delivery_notice", r"\b(tried to (make a )?deliver\w*|delivery (waiting|attempt|failed)|redeliver\w*|parcel (is )?(waiting|held|on hold))\b", 0.5),
    ],
    "reward": [
        _c("you_won", r"\b(you|u|you've|u've|you have|u have|ur number has)\s?(just )?(won(?!['’]t)|been (specially )?(selected|chosen|awarded))\b|\b(you are|you're|u r|u are) (specially )?(selected|chosen)\b|\bwinners?\b", 0.6),
        _c("win_offer", r"\b(to )?win (a|an|£|\$|up to|cash|free|over|one|tickets?|\d)\b", 0.5),
        _c("prize", r"\bprizes?\b|\bjackpot\b|\bsweepstake\w*|\blottery\b|\b(prize|weekly|todays|today's|monthly|free) draw\b", 0.5),
        _c("congrats_weak", r"\bcongratulations\b|\bcongrats\b", 0.3),
        _c("claim", r"\bclaim\b|\bredeem\b|\bcollect your\b|\bunclaimed\b|\bunredeemed\b", 0.5),
        _c("award", r"\bawarded\b|\bbonus\b|\breward(s)?\b|\bvouchers?\b|\bgift ?cards?\b|\bcash ?back\b", 0.5),
        _c("big_money", r"[£$€]\s?\d{3,}|\b\d{3,}\s?(pounds|dollars)\b|<UKP>\d+", 0.4),
        _c("guaranteed", r"\bguaranteed?\b|\brisk[- ]free\b", 0.4),
        _c("refund_owed", r"\b(you are|you're|u r) (owed|entitled|eligible)\b|\bunclaimed refund\b|\bclaim (your|ur) refund\b", 0.5),
        _c("refund_weak", r"\brefund\b", 0.3),
        _c("free_weak", r"\bfree\b|\bcomplimentary\b|\bfor nothing\b", 0.3),
        _c("cash_weak", r"\bcash\b", 0.3),
    ],
}


@dataclass
class TacticResult:
    detected: bool
    score: float
    evidence: list[dict]  # [{"cue", "text", "start", "end"}]


def detect(text: str) -> dict[str, TacticResult]:
    out: dict[str, TacticResult] = {}
    for tactic, cues in TACTICS.items():
        evidence, score = [], 0.0
        for cue in cues:
            hits = list(cue.rx.finditer(text))
            if hits:
                score += cue.weight  # each cue counts once, however often it repeats
                evidence += [{"cue": cue.name, "text": m.group(0), "start": m.start(), "end": m.end()}
                             for m in hits]
        score = round(min(1.0, score), 2)
        out[tactic] = TacticResult(score >= DETECT_AT, score, sorted(evidence, key=lambda e: e["start"]))
    return out


def detect_dict(text: str) -> dict[str, dict]:
    return {k: asdict(v) for k, v in detect(text).items()}
