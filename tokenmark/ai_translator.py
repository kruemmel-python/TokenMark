import json, os, re, urllib.parse, urllib.request
from pathlib import Path
from .catalog import load_catalog
from .tm import update_tm, fuzzy_suggestions
from .glossary import relevant_terms, glossary_prompt

def _mock_translate(text: str, target_lang: str) -> str:
    return f"[{target_lang}] {text}"


def _strip_json_fences(content: str) -> str:
    content = (content or "").strip()
    if content.startswith("```"):
        content = content.strip("`").strip()
        if content.lower().startswith("json"):
            content = content[4:].strip()
    return content

def _repair_jsonish(content: str) -> str:
    """Repair common local-LLM JSON mistakes without changing translated text.

    Examples accepted:
      ["text",]
      {"translations": ["text",],}
      ```json
      ["text"]
      ```
    """
    content = (content or "").strip()
    # Remove trailing commas before ] or }.
    content = re.sub(r",\s*([\]\}])", r"\1", content)
    # Some local models return smart quotes around the whole JSON block less often;
    # do not attempt broad quote conversion because it can corrupt translated text.
    return content

def _json_from_model_text(content: str):
    """Parse tolerant model output. Accepts fenced JSON, trailing commas, and JSON surrounded by prose."""
    content = _strip_json_fences(content)
    repaired = _repair_jsonish(content)
    try:
        return json.loads(repaired)
    except Exception:
        pass
    # Last-resort extraction: take the broadest JSON array/object span.
    starts = [i for i in (repaired.find("["), repaired.find("{")) if i != -1]
    if not starts:
        raise ValueError("no JSON object or array found")
    start = min(starts)
    end_array = repaired.rfind("]")
    end_obj = repaired.rfind("}")
    end = max(end_array, end_obj)
    if end <= start:
        raise ValueError("no complete JSON object or array found")
    snippet = _repair_jsonish(repaired[start:end+1])
    return json.loads(snippet)

def _coerce_translation_list(payload, items):
    """Normalize common LLM response shapes to a list of strings."""
    expected = len(items)
    ids = [str(it.get("id", "")) for it in items]

    if isinstance(payload, list):
        # ["...", "..."]
        if all(not isinstance(x, dict) for x in payload):
            out = [str(x) for x in payload]
        else:
            # [{"id":"...", "target":"..."}, ...] or {"translation": "..."}
            by_id = {}
            sequential = []
            for x in payload:
                if not isinstance(x, dict):
                    sequential.append(str(x))
                    continue
                val = (
                    x.get("target")
                    or x.get("translation")
                    or x.get("translated")
                    or x.get("text")
                    or x.get("value")
                    or x.get("msgstr")
                    or ""
                )
                if x.get("id") is not None:
                    by_id[str(x.get("id"))] = str(val)
                sequential.append(str(val))
            out = [by_id.get(i, "") for i in ids] if by_id and all(i in by_id for i in ids) else sequential
    elif isinstance(payload, dict):
        # {"translations": [...]}, {"items": [...]}, {"results": [...]}
        for key in ("translations", "items", "results", "data", "targets"):
            if isinstance(payload.get(key), list):
                return _coerce_translation_list(payload[key], items)
        # {"id1": "translation", ...}
        if all(i in payload for i in ids):
            out = [str(payload[i]) for i in ids]
        else:
            # {"id1": {"target": "..."}, ...}
            out = []
            for i in ids:
                v = payload.get(i, "")
                if isinstance(v, dict):
                    v = v.get("target") or v.get("translation") or v.get("text") or ""
                out.append(str(v))
    else:
        out = []

    if len(out) != expected or any(x is None for x in out):
        raise ValueError(f"expected {expected} translations, got {len(out)}")
    return [str(x) for x in out]

