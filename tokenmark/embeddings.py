
"""Optional embedding backends for TokenMark TM.

The default stays dependency-free. Setting TOKENMARK_EMBEDDING_BACKEND to
"sentence-transformers" or "openai" enables stronger semantic vectors when the
optional dependency/API key is available.
"""
from __future__ import annotations
import hashlib, json, os, math, urllib.request
from functools import lru_cache

def _norm(v):
    mag=math.sqrt(sum(float(x)*float(x) for x in v)) or 1.0
    return [float(x)/mag for x in v]

@lru_cache(maxsize=2)
def _st_model(name: str):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(name)

def sentence_transformer_vector(text: str, model: str | None = None) -> list[float]:
    model = model or os.environ.get("TOKENMARK_SENTENCE_MODEL") or "sentence-transformers/all-MiniLM-L6-v2"
    emb = _st_model(model).encode([text or ""], normalize_embeddings=True)[0]
    return [float(x) for x in emb.tolist()]

def openai_vector(text: str, model: str | None = None) -> list[float]:
    key=os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    model=model or os.environ.get("TOKENMARK_OPENAI_EMBEDDING_MODEL") or "text-embedding-3-small"
    payload=json.dumps({"model":model,"input":text or ""}).encode("utf-8")
    req=urllib.request.Request(
        "https://api.openai.com/v1/embeddings",
        data=payload,
        headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data=json.loads(r.read().decode("utf-8"))
    return _norm(data["data"][0]["embedding"])

def vector_for(text: str, fallback_fn) -> tuple[list[float], str]:
    backend=(os.environ.get("TOKENMARK_EMBEDDING_BACKEND") or "hash").lower().strip()
    try:
        if backend in ("sentence-transformers","sentence_transformers","st"):
            return sentence_transformer_vector(text), "sentence-transformers"
        if backend == "openai":
            return openai_vector(text), "openai"
    except Exception as exc:
        # Never make builds fail only because an optional vector backend is absent.
        if os.environ.get("TOKENMARK_EMBEDDING_STRICT") == "1":
            raise
    return fallback_fn(text), "hash-ngram"
