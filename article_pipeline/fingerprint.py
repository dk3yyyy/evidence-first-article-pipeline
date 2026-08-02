"""Deterministic evidence-surface fingerprinting for Markdown drafts."""

from __future__ import annotations

import collections
import hashlib
import json
import re
from typing import Any

from .markdown import STATUS_LINE_RE, extract_destinations

INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
FENCE_RE = re.compile(r"```[^\n]*\n.*?```", re.S)
HEADING_RE = re.compile(r"^#{1,6}\s+.+$", re.M)
NUMBER_RE = re.compile(r"(?<![\w.])(?:\d+(?:[.,]\d+)*|n\s*=\s*\d+)(?![\w.])", re.I)
UNIT_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:kHz|Hz|MHz|GHz|ms|s|%|px|MB|GB|words?|"
    r"samples?|utterances?|runs?|models?|tokens?)\b",
    re.I,
)
CLAIM_ID_RE = re.compile(r"\b(?:CLM|CLAIM)-[A-Za-z0-9_-]+\b", re.I)
DEFAULT_SCOPE_TERMS = (
    "may",
    "can",
    "could",
    "appears",
    "suggests",
    "reported",
    "estimated",
    "among inspected sources",
    "among the sources inspected",
    "synthetic",
    "does not establish",
    "not demonstrated",
    "unverified",
    "preprint",
)


def _counter(pattern: re.Pattern[str], text: str) -> collections.Counter[str]:
    return collections.Counter(pattern.findall(text))


def _status_lines(text: str) -> list[str]:
    return [match.group(0).strip() for match in STATUS_LINE_RE.finditer(text)]


def _scope_counts(text: str, terms: tuple[str, ...]) -> dict[str, int]:
    low = text.lower()
    return {term: low.count(term.lower()) for term in terms}


def fingerprint_text(
    text: str, scope_terms: tuple[str, ...] = DEFAULT_SCOPE_TERMS
) -> dict[str, Any]:
    """Return a stable, JSON-serializable fingerprint of protected Markdown surfaces."""
    destinations = extract_destinations(text)
    result: dict[str, Any] = {
        "markdown_link_destinations": dict(
            sorted(collections.Counter(destinations["inline_links"]).items())
        ),
        "raw_urls": dict(sorted(collections.Counter(destinations["raw_links"]).items())),
        "images": [list(item) for item in destinations["images"]],
        "inline_code": dict(sorted(_counter(INLINE_CODE_RE, text).items())),
        "code_fences": FENCE_RE.findall(text),
        "headings_and_order": HEADING_RE.findall(text),
        "numeric_tokens": dict(sorted(_counter(NUMBER_RE, text).items())),
        "number_unit_tokens": dict(sorted(_counter(UNIT_RE, text).items())),
        "claim_ids": dict(sorted(_counter(CLAIM_ID_RE, text).items())),
        "status_lines": _status_lines(text),
        "uncertainty_counts": _scope_counts(text, scope_terms),
    }
    canonical = json.dumps(result, sort_keys=True, ensure_ascii=False).encode("utf-8")
    result["sha256"] = hashlib.sha256(canonical).hexdigest()
    return result


def compare_text(
    master: str, candidate: str, scope_terms: tuple[str, ...] = DEFAULT_SCOPE_TERMS
) -> dict[str, Any]:
    """Fail closed when the candidate changes protected evidence surfaces."""
    before = fingerprint_text(master, scope_terms)
    after = fingerprint_text(candidate, scope_terms)
    exact_fields = (
        "markdown_link_destinations",
        "raw_urls",
        "images",
        "inline_code",
        "code_fences",
        "headings_and_order",
        "numeric_tokens",
        "number_unit_tokens",
        "claim_ids",
        "status_lines",
    )
    checks = {field: before[field] == after[field] for field in exact_fields}
    checks["uncertainty_counts_not_reduced"] = all(
        after["uncertainty_counts"].get(term, 0) >= count
        for term, count in before["uncertainty_counts"].items()
    )
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "master_sha256": before["sha256"],
        "candidate_sha256": after["sha256"],
        "before": before,
        "after": after,
    }