def _deepl_translate_batch(texts, target_lang):
    key=os.environ.get("DEEPL_API_KEY")
    if not key:
        raise SystemExit("DEEPL_API_KEY is not set. Use --provider mock for an offline first draft.")
    data=urllib.parse.urlencode([("auth_key",key),("target_lang",target_lang.upper()), *[("text",t) for t in texts]]).encode()
    req=urllib.request.Request("https://api-free.deepl.com/v2/translate", data=data)
    with urllib.request.urlopen(req, timeout=60) as r:
        payload=json.loads(r.read().decode("utf-8"))
    return [x["text"] for x in payload.get("translations",[])]

def _openai_translate_batch(items, target_lang, glossary_path=None, model=None):
    key=os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY is not set. Use --provider mock for an offline first draft.")
    model=model or os.environ.get("TOKENMARK_OPENAI_MODEL","gpt-4o-mini")
    texts=[it["source"] for it in items]
    terms=relevant_terms(texts, glossary_path) if glossary_path else []
    system=(
        "You are a documentation localization engine. Translate only the JSON field 'source' into "
        f"{target_lang}. Keep Markdown structure, URLs, placeholders, inline code, product names and punctuation-safe syntax intact. "
        "Return JSON only: an array of strings in the same order. "
    )
    gp=glossary_prompt(terms)
    if gp:
        system += "\n" + gp
    payload_items=[]
    for it in items:
        payload_items.append({
            "id": it["id"],
            "source": it["source"],
            "previous_context": it.get("previous",""),
            "next_context": it.get("next","")
        })
    body=json.dumps({
        "model": model,
        "messages": [
            {"role":"system","content":system},
            {"role":"user","content":json.dumps(payload_items, ensure_ascii=False)}
        ],
        "temperature":0.1
    }).encode("utf-8")
    req=urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"}
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        payload=json.loads(r.read().decode("utf-8"))
    content=payload["choices"][0]["message"]["content"].strip()
    try:
        return _coerce_translation_list(_json_from_model_text(content), items)
    except Exception as exc:
        raise SystemExit(f"OpenAI translator returned an unexpected response shape: {exc}") from exc

def _gemini_translate_batch(items, target_lang, glossary_path=None, model=None):
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set. In PowerShell: $env:GEMINI_API_KEY='your_key'")
    try:
        from google import genai
        from google.genai import types
    except Exception as exc:
        raise SystemExit("Gemini provider requires google-genai. Install it with: python -m pip install google-genai") from exc

    model = model or os.environ.get("TOKENMARK_GEMINI_MODEL", "gemini-2.5-flash-lite")
    texts = [it["source"] for it in items]
    terms = relevant_terms(texts, glossary_path) if glossary_path else []
    system = (
        "You are TokenMark's documentation localization engine. "
        f"Translate each item's 'source' field into {target_lang}. "
        "Keep Markdown structure, URLs, placeholders, inline code, JSX/HTML tags, product names, "
        "and punctuation-safe syntax intact. Use previous_context and next_context only as read-only context. "
        "Return JSON only: an array of strings in the same order as the input."
    )
    gp = glossary_prompt(terms)
    if gp:
        system += "\n" + gp

    payload_items = []
    for it in items:
        payload_items.append({
            "id": it["id"],
            "source": it["source"],
            "previous_context": it.get("previous", ""),
            "next_context": it.get("next", "")
        })

    prompt = system + "\n\nInput JSON:\n" + json.dumps(payload_items, ensure_ascii=False)
    client = genai.Client(api_key=key)
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
    except TypeError:
        # Compatibility fallback for older google-genai versions.
        response = client.models.generate_content(model=model, contents=prompt)

    content = (getattr(response, "text", None) or "").strip()
    if not content and hasattr(response, "candidates"):
        try:
            content = response.candidates[0].content.parts[0].text.strip()
        except Exception:
            pass
    try:
        return _coerce_translation_list(_json_from_model_text(content), items)
    except Exception as exc:
        # Gemini sometimes returns a single object or drops one item in larger batches.
        # For batch calls, retry each segment individually before failing the whole command.
        if len(items) > 1:
            out = []
            for it in items:
                out.extend(_gemini_translate_batch([it], target_lang, glossary_path=glossary_path, model=model))
            return out
        raise SystemExit(
            "Gemini translator returned an unexpected response shape. "
            f"Use --batch-size 1 or retry. Raw parse error: {exc}"
        ) from exc

