import pytest
from fastapi.testclient import TestClient

from sentinel.classifier import DEFAULT_MODEL
from sentinel.explain import risk_level

pytestmark = pytest.mark.skipif(not DEFAULT_MODEL.exists(), reason="run src/train.py first")


@pytest.fixture(scope="module")
def client():
    from sentinel.api import app
    return TestClient(app)


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_delivery_notice_without_tactics_is_not_high(client):
    # the false-positive class this rule targets: looks like 2011 spam to the classifier, no pressure tactics
    body = client.post("/api/analyze", json={"text": "Flipkart: Your order 670074 is out for delivery. Track: https://flipkart.com/track/x"}).json()
    assert body["risk_level"] != "high"


def test_refund_notice_is_not_a_reward_lure(client):
    body = client.post("/api/analyze", json={"text": "Income Tax Dept: Your refund of INR 14882 has been processed. Will be credited in 3-5 days."}).json()
    assert "reward" not in body["tactics_detected"]


def test_scam_message(client):
    r = client.post("/api/analyze", json={"text": "URGENT! You have won a £2000 prize. Call 09061701461 to claim"})
    assert r.status_code == 200
    body = r.json()
    assert body["risk_level"] == "high" and body["verdict"] == "This looks like a scam"
    reward = next(t for t in body["tactics"] if t["id"] == "reward")
    assert reward["detected"] and reward["evidence"] and reward["advice"]
    for t in body["tactics"]:
        for e in t["evidence"]:
            assert body["text"][e["start"]:e["end"]] == e["text"]


def test_normal_message(client):
    body = client.post("/api/analyze", json={"text": "Hey are we still on for dinner at 7?"}).json()
    assert body["risk_level"] == "low" and body["tactics_detected"] == []


@pytest.mark.parametrize("payload", [{"text": "   "}, {"text": "x" * 2001}, {}, {"text": 5}])
def test_rejects_bad_input(client, payload):
    assert client.post("/api/analyze", json=payload).status_code == 422


def test_errors_do_not_echo_input_or_internals(client):
    secret = "CANARY-7f3a my bank pin is 1234"
    r = client.post("/api/analyze", json={"text": secret + "x" * 2001})
    assert r.status_code == 422
    assert "CANARY" not in r.text and "pydantic" not in r.text and "loc" not in r.json()
    assert set(r.json()) == {"error"}
    nf = client.get("/api/nope")
    assert nf.status_code == 404 and set(nf.json()) == {"error"}


def test_oversized_body_rejected_before_parsing(client):
    r = client.post("/api/analyze", content=b'{"text":"' + b"a" * 50_000 + b'"}', headers={"content-type": "application/json"})
    assert r.status_code == 413 and r.json() == {"error": "Message too long."}


def test_unexpected_errors_are_generic(monkeypatch):
    import sentinel.api as api
    from fastapi.testclient import TestClient
    monkeypatch.setattr(api, "analyze", lambda text: (_ for _ in ()).throw(RuntimeError("boom /secret/path.py line 42")))
    r = TestClient(api.app, raise_server_exceptions=False).post("/api/analyze", json={"text": "hello"})
    assert r.status_code == 500 and "boom" not in r.text and "secret" not in r.text


def test_evidence_offsets_survive_whitespace_strip(client):
    body = client.post("/api/analyze", json={"text": "   URGENT call now  "}).json()
    for t in body["tactics"]:
        for e in t["evidence"]:
            assert body["text"][e["start"]:e["end"]] == e["text"]


def _utf16_slice(s: str, start: int, end: int) -> str:
    """Slice the way JavaScript does (UTF-16 code units)."""
    return s.encode("utf-16-le")[2 * start:2 * end].decode("utf-16-le")


def test_evidence_offsets_are_utf16_for_emoji(client):
    text = "🚨🚨 URGENT: your account will be suspended 💳 verify immediately"
    body = client.post("/api/analyze", json={"text": text}).json()
    spans = [e for t in body["tactics"] for e in t["evidence"]]
    assert spans
    for e in spans:
        assert _utf16_slice(body["text"], e["start"], e["end"]) == e["text"]


def test_undetected_tactics_do_not_move_the_risk_marker(client):
    # weak cues only ("free", "now"): nothing detected -> score must stay in the low band
    body = client.post("/api/analyze", json={"text": "free pizza at mine now"}).json()
    assert body["risk_level"] == "low" and body["tactics_detected"] == []
    assert body["risk_score"] < 1 / 3


@pytest.mark.parametrize("p, spam, n, level", [
    (0.9, True, 1, "high"),     # two signals: classifier + a tactic
    (0.1, False, 2, "high"),    # two signals: two tactics
    (0.99, True, 0, "medium"),  # classifier alone is ONE signal -> Medium, however confident
    (0.1, False, 1, "medium"),  # one tactic alone
    (0.25, False, 0, "medium"),
    (0.05, False, 0, "low"),
])
def test_risk_level(p, spam, n, level):
    assert risk_level(p, spam, n) == level
