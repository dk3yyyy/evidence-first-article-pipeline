"""Concurrent HTTP validation for article citation links."""
from __future__ import annotations

import concurrent.futures
import ipaddress
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\((https?://[^)]+)\)")
RAW_RE = re.compile(r"(?<!\()https?://[^\s)>]+")


class UnsafeDestinationError(ValueError):
    """Raised when a link or redirect targets a non-public network."""


def extract_links(text: str) -> list[str]:
    links = LINK_RE.findall(text) + RAW_RE.findall(text)
    # Sentence punctuation is not part of a bare URL. Parentheses are left
    # untouched because they can be meaningful URL characters.
    return sorted(set(url.rstrip(".,;:!?") for url in links))


def _unsafe_destination(url: str) -> str | None:
    """Return a reason when a URL targets a local or private network."""
    host = urllib.parse.urlsplit(url).hostname
    if not host:
        return "missing hostname"
    if host.lower() == "localhost" or host.lower().endswith(".localhost"):
        return "localhost destinations are disabled"
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, None)}
    except socket.gaierror:
        return None  # The request path will report the DNS failure normally.
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            return f"non-public destination {ip} is disabled"
    return None


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        unsafe = _unsafe_destination(newurl)
        if unsafe:
            raise UnsafeDestinationError(unsafe)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _check(url: str, timeout: float) -> dict[str, Any]:
    unsafe = _unsafe_destination(url)
    if unsafe:
        return {"url": url, "status": None, "final_url": None, "result": "unsafe", "error": unsafe}
    request = urllib.request.Request(url, headers={"User-Agent": "evidence-first-article-pipeline/0.1"})
    opener = urllib.request.build_opener(_SafeRedirectHandler())
    try:
        with opener.open(request, timeout=timeout) as response:
            return {"url": url, "status": response.status, "final_url": response.url, "result": "pass"}
    except UnsafeDestinationError as exc:
        return {"url": url, "status": None, "final_url": None, "result": "unsafe", "error": str(exc)}
    except urllib.error.HTTPError as exc:
        result = "blocked" if exc.code in {401, 403, 429} else "fail"
        return {"url": url, "status": exc.code, "final_url": exc.url, "result": result}
    except Exception as exc:  # network errors are report data, not crashes
        return {"url": url, "status": None, "final_url": None, "result": "fail", "error": str(exc)}


def audit_links(text: str, timeout: float = 20.0, workers: int = 8) -> dict[str, Any]:
    links = extract_links(text)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        results = list(pool.map(lambda url: _check(url, timeout), links))
    states = ("pass", "blocked", "unsafe", "fail")
    counts = {state: sum(item["result"] == state for item in results) for state in states}
    return {
        "pass": counts["fail"] == 0 and counts["unsafe"] == 0,
        "summary": {"total": len(results), **counts},
        "results": results,
    }
