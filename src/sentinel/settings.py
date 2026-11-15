"""Environment settings. SENTINEL_* names are canonical; the pre-rename VERITAS_* names are still read as a fallback,
so a deployment whose variables haven't been renamed yet keeps working (no silent switch-off of the AI layer)."""
import os


def env(name: str, default: str | None = None) -> str | None:
    """Read SENTINEL_<name>, falling back to VERITAS_<name>, then the default."""
    for prefix in ("SENTINEL_", "VERITAS_"):
        value = os.environ.get(prefix + name)
        if value is not None:
            return value
    return default
