
import json, sqlite3, time, hashlib, math, difflib, struct
from pathlib import Path
from .idgen import normalize_text

VECTOR_DIM = 96

def source_key(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()

def _tokens(text):
    return {w.lower() for w in normalize_text(text).split() if w.strip()}

def lexical_similarity(a,b):
    a=a or ""; b=b or ""
    if not a or not b: return 0.0
    ratio=difflib.SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()
    ta,tb=_tokens(a),_tokens(b)
    jac=(len(ta&tb)/len(ta|tb)) if ta and tb else 0.0
    return round((ratio*0.72)+(jac*0.28),4)

def semantic_vector(text: str, dim: int = VECTOR_DIM) -> list[float]:
    """Dependency-free semantic-ish embedding.

    TokenMark can optionally be connected to OpenAI/sentence-transformers later.
    The built-in vectorizer uses hashed word and character n-grams. It is not a
    neural embedding, but it captures stems, synonyms introduced by compounds and
    moderate rephrasings better than exact hashes while staying offline/portable.
    """
    norm = normalize_text(text or "").lower()
    vec = [0.0] * dim
    words = [w for w in norm.split() if w]
    grams = []
    grams.extend(words)
    for w in words:
        padded = f"_{w}_"
        for n in (3,4,5):
            grams.extend(padded[i:i+n] for i in range(max(0, len(padded)-n+1)))
    for i in range(max(0, len(words)-1)):
        grams.append(words[i] + " " + words[i+1])
    for g in grams:
        h = hashlib.blake2b(g.encode("utf-8"), digest_size=8).digest()
        idx = int.from_bytes(h[:4], "little") % dim
        sign = 1.0 if (h[4] & 1) else -1.0
        vec[idx] += sign
    mag = math.sqrt(sum(v*v for v in vec)) or 1.0
    return [v/mag for v in vec]


def embedding_vector(text: str) -> tuple[list[float], str]:
    """Return configured embedding vector plus backend name.

    TOKENMARK_EMBEDDING_BACKEND:
      - hash (default): offline deterministic hashed n-grams
      - sentence-transformers: local neural embeddings if installed
      - openai: OpenAI embeddings API if OPENAI_API_KEY is set
    """
    try:
        from .embeddings import vector_for
        return vector_for(text, semantic_vector)
    except Exception:
        return semantic_vector(text), "hash-ngram"

def pack_vector(vec: list[float]) -> bytes:
    return struct.pack("<" + "f"*len(vec), *vec)

def unpack_vector(blob: bytes | None) -> list[float] | None:
    if not blob:
        return None
    n = len(blob)//4
    return list(struct.unpack("<" + "f"*n, blob))

def cosine(a, b):
    if not a or not b:
        return 0.0
    n=min(len(a),len(b))
    return max(0.0, min(1.0, sum(a[i]*b[i] for i in range(n))))

def connect(path):
    p=Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    con=sqlite3.connect(str(p))
    con.row_factory=sqlite3.Row
    con.execute("""
    CREATE TABLE IF NOT EXISTS tm_entries(
      source_key TEXT,
      source TEXT NOT NULL,
      target TEXT NOT NULL,
      lang TEXT NOT NULL,
      kind TEXT,
      segment_id TEXT,
      status TEXT DEFAULT 'translated',
      updated_at REAL,
      meta_json TEXT DEFAULT '{}',
      embedding BLOB,
      embedding_backend TEXT DEFAULT 'hash-ngram',
      PRIMARY KEY(source_key, lang)
    )""")
    # Upgrade pre-0.7 databases in-place.
    cols={r["name"] for r in con.execute("PRAGMA table_info(tm_entries)").fetchall()}
    if "embedding" not in cols:
        con.execute("ALTER TABLE tm_entries ADD COLUMN embedding BLOB")
    if "embedding_backend" not in cols:
        con.execute("ALTER TABLE tm_entries ADD COLUMN embedding_backend TEXT DEFAULT 'hash-ngram'")
    con.execute("CREATE INDEX IF NOT EXISTS idx_tm_lang_kind ON tm_entries(lang, kind)")
    con.execute("""
    CREATE TABLE IF NOT EXISTS tm_revisions(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_key TEXT NOT NULL,
      lang TEXT NOT NULL,
      target TEXT NOT NULL,
      author TEXT DEFAULT 'unknown',
      status TEXT DEFAULT 'translated',
      timestamp REAL NOT NULL,
      meta_json TEXT DEFAULT '{}'
    )""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_tm_revisions_key ON tm_revisions(source_key, lang, timestamp)")
    con.commit()
    return con

def upsert(con, source, target, lang, kind="", segment_id="", status="translated", meta=None, with_embedding=True, author=None):
    if not source or not target: return
    sk=source_key(source)
    vec, backend = embedding_vector(source) if with_embedding else (None, "")
    emb=pack_vector(vec) if vec is not None else None
    con.execute("""INSERT INTO tm_entries(source_key,source,target,lang,kind,segment_id,status,updated_at,meta_json,embedding,embedding_backend)
      VALUES(?,?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(source_key,lang) DO UPDATE SET target=excluded.target, kind=excluded.kind,
      segment_id=excluded.segment_id, status=excluded.status, updated_at=excluded.updated_at, meta_json=excluded.meta_json,
      embedding=COALESCE(excluded.embedding, tm_entries.embedding),
      embedding_backend=COALESCE(excluded.embedding_backend, tm_entries.embedding_backend)""",
      (sk,source,target,lang,kind,segment_id,status,time.time(),json.dumps(meta or {}, ensure_ascii=False),emb,backend))
    meta = meta or {}
    rev_author = author or meta.get("author") or meta.get("auto_translated_by") or meta.get("provider") or "unknown"
    con.execute("INSERT INTO tm_revisions(source_key,lang,target,author,status,timestamp,meta_json) VALUES(?,?,?,?,?,?,?)",
                (sk,lang,target,rev_author,status,time.time(),json.dumps(meta, ensure_ascii=False)))

def exact(con, source, lang):
    return con.execute("SELECT * FROM tm_entries WHERE source_key=? AND lang=?", (source_key(source),lang)).fetchone()

def fuzzy(con, source, lang, threshold=0.82, top_k=3, mode="hybrid"):
    rows=con.execute("SELECT * FROM tm_entries WHERE lang=? ORDER BY updated_at DESC LIMIT 10000", (lang,)).fetchall()
    qvec = embedding_vector(source)[0] if mode in ("hybrid","vector","semantic") else None
    out=[]
    for r in rows:
        lex=lexical_similarity(source, r["source"])
        sem=0.0
        rv=unpack_vector(r["embedding"])
        if qvec is not None and rv is not None:
            sem=cosine(qvec, rv)
        if mode in ("vector","semantic"):
            score=sem
        elif mode=="lexical":
            score=lex
        else:
            score=max(lex, (sem*0.78)+(lex*0.22))
        if score>=threshold:
            out.append({"score":round(score,4),"lexical_score":lex,"semantic_score":round(sem,4),
                        "source":r["source"],"target":r["target"],"kind":r["kind"],
                        "segment_id":r["segment_id"],"status":r["status"]})
    out.sort(key=lambda x:x["score"], reverse=True)
    return out[:top_k]

def backfill_embeddings(sqlite_path):
    con=connect(sqlite_path); n=0
    rows=con.execute("SELECT source_key,lang,source FROM tm_entries WHERE embedding IS NULL").fetchall()
    for r in rows:
        con.execute("UPDATE tm_entries SET embedding=? WHERE source_key=? AND lang=?",
                    (pack_vector(embedding_vector(r["source"])[0]), r["source_key"], r["lang"]))
        n+=1
    con.commit(); con.close()
    return n

def migrate_json(json_path, sqlite_path, lang="de"):
    p=Path(json_path)
    if not p.exists(): return 0
    data=json.loads(p.read_text(encoding="utf-8"))
    con=connect(sqlite_path); n=0
    for e in data.get("entries",{}).values() if isinstance(data.get("entries"),dict) else data.get("entries",[]):
        if isinstance(e, dict) and e.get("source") and e.get("target"):
            upsert(con,e.get("source"),e.get("target"),lang,e.get("kind",""),e.get("last_segment_id") or e.get("segment_id",""),e.get("status","translated"))
            n+=1
    con.commit(); con.close()
    return n


def history(con, source_key_value=None, lang=None, segment_id=None, limit=5):
    """Return recent TM revisions.

    Either pass source_key_value/lang or segment_id/lang.
    """
    if segment_id and lang:
        row=con.execute("SELECT source_key FROM tm_entries WHERE segment_id=? AND lang=? ORDER BY updated_at DESC LIMIT 1",(segment_id,lang)).fetchone()
        if row:
            source_key_value=row["source_key"]
    if source_key_value and lang:
        rows=con.execute("SELECT * FROM tm_revisions WHERE source_key=? AND lang=? ORDER BY timestamp DESC LIMIT ?",
                         (source_key_value,lang,limit)).fetchall()
    else:
        rows=con.execute("SELECT * FROM tm_revisions ORDER BY timestamp DESC LIMIT ?",(limit,)).fetchall()
    return [dict(r) for r in rows]
