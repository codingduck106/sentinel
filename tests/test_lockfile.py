"""Guard against dependency drift: production once failed because uv.lock (which Vercel
installs from) was missing a runtime dependency declared in pyproject.toml."""
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _locked() -> dict[str, str]:
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    return {pkg["name"].lower(): pkg.get("version", "") for pkg in lock.get("package", [])}


def _canon(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def test_every_runtime_dependency_is_locked_at_the_pinned_version():
    deps = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["dependencies"]
    locked = {_canon(k): v for k, v in _locked().items()}
    problems = []
    for spec in deps:
        m = re.match(r"^\s*([A-Za-z0-9_.\-]+)\s*(?:==\s*([^;\s]+))?", spec)
        name, pinned = _canon(m.group(1)), m.group(2)
        if name not in locked:
            problems.append(f"{name} is in pyproject.toml but missing from uv.lock")
        elif pinned and locked[name] != pinned:
            problems.append(f"{name}: pyproject pins {pinned}, uv.lock has {locked[name]}")
    assert not problems, "Run `uv lock` and commit uv.lock:\n" + "\n".join(problems)
