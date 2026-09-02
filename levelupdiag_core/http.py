"""Small dependency-free HTTP helpers."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

@dataclass(slots=True)
class HttpResult:
    url: str
    ok: bool
    status: int | None
    duration_ms: int
    error: str = ""
    body_preview: str = ""


def get(url: str, timeout: float = 5.0, accept: str = "*/*") -> HttpResult:
    started = time.perf_counter()
    req = urllib.request.Request(url, method="GET", headers={"Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(2048).decode("utf-8", errors="replace")
            duration = int((time.perf_counter() - started) * 1000)
            status = int(resp.status)
            return HttpResult(url=url, ok=200 <= status < 400, status=status, duration_ms=duration, body_preview=body[:500])
    except urllib.error.HTTPError as exc:
        duration = int((time.perf_counter() - started) * 1000)
        return HttpResult(url=url, ok=False, status=int(exc.code), duration_ms=duration, error=str(exc))
    except Exception as exc:
        duration = int((time.perf_counter() - started) * 1000)
        return HttpResult(url=url, ok=False, status=None, duration_ms=duration, error=f"{type(exc).__name__}: {exc}")


def get_json(url: str, timeout: float = 5.0) -> tuple[HttpResult, dict | list | None]:
    result = get(url, timeout=timeout, accept="application/json")
    if not result.ok:
        return result, None
    try:
        return result, json.loads(result.body_preview or "{}")
    except Exception as exc:
        result.ok = False
        result.error = f"Invalid JSON: {exc}"
        return result, None
