"""Keyword/regex weak labeler for manipulation categories (multi-label).

These rules are a *seed* for annotation, not ground truth. They were written and
checked against data/processed/train.csv only — never tune them on val/test.

Usage:  python src/weak_labels.py [--split train] [--sample 0]
"""
from __future__ import annotations

import argparse
import re

import pandas as pd

R = lambda p: re.compile(p, re.I)  # noqa: E731

CATEGORIES: dict[str, dict] = {
    "urgency": {
        "desc": "Time pressure / scarcity: act now, expires, limited, final notice.",
        "rx": R(r"\burgent\b|\bimmediately\b|\basap\b|\bnow!|\bact now\b|\btoday only\b|"
                r"\bexpir\w*|\bvalid (for )?\d+ ?(hrs?|hours?|days?)\b|\blast chance\b|"
                r"\bfinal (notice|attempt|chance)\b|\bhurry\b|\blimited\b|\b2nd attempt\b"),
    },
    "reward_lure": {
        "desc": "Prize, win, free gift, cash, voucher — an unearned benefit as bait.",
        "rx": R(r"\bwon\b|\bwinner\b|\bwin\b|\bprize\b|\bclaim\b|\bselected\b|\bawarded\b|"
                r"\bfree\b|\bbonus\b|\bvoucher\b|\bcash\b|\bjackpot\b|\bguaranteed\b|"
                r"£\s?\d{3,}|\breward\b"),
    },
    "authority_impersonation": {
        "desc": "Claims to be a bank, network operator, customer service, delivery or official body.",
        "rx": R(r"\bcustomer (service|care|loyalty)\b|\bvalued (network |vodafone |orange )?customer\b|"
                r"\baccount (statement|review|has been)\b|\bbank (of|account)\b|"
                r"\b(tried to make a|attempt\w* to) deliver\w*|\bdelivery waiting\b|\bcourier\b|"
                r"\bour records\b|\brecent review of your\b|\bmobile (provider|operator)\b|"
                r"\b(vodafone|orange|o2|t-mobile) (customer|subscriber)s?\b|\bnational (lottery|savings)\b"),
    },
    "fear_threat": {
        "desc": "Threat of loss, penalty, suspension, or a problem the recipient must fix.",
        # "fine" deliberately excluded: in this corpus it is almost always "I'm fine".
        "rx": R(r"\bsuspend\w*|\bpenalt\w+|\bunpaid\b|\boverdue\b|\bdeactivat\w+|\bunauthori[sz]ed\b|"
                r"\bwill be (cancelled|closed|lost|terminated|disconnected)\b|\bunclaimed\b|"
                r"\b(important|urgent) (message|information|notice)\b|\bfinal (notice|attempt)\b|"
                r"\b(un)?able to (contact|reach) you\b|\btrying to contact (u|you)\b|\blegal action\b"),
    },
    "callback_cta": {
        "desc": "Push to call/text a premium or short-code number, or follow a link.",
        "rx": R(r"\b0[89]\d{8,}\b|\b(text|txt|send|reply)\b[^.]{0,25}\bto \d{4,6}\b|"
                r"\bcall \d{5,}|\b\d{5}\b.*\b(txt|text|reply)\b|https?://|www\.|\.(com|co\.uk|net)\b"),
    },
    "subscription_trap": {
        "desc": "Hidden recurring charges, opt-out wording, per-message pricing.",
        "rx": R(r"\b\d+p\b|\b(\d+|£\d+(\.\d+)?)\s?(p|ppm|/min|/msg|pmsg|/wk|/week|/month|pw)\b|"
                r"\bstop\b.*\b(to|send)\b|\bunsubscribe\b|\bopt[ -]?out\b|\bsubscri\w+|"
                r"\b(18|16)\+|\bper (week|msg|min)\b|\bstd (txt )?rate\b|\bt&c'?s?\b|\bpobox\b|\bpo box\b"),
    },
    "social_romance_lure": {
        "desc": "Flirting, dating, 'someone likes you', chat lines — exploiting curiosity/loneliness.",
        "rx": R(r"\bsingles?\b|\bdate\b.*\b(call|txt|text)\b|\bdating\b|\bsexy\b|\bhorny\b|"
                r"\bsomeone (has been|is) (looking|interested)|\bsecret admirer\b|\bflirt\w*|"
                r"\blonely\b|\bchat\b.*\b(0[89]\d+|\d{5})\b|\bmeet (local|new)\b"),
    },
}


def tag(text: str) -> dict[str, int]:
    return {c: int(bool(spec["rx"].search(text))) for c, spec in CATEGORIES.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="train", choices=["train"],
                    help="only train is allowed: rules must not be tuned on val/test")
    ap.add_argument("--sample", type=int, default=0, help="print N random hits per category for hand-checking")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    df = pd.read_csv(f"data/processed/{a.split}.csv")
    tags = pd.DataFrame([tag(t) for t in df["text"]])
    df = pd.concat([df, tags], axis=1)

    rows = []
    for c in CATEGORIES:
        spam_rate = df.loc[df.label == 1, c].mean()
        ham_rate = df.loc[df.label == 0, c].mean()
        rows.append({"category": c, "spam_hits": int(df.loc[df.label == 1, c].sum()),
                     "spam_%": round(100 * spam_rate, 1), "ham_hits": int(df.loc[df.label == 0, c].sum()),
                     "ham_%": round(100 * ham_rate, 1),
                     "lift": round(spam_rate / ham_rate, 1) if ham_rate else float("inf")})
    print(pd.DataFrame(rows).to_string(index=False))
    n_cat = tags.sum(axis=1)
    print(f"\nspam with >=1 category: {100 * (n_cat[df.label == 1] > 0).mean():.1f}%   "
          f"ham with >=1 category: {100 * (n_cat[df.label == 0] > 0).mean():.1f}%   "
          f"mean categories per spam: {n_cat[df.label == 1].mean():.2f}")

    if a.sample:
        for c in CATEGORIES:
            hits = df[df[c] == 1]
            print(f"\n=== {c} ({len(hits)} hits) ===")
            for _, r in hits.sample(min(a.sample, len(hits)), random_state=a.seed).iterrows():
                print(f"  [{'SPAM' if r.label else 'ham '}] {r.text[:140]}")


if __name__ == "__main__":
    main()
