from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter()


class CurlParseRequest(BaseModel):
    curl: str


class CurlParseResponse(BaseModel):
    url: str
    method: str
    headers: Dict[str, str]
    body: Optional[Any]
    params: Dict[str, str]


def _fallback_parse(curl: str) -> Dict[str, Any]:
    # very close to frontend parser but simplified for server
    text = (
        curl.replace("\\\n", " ")
        .replace("\u2013", "--").replace("\u2014", "--").replace("\u2015", "--")
        .replace("\u2018", "'").replace("\u2019", "'")
        .replace("\u201C", '"').replace("\u201D", '"')
    )
    method = ""
    url = ""
    headers: Dict[str, str] = {}
    body_str = ""

    # Improved tokenization that handles headers with colons
    tokens: list[str] = []
    i = 0
    while i < len(text):
        # Skip leading whitespace
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text):
            break
            
        # Handle quoted strings
        if text[i] in ("'", '"'):
            quote = text[i]
            i += 1
            token = ""
            while i < len(text) and text[i] != quote:
                if text[i] == "\\" and i + 1 < len(text):
                    i += 1
                    token += text[i]
                else:
                    token += text[i]
                i += 1
            if i < len(text):
                i += 1  # skip closing quote
            tokens.append(token)
            continue
            
        # Handle regular tokens
        token = ""
        while i < len(text) and not text[i].isspace():
            token += text[i]
            i += 1
        if token:
            tokens.append(token)

    j = 0
    while j < len(tokens):
        t = tokens[j]
        if t in ("-X", "--request") and j + 1 < len(tokens):
            method = tokens[j + 1]
            j += 2
            continue
        if t in ("-H", "--header") and j + 1 < len(tokens):
            hv = tokens[j + 1]
            idx = hv.find(":")
            if idx > -1:
                # Header with colon format: "Key: Value"
                k = hv[:idx].strip()
                v = hv[idx + 1 :].strip()
                headers[k] = v
            else:
                # Header as separate key-value pair
                k = hv.strip()
                if j + 2 < len(tokens):
                    v = tokens[j + 2].strip()
                    headers[k] = v
                    j += 3
                    continue
            j += 2
            continue
        if t in ("--data", "--data-raw", "--data-binary", "--data-urlencode", "-d") and j + 1 < len(tokens):
            body_str = tokens[j + 1]
            j += 2
            continue
        # Skip common curl flags that don't affect the request structure
        if t in ("--location", "--follow", "-L", "--max-redirs", "--connect-timeout", "--timeout", 
                 "--retry", "--retry-delay", "--retry-max-time", "--insecure", "-k", "--verbose", "-v"):
            j += 1
            continue
        if not url and (t.startswith("http://") or t.startswith("https://") or t.startswith("/")):
            url = t
        j += 1

    params: Dict[str, str] = {}
    if url:
        try:
            base_for_path = "http://local" if url.startswith("/") else None
            u = ( __import__("urllib.parse").parse.urlparse(url) if base_for_path is None
                else __import__("urllib.parse").parse.urlparse(base_for_path + url) )
            for p in __import__("urllib.parse").parse.parse_qsl(u.query, keep_blank_values=True):
                params[p[0]] = p[1]
        except Exception:
            pass

    body: Any | None = None
    if body_str:
        s = body_str.strip()
        if s.startswith("{") or s.startswith("["):
            try:
                import json
                body = json.loads(s)
            except Exception:
                body = s
        else:
            # form encoded
            for pair in s.split("&"):
                if not pair:
                    continue
                k, _, v = pair.partition("=")
                params.setdefault(__import__("urllib.parse").parse.unquote_plus(k), __import__("urllib.parse").parse.unquote_plus(v))

    mm = (method or ("POST" if body_str else "GET")).upper()
    return {"url": url, "method": mm, "headers": headers, "body": body, "params": params}


@router.post("/parse-curl", response_model=CurlParseResponse)
async def parse_curl_endpoint(payload: CurlParseRequest) -> CurlParseResponse:
    curl = payload.curl or ""
    if not curl.strip():
        raise HTTPException(status_code=400, detail="Empty cURL input")
    
    try:
        # Try the external curlparser first
        try:
            import curlparser  # type: ignore
            req = curlparser.parse(curl)
            url: str = getattr(req, "url", "")
            method: str = getattr(req, "method", "GET").upper()
            headers: Dict[str, str] = dict(getattr(req, "headers", {}) or {})
            body = getattr(req, "data", None)
            params: Dict[str, str] = {}
            try:
                from urllib.parse import urlparse, parse_qsl
                u = urlparse(url)
                params = {k: v for k, v in parse_qsl(u.query, keep_blank_values=True)}
            except Exception:
                pass
            return CurlParseResponse(url=url, method=method, headers=headers, body=body, params=params)
        except (SystemExit, Exception) as e:
            # If curlparser fails (including SystemExit), use fallback
            data = _fallback_parse(curl)
            return CurlParseResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse cURL: {e}")


