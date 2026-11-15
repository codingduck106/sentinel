import pytest

from veritas.preprocess import normalize


@pytest.mark.parametrize("placeholder, real, token", [
    ("<#>", "42", "num"),
    ("<DECIMAL>", "3.5", "num"),
    ("<URL>", "http://bit.ly/x1", "urltok"),
    ("<URL>", "www.example.co.uk", "urltok"),
    ("<EMAIL>", "joe@example.com", "emailtok"),
    ("<TIME>", "10:30", "timetok"),
    ("<UKP>2000", "£2000", "moneytok"),
])
def test_placeholders_and_real_values_share_a_token(placeholder, real, token):
    # The whole point: a placeholder must be indistinguishable from what it replaced.
    assert normalize(f"see {placeholder} ok") == normalize(f"see {real} ok") == f"see {token} ok"


def test_phone_and_shortcode_collapse_to_num():
    # No dedicated phone/shortcode token: in training those were an anonymization artifact.
    assert normalize("call 0800 123 4567 or txt WIN to 87066") == "call num or txt win to num"
    assert normalize("Your code is 482913") == normalize("Your code is <#>")


def test_no_angle_brackets_survive():
    assert "<" not in normalize("at <TIME> i have <#> mins, <DECIMAL> left <URL>")
