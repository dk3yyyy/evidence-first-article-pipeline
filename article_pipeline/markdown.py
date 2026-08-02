"""Small deterministic Markdown scanner for links, images and reader text.

It is intentionally narrower than a renderer but handles balanced inline-link
parentheses, reference-style destinations, fenced/inline code and escaped
brackets without requiring a networked parser dependency.
"""

from __future__ import annotations

import re
from typing import Any

FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.S)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
FENCE_RE = re.compile(r"```[^\n]*\n.*?```|~~~[^\n]*\n.*?~~~", re.S)
INLINE_CODE_RE = re.compile(r"(`+)(.*?)\1", re.S)
REFERENCE_RE = re.compile(r"^[ \t]*\[([^\]]+)\]:[ \t]*(?:<([^>]+)>|([^\s]+))(?:[ \t]+.*)?$", re.M)
RAW_URL_RE = re.compile(r"(?<![\w(])https?://[^\s<>]+")
STATUS_LINE_RE = re.compile(
    r"^\s*(?:Status:\s*)?\*{0,2}(?:(?:LOCAL\s+)?DRAFT\s*(?:—|-)\s*NOT\s+PUBLISHED|PUBLISHED)\*{0,2}\s*$",
    re.M | re.I,
)


def _mask(pattern: re.Pattern[str], text: str) -> str:
    return pattern.sub(lambda match: "\n" * match.group(0).count("\n") or " ", text)


def _find_closing_bracket(text: str, start: int) -> int | None:
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "]":
            return index
    return None


def _inline_destination(text: str, start: int) -> tuple[str, int] | None:
    if start >= len(text) or text[start] != "(":
        return None
    depth = 1
    escaped = False
    angle = False
    destination: list[str] = []
    index = start + 1
    while index < len(text):
        char = text[index]
        if escaped:
            destination.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
            destination.append(char)
        elif char == "<" and not destination:
            angle = True
        elif char == ">" and angle:
            angle = False
        elif char == "(" and not angle:
            depth += 1
            destination.append(char)
        elif char == ")" and not angle:
            depth -= 1
            if depth == 0:
                raw = "".join(destination).strip()
                if raw.startswith("<") and raw.endswith(">"):
                    raw = raw[1:-1]
                elif re.search(r"\s", raw):
                    raw = raw.split(None, 1)[0]
                return raw, index + 1
            destination.append(char)
        else:
            destination.append(char)
        index += 1
    return None


def extract_destinations(text: str) -> dict[str, Any]:
    """Extract HTTP links plus image (alt, destination) pairs."""
    safe = _mask(FENCE_RE, text)
    safe = _mask(INLINE_CODE_RE, safe)
    safe = HTML_COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n") or " ", safe)
    references: dict[str, str] = {}
    for match in REFERENCE_RE.finditer(safe):
        references[match.group(1).strip().casefold()] = match.group(2) or match.group(3)
    safe = REFERENCE_RE.sub(lambda m: " " * len(m.group(0)), safe)

    inline_links: list[str] = []
    raw_links: list[str] = []
    images: list[tuple[str, str]] = []
    occupied: list[tuple[int, int]] = []
    index = 0
    while index < len(safe):
        image = safe.startswith("![", index)
        if not image and safe[index] != "[":
            index += 1
            continue
        label_start = index + 2 if image else index + 1
        close = _find_closing_bracket(safe, label_start)
        if close is None:
            index += 1
            continue
        label = safe[label_start:close]
        cursor = close + 1
        destination: str | None = None
        end = cursor
        inline = _inline_destination(safe, cursor)
        if inline:
            destination, end = inline
        elif cursor < len(safe) and safe[cursor] == "[":
            ref_close = _find_closing_bracket(safe, cursor + 1)
            if ref_close is not None:
                ref = safe[cursor + 1 : ref_close].strip() or label
                destination = references.get(ref.casefold())
                end = ref_close + 1
        elif label.casefold() in references:
            destination = references[label.casefold()]
        if destination:
            if image:
                images.append((label, destination))
            elif destination.startswith(("http://", "https://")):
                inline_links.append(destination)
            occupied.append((index, end))
            index = max(end, close + 1)
        else:
            index = close + 1

    for match in RAW_URL_RE.finditer(safe):
        if any(start <= match.start() < end for start, end in occupied):
            continue
        raw_links.append(match.group(0).rstrip(".,;:!?"))
    links = sorted(set(inline_links + raw_links))
    return {
        "links": links,
        "inline_links": sorted(inline_links),
        "raw_links": sorted(raw_links),
        "images": images,
    }


def reader_lines(text: str, include_alt: bool = False) -> list[tuple[int, str]]:
    """Return reader-facing lines with original line numbers preserved."""
    front = FRONT_MATTER_RE.match(text)
    body = _mask(FRONT_MATTER_RE, text) if front else text
    body = _mask(HTML_COMMENT_RE, body)
    body = _mask(FENCE_RE, body)
    body = INLINE_CODE_RE.sub(" ", body)

    image_inline = re.compile(r"!\[([^\]]*)\]\((?:[^()]|\([^()]*\))*\)")
    link_inline = re.compile(r"(?<!!)\[([^\]]+)\]\((?:[^()]|\([^()]*\))*\)")
    body = image_inline.sub(lambda m: m.group(1) if include_alt else " ", body)
    body = link_inline.sub(lambda m: m.group(1), body)
    body = re.sub(r"!\[([^\]]*)\]\[[^\]]*\]", lambda m: m.group(1) if include_alt else " ", body)
    body = re.sub(r"(?<!!)\[([^\]]+)\]\[[^\]]*\]", r"\1", body)
    body = REFERENCE_RE.sub(" ", body)
    body = RAW_URL_RE.sub(" ", body)
    body = STATUS_LINE_RE.sub(" ", body)
    body = re.sub(r"^#{1,6}\s*", "", body, flags=re.M)
    return [(number, line) for number, line in enumerate(body.splitlines(), start=1)]


def reader_text(text: str, include_alt: bool = False) -> str:
    """Return normalized reader-facing prose while preserving link labels."""
    return "\n".join(line for _, line in reader_lines(text, include_alt=include_alt))
