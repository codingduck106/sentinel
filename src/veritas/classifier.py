"""Spam/legitimate classifier: Input text -> normalize -> TF-IDF -> Logistic Regression.

`scam_probability` is P(spam) from a model trained on the 2011 UCI SMS Spam Collection.
Those labels are "spam", which includes scams but also legal-but-unwanted marketing,
so read it as "probability this looks like unsolicited spam/scam SMS".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer

from veritas.preprocess import normalize_many

DEFAULT_MODEL = Path(__file__).resolve().parents[2] / "models" / "spam_lr.joblib"


def build_pipeline(C: float = 10.0) -> Pipeline:
    return Pipeline([
        ("normalize", FunctionTransformer(normalize_many)),
        ("tfidf", FeatureUnion([
            ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
            ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)),
        ])),
        ("lr", LogisticRegression(C=C, max_iter=2000)),
    ])


@dataclass
class SpamClassifier:
    pipeline: Pipeline
    threshold: float = 0.5
    meta: dict = field(default_factory=dict)

    def proba(self, texts: list[str]) -> np.ndarray:
        return self.pipeline.predict_proba(texts)[:, 1]

    def predict(self, texts: list[str]) -> np.ndarray:
        return (self.proba(texts) >= self.threshold).astype(int)

    def save(self, path: Path = DEFAULT_MODEL) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"pipeline": self.pipeline, "threshold": self.threshold, "meta": self.meta}, path)

    @classmethod
    def load(cls, path: Path = DEFAULT_MODEL) -> "SpamClassifier":
        # joblib/pickle executes code on load: only load model files you produced.
        d = joblib.load(path)
        return cls(d["pipeline"], d["threshold"], d["meta"])

    def top_features(self, k: int = 30) -> tuple[list, list]:
        names = self.pipeline.named_steps["tfidf"].get_feature_names_out()
        coef = self.pipeline.named_steps["lr"].coef_[0]
        order = np.argsort(coef)
        return ([(names[i], round(coef[i], 2)) for i in order[::-1][:k]],
                [(names[i], round(coef[i], 2)) for i in order[:k]])
