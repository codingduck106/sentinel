"""Vercel Python entrypoint (service "backend", entrypoint main:app)."""
import os
import sys

# Keep Vercel's Python bundler aware of the optional contextual-analysis dependency.
import anthropic  # noqa: F401

# Serverless has no /dev/shm: tell joblib up front to run serially (silences a cold-start warning).
os.environ.setdefault("JOBLIB_MULTIPROCESSING", "0")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from veritas.api import app  # noqa: E402,F401
