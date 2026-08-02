"""Deterministic editorial lint gates that complement evidence comparison."""
from __future__ import annotations

import re
from typing import Any

FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.S)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
FENCE_RE = re.compile(r"```[^\n]*\n.*?```", re.S)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
URL_RE = re.compile(r"https?://\S+")
STATUS_LINE_RE = re.compile(
    r"^\s*(?:Status:\s*)?\*{0,2}(?:(?:LOCAL\s+)?DRAFT\s*(?:—|-)\s*NOT\s+PUBLISHED|PUBLISHED)\*{0,2}\s*$",
    re.M | re.I,
)
WORD_RE = re.compile(r"\b[\w]+(?:['’\-][\w]+)*\b", re.UNICODE)
DEFAULT_FABRICATION_TERMS = (
    "our customers",
    "customer story",
    "in production",
    "real caller",
    "real callers",
    "real user",
    "real users",
)


def _split_front_matter(text: str) -> tuple[str, str]:
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return "", text
    return match.group(1), text[match.end():]


def _reader_text(text: str) -> str:
    _, body = _split_front_matter(text)
    body = HTML_COMMENT_RE.sub(" ", body)
    body = FENCE_RE.sub(" ", body)
    body = IMAGE_RE.sub(" ", body)
    body = URL_RE.sub(" ", body)
    body = STATUS_LINE_RE.sub(" ", body)
    body = re.sub(r"^#{1,6}\s*", "", body, flags=re.M)
    return body


def scan_em_dashes(text: str, limit: int = 0) -> dict[str, Any]:
    """Count reader-visible em dashes while preserving required status markers."""
    metadata, body = _split_front_matter(text)
    metadata = HTML_COMMENT_RE.sub("", metadata)
    comments = "".join(HTML_COMMENT_RE.findall(body))
    body_without_comments = HTML_COMMENT_RE.sub("", body)
    fenced_code = "".join(FENCE_RE.findall(body_without_comments))
    body_without_comments = FENCE_RE.sub("", body_without_comments)
    status_lines = STATUS_LINE_RE.findall(body_without_comments)
    visible = STATUS_LINE_RE.sub("", body_without_comments)
    visible_count = visible.count("—")
    metadata_count = metadata.count("—")
    return {
        "pass": visible_count <= limit and metadata_count <= limit,
        "limit": limit,
        "visible_count": visible_count,
        "metadata_count": metadata_count,
        "ignored_status_count": sum(line.count("—") for line in status_lines),
        "ignored_comment_count": comments.count("—"),
        "ignored_code_count": fenced_code.count("—"),
    }


def count_words(text: str) -> dict[str, int]:
    """Return two normalized reader-facing counts and the conservative maximum."""
    reader = _reader_text(text)
    regex_tokens = WORD_RE.findall(reader)
    whitespace_ready = re.sub(r"[^\w'’\-]+", " ", reader, flags=re.UNICODE).strip()
    whitespace_tokens = [token for token in whitespace_ready.split() if WORD_RE.fullmatch(token)]
    return {
        "regex_count": len(regex_tokens),
        "whitespace_count": len(whitespace_tokens),
        "conservative_count": max(len(regex_tokens), len(whitespace_tokens)),
    }


def _sentences(text: str) -> list[tuple[str, int]]:
    reader = _reader_text(text)
    out: list[tuple[str, int]] = []
    for raw in re.split(r"(?<=[.!?])\s+|\n{2,}", reader):
        normalized = " ".join(raw.split()).strip()
        if not normalized:
            continue
        words = WORD_RE.findall(normalized)
        out.append((normalized.casefold(), len(words)))
    return out


def measure_distinctness(master: str, candidate: str, minimum_words: int = 12) -> dict[str, Any]:
    """Detect long sentences copied verbatim between two reader-facing drafts."""
    master_sentences = {sentence for sentence, count in _sentences(master) if count >= minimum_words}
    candidate_sentences = {sentence for sentence, count in _sentences(candidate) if count >= minimum_words}
    overlaps = sorted(master_sentences & candidate_sentences)
    return {
        "pass": not overlaps,
        "minimum_words": minimum_words,
        "overlap_count": len(overlaps),
        "overlaps": overlaps,
    }


def check_fabrication(text: str, terms: list[str] | tuple[str, ...] | None = None) -> dict[str, Any]:
    """Flag configurable unsupported-experience phrases, allowing explicit negation."""
    selected = tuple(terms or DEFAULT_FABRICATION_TERMS)
    hits: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        low = line.casefold()
        for term in selected:
            pattern = re.compile(rf"\b{re.escape(term.casefold())}\b")
            for match in pattern.finditer(low):
                prefix = low[max(0, match.start() - 50):match.start()]
                if re.search(r"\b(?:no|not|never|without)\s+(?:\w+\s+){0,3}$", prefix):
                    continue
                hits.append({"line": line_number, "term": term, "text": line.strip()})
    return {"pass": not hits, "terms": list(selected), "hit_count": len(hits), "hits": hits}
