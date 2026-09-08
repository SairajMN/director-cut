import os
from pathlib import Path

_LOADED = False


def load_env(path: str | None = None) -> None:
    """Load KEY=VALUE pairs from .env into os.environ (existing env wins)."""
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    env_file = Path(path or Path(__file__).parent / ".env")
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))
