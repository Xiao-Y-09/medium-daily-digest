# from pathlib import Path

# def load_reader_profile(path: str = "reader_profile.md") -> str:
#     return Path(path).read_text(encoding="utf-8").strip()

from pathlib import Path

def load_reader_profile(path: str = "reader_profile.md") -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"{path} not found. Copy reader_profile.example.md to {path} and edit it."
        )
    return p.read_text(encoding="utf-8").strip()