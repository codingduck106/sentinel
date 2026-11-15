"""Hand-written cases. Modern positives matter most: the 2011 corpus has almost no
fear or impersonation examples, so these are the main check on those detectors."""
import pytest

from veritas.tactics import detect

POSITIVES = [
    # (text, tactics that must be detected)
    ("URGENT! Your account has been suspended. Verify within 24 hours to avoid closure.", {"urgency", "fear"}),
    ("HSBC Security Team: we have detected unusual activity on your account. Call us immediately.",
     {"authority_impersonation", "fear", "urgency"}),
    ("Royal Mail: your parcel is on hold due to an unpaid fee. Pay now: royalmail-redeliver.com",
     {"authority_impersonation", "fear"}),
    ("HMRC: you are entitled to a tax refund of £326.40. Claim before it expires.",
     {"authority_impersonation", "reward", "urgency"}),
    ("This is your final notice. Failure to pay will result in legal action and an arrest warrant.",
     {"fear", "urgency"}),
    ("Congratulations! You have won a £1000 Tesco gift card. Claim now!", {"reward", "urgency"}),
    ("WINNER!! As a valued network customer you have been selected to receive a £900 prize reward!",
     {"reward", "authority_impersonation"}),
    ("Your Netflix payment failed. Your account will be suspended unless you update billing.",
     {"fear", "authority_impersonation"}),
    ("Social Security Administration: your benefits are suspended due to fraudulent activity.",
     {"fear", "authority_impersonation"}),
]

HAM_TRAPS = [
    "I'm fine, hope you are too",
    "Are you free tonight?",
    "We won the match!! Celebrating at the pub",
    "Lol you won't believe what happened",
    "Congrats on the new job!",
    "I'm at the bank, back in 10",
    "Finally the match heading towards draw",
    "Yo dude guess who just got arrested the other day",
    "Can you call me when you get a chance",
    "Mum said dinner is at 7",
    # common words that are also brand names
    "I'll chase the delivery guy about the payment",
    "Bought apples and oranges, will sort the payment later",
    "Life has ups and downs, my account of it is long",
]


@pytest.mark.parametrize("text, expected", POSITIVES)
def test_detects_manipulation(text, expected):
    found = {k for k, v in detect(text).items() if v.detected}
    assert expected <= found, f"missing {expected - found}; got {found}"


@pytest.mark.parametrize("text", HAM_TRAPS)
def test_ham_traps_trigger_nothing(text):
    found = {k for k, v in detect(text).items() if v.detected}
    assert not found, f"false positive {found}"


def test_evidence_spans_point_into_text():
    text = "URGENT! You have won a £2000 prize. Call 09061701461 now"
    for res in detect(text).values():
        for e in res.evidence:
            assert text[e["start"]:e["end"]] == e["text"]


def test_single_weak_cue_does_not_trigger():
    r = detect("free stuff")
    assert r["reward"].score == 0.3 and not r["reward"].detected


def test_scores_bounded():
    r = detect("URGENT URGENT immediately last chance within 2 hours today only hurry act now")
    assert r["urgency"].score == 1.0
