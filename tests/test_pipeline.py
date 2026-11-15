from pathlib import Path

import pytest

from sentinel.analyze import analyze
from sentinel.classifier import DEFAULT_MODEL, SpamClassifier, build_pipeline

TOY_X = ["win a free prize call 09061701461 now", "claim your £500 cash txt WIN to 87066",
         "urgent you have won a voucher reply YES", "free entry weekly draw txt to 80086",
         "see you at 7 for dinner", "ok lol i'm on my way", "can you pick up milk", "love you, talk tonight"] * 3
TOY_Y = [1, 1, 1, 1, 0, 0, 0, 0] * 3


def test_roundtrip_save_load(tmp_path: Path):
    clf = SpamClassifier(build_pipeline(C=10).fit(TOY_X, TOY_Y), threshold=0.5, meta={"x": 1})
    clf.save(tmp_path / "m.joblib")
    clf2 = SpamClassifier.load(tmp_path / "m.joblib")
    assert (clf.proba(TOY_X) == clf2.proba(TOY_X)).all() and clf2.meta == {"x": 1}
    assert clf2.predict(["claim your free prize now call 09061701461"])[0] == 1


def test_placeholder_does_not_shift_prediction(tmp_path: Path):
    # normalize() runs inside the pipeline, so '<#>' and '5' must score identically.
    clf = SpamClassifier(build_pipeline(C=10).fit(TOY_X, TOY_Y))
    a, b = clf.proba(["i have <#> mins left"]), clf.proba(["i have 5 mins left"])
    assert a[0] == pytest.approx(b[0])


@pytest.mark.skipif(not DEFAULT_MODEL.exists(), reason="run src/train.py first")
def test_analyze_output_shape():
    r = analyze("URGENT! You have won a £2000 prize. Call 09061701461 to claim")
    assert set(r) >= {"scam_probability", "label", "tactics", "tactics_detected"}
    assert r["label"] == "spam" and r["scam_probability"] > 0.9
    assert {"urgency", "reward"} <= set(r["tactics_detected"])
    assert set(r["tactics"]) == {"urgency", "fear", "authority_impersonation", "reward"}
    assert analyze("Ok see you at 7 for dinner")["label"] == "legitimate"
