"""Legacy import alias, kept only so models/spam_lr.joblib (pickled when the package was named `veritas`)
still unpickles. The saved model references veritas.preprocess; this maps that path onto sentinel.
Do not import from here in new code; re-saving the model is a deliberate, separate change."""
import importlib
import sys

for _name in ("preprocess", "classifier", "tactics", "explain", "analyze"):
    sys.modules[f"{__name__}.{_name}"] = importlib.import_module(f"sentinel.{_name}")
