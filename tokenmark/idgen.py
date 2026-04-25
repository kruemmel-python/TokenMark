import hashlib, difflib
from pathlib import Path

def normalize_text(text: str) -> str:
    return " ".join((text or "").replace("\r\n","\n").split())

def fingerprint(text: str) -> str:
    return "sha256:" + hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()

def deterministic_id(path: str, kind: str, index: int, text: str) -> str:
    seed = f"{Path(path).as_posix()}::{kind}[{index}]::{normalize_text(text)}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]

def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()