def _lmstudio_model(base_url: str) -> str:
    model = os.environ.get("TOKENMARK_LMSTUDIO_MODEL", "").strip()
    if model:
        return model
    try:
        req = urllib.request.Request(base_url.rstrip("/") + "/models")
        with urllib.request.urlopen(req, timeout=10) as r:
            payload = json.loads(r.read().decode("utf-8"))
        data = payload.get("data") or []
        if data:
            first = data[0]
            if isinstance(first, dict):
                return str(first.get("id") or first.get("name") or "local-model")
            return str(first)
    except Exception:
        pass
    return "local-model"

def _lmstudio_translate_batch(items, target_lang, glossary_path=None, model=None):
    """Translate via LM Studio's OpenAI-compatible /v1/chat/completions endpoint.

    Environment:
      TOKENMARK_LMSTUDIO_BASE_URL  default: http://127.0.0.1:1234/v1
      TOKENMARK_LMSTUDIO_MODEL     optional; otherwise first model from /v1/models is used
      TOKENMARK_LMSTUDIO_API_KEY   optional dummy key; default: lm-studio
    """
    base_url = os.environ.get("TOKENMARK_LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1").rstrip("/")
    model = model or _lmstudio_model(base_url)
    api_key = os.environ.get("TOKENMARK_LMSTUDIO_API_KEY", "lm-studio")

    texts = [it["source"] for it in items]
    terms = relevant_terms(texts, glossary_path) if glossary_path else []
    system = (
        "You are TokenMark's local documentation localization engine running in LM Studio. "
        f"Translate each item's 'source' field into {target_lang}. "
        "Keep Markdown structure, URLs, placeholders, inline code, JSX/HTML tags, product names, "
        "and punctuation-safe syntax intact. Use previous_context and next_context only as read-only context. "
        "Return JSON only: an array of strings in the exact same order and length as the input. "
        "Do not add explanations, markdown fences, or extra keys."
    )
    gp = glossary_prompt(terms)
    if gp:
        system += "\n" + gp

    payload_items = []
    for it in items:
        payload_items.append({
            "id": it["id"],
            "source": it["source"],
            "previous_context": it.get("previous", ""),
            "next_context": it.get("next", "")
        })

    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(payload_items, ensure_ascii=False)}
        ],
        "temperature": float(os.environ.get("TOKENMARK_LMSTUDIO_TEMPERATURE", "0.1")),
        "stream": False
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        base_url + "/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=int(os.environ.get("TOKENMARK_LMSTUDIO_TIMEOUT", "240"))) as r:
            payload = json.loads(r.read().decode("utf-8"))
    except Exception as exc:
        raise SystemExit(
            "LM Studio provider could not reach the local server. "
            "Start LM Studio Server and set, for example: "
            "$env:TOKENMARK_LMSTUDIO_BASE_URL='http://127.0.0.1:1234/v1'. "
            f"Original error: {exc}"
        ) from exc

    try:
        content = payload["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        raise SystemExit(f"LM Studio returned an unexpected chat/completions response: {payload}") from exc

    try:
        return _coerce_translation_list(_json_from_model_text(content), items)
    except Exception as exc:
        # Local models often miss JSON shape for batches. Fall back to one segment at a time.
        if len(items) > 1:
            out = []
            for it in items:
                out.extend(_lmstudio_translate_batch([it], target_lang, glossary_path=glossary_path, model=model))
            return out
        # Last resort for single-item calls: use raw text as translation if it is not JSON,
        # or recover the first quoted string from a malformed one-item JSON array.
        raw = _strip_json_fences(content).strip()
        if raw and not raw.startswith("{") and not raw.startswith("["):
            return [raw]
        m = re.match(r'^\s*\[\s*"((?:\\.|[^"\\])*)"', raw, flags=re.S)
        if m:
            try:
                return [json.loads('"' + m.group(1) + '"')]
            except Exception:
                return [m.group(1)]
        raise SystemExit(
            "LM Studio translator returned an unexpected response shape. "
            "Try --batch-size 1 or use a stronger instruct model. "
            f"Raw parse error: {exc}\nRaw content: {content[:500]}"
        ) from exc


def _contextual_items(entries, missing):
    index={id(e):i for i,e in enumerate(entries)}
    items=[]
    for e in missing:
        i=index[id(e)]
        prev=next((entries[j].get("source","") for j in range(i-1,-1,-1) if not entries[j].get("frozen")), "")
        nxt=next((entries[j].get("source","") for j in range(i+1,len(entries)) if not entries[j].get("frozen")), "")
        items.append({"id":e.get("id"),"source":e.get("source",""),"previous":prev,"next":nxt})
    return items

def auto_translate_catalog(catalog_path, target_lang, provider="mock", tm_path=None, glossary_path=None, batch_size=20):
    data=load_catalog(catalog_path)
    entries=data.get("entries",[])
    # First let the scalable TM propose exact/fuzzy suggestions. They are drafts and must be reviewed.
    if tm_path:
        for e in entries:
            if e.get("frozen") or e.get("target"):
                continue
            matches=fuzzy_suggestions(tm_path, e.get("source",""), target_lang, threshold=0.96, top_k=1)
            if matches:
                e["target"]=matches[0]["target"]
                e["status"]="needs_review"
                meta=e.setdefault("meta",{})
                meta["tm_suggestion"]=matches[0]
    missing=[e for e in entries if not e.get("frozen") and not e.get("target")]
    translated=[]
    if provider in ("mock","identity"):
        translated=[_mock_translate(e.get("source",""), target_lang) if provider=="mock" else e.get("source","") for e in missing]
    elif provider=="deepl":
        # DeepL does not get rich context here; TokenMark still enforces QA after translation.
        for i in range(0,len(missing),batch_size):
            translated.extend(_deepl_translate_batch([e.get("source","") for e in missing[i:i+batch_size]], target_lang))
    elif provider=="openai":
        items=_contextual_items(entries, missing)
        for i in range(0,len(items),batch_size):
            translated.extend(_openai_translate_batch(items[i:i+batch_size], target_lang, glossary_path=glossary_path))
    elif provider=="gemini":
        items=_contextual_items(entries, missing)
        for i in range(0,len(items),batch_size):
            translated.extend(_gemini_translate_batch(items[i:i+batch_size], target_lang, glossary_path=glossary_path))
    elif provider=="lmstudio":
        items=_contextual_items(entries, missing)
        for i in range(0,len(items),batch_size):
            translated.extend(_lmstudio_translate_batch(items[i:i+batch_size], target_lang, glossary_path=glossary_path))
    else:
        raise SystemExit(f"Unsupported provider: {provider}. Supported: mock, identity, deepl, openai, gemini, lmstudio")
    for e,t in zip(missing, translated):
        e["target"]=t
        e["status"]="needs_review"
        meta=e.get("meta") or {}
        meta["auto_translated_by"]=provider
        if glossary_path:
            meta["glossary_checked"]=True
        e["meta"]=meta
    Path(catalog_path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    if tm_path:
        from .models import Segment
        segs=[Segment(e["id"], e.get("kind",""), e.get("source",""), e.get("target",""), e.get("frozen",False), e.get("fingerprint",""), e.get("status",""), e.get("meta") or {}) for e in data.get("entries",[])]
        update_tm(segs, tm_path, target_lang)
    return len(missing)
