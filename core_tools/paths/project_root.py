from pathlib import Path


def _find_root() -> Path:
    p = Path(__file__).resolve()
    while p.parent != p:
        if (p / 'reports').is_dir() and (p / '.git').is_dir():
            return p
        p = p.parent
    raise RuntimeError("Project root not found — expected reports/ and .git/ at the same level")


PROJECT_ROOT = _find_root()
