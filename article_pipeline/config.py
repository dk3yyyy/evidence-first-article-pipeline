"""Project configuration loading and validation."""

from __future__ import annotations

import copy
import tomllib
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "schema_version": 1,
    "editorial": {
        "em_dash_limit": 0,
        "minimum_distinct_sentence_words": 12,
        "fabrication_terms": [
            "our customers",
            "customer story",
            "in production",
            "real caller",
            "real callers",
            "real user",
            "real users",
        ],
        "minimum_words": 0,
        "maximum_words": 0,
    },
    "links": {
        "enabled": True,
        "allow_blocked": True,
        "timeout_seconds": 20.0,
        "workers": 8,
    },
    "visuals": {
        "required_roles": ["illustration", "informative-image", "diagram"],
        "require_alt_text": True,
        "require_provenance": True,
    },
}


def _merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _merge(base[key], value)
        else:
            base[key] = value
    return base


def _require(value: Any, expected: type | tuple[type, ...], path: str) -> None:
    if not isinstance(value, expected) or isinstance(value, bool) and expected is int:
        raise ValueError(f"{path} must be {expected}, got {type(value).__name__}")


def validate_config(config: dict[str, Any]) -> None:
    _require(config.get("schema_version"), int, "schema_version")
    editorial = config.get("editorial")
    links = config.get("links")
    visuals = config.get("visuals")
    if not isinstance(editorial, dict):
        raise ValueError("editorial must be a table")
    if not isinstance(links, dict):
        raise ValueError("links must be a table")
    if not isinstance(visuals, dict):
        raise ValueError("visuals must be a table")
    for key in (
        "em_dash_limit",
        "minimum_distinct_sentence_words",
        "minimum_words",
        "maximum_words",
    ):
        _require(editorial.get(key), int, f"editorial.{key}")
        if editorial[key] < 0:
            raise ValueError(f"editorial.{key} must be non-negative")
    _require(editorial.get("fabrication_terms"), list, "editorial.fabrication_terms")
    if not all(isinstance(item, str) and item.strip() for item in editorial["fabrication_terms"]):
        raise ValueError("editorial.fabrication_terms must contain non-empty strings")
    _require(links.get("enabled"), bool, "links.enabled")
    _require(links.get("allow_blocked"), bool, "links.allow_blocked")
    _require(links.get("timeout_seconds"), (int, float), "links.timeout_seconds")
    _require(links.get("workers"), int, "links.workers")
    if links["timeout_seconds"] <= 0 or links["workers"] <= 0:
        raise ValueError("link timeout and worker count must be positive")
    _require(visuals.get("required_roles"), list, "visuals.required_roles")
    _require(visuals.get("require_alt_text"), bool, "visuals.require_alt_text")
    _require(visuals.get("require_provenance"), bool, "visuals.require_provenance")


def load_config(path: Path) -> dict[str, Any]:
    config = copy.deepcopy(DEFAULT_CONFIG)
    if path.is_file():
        with path.open("rb") as handle:
            loaded = tomllib.load(handle)
        config = _merge(config, loaded)
    validate_config(config)
    return config
