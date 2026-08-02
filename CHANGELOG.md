# Changelog

All notable changes to this project are documented here.

## 0.3.0 - 2026-08-02

### Added

- Project policy in `article-pipeline.toml`.
- Machine-readable source, claim, model and visual manifests with JSON Schemas.
- Claim markers and claim-local required-qualifier validation.
- Balanced Markdown link parsing with reference-style and code-block handling.
- `check` aggregate release gate and `sync` evidence-table renderer.
- Visual file parsing, non-empty checks, alt text, caption and provenance validation.
- Reproducible archive `MANIFEST.json` with per-file SHA-256 hashes.
- Complete passing example package.
- Ruff, mypy and 80% coverage CI gates.

## 0.2.0 - 2026-08-02

### Added

- Reader-visible em-dash linting that preserves required status markers.
- Dual normalized word counts with a conservative maximum.
- Long-sentence distinctness checks across master and adapted editions.
- Configurable unsupported-experience and fabrication phrase scanning.
- CLI and regression coverage for every new gate.
- CI coverage for Python 3.11 through 3.14.

## 0.1.0 - 2026-08-02

### Added

- Installable Python 3.11+ command-line interface.
- Complete evidence-first article-package templates.
- Deterministic Markdown evidence fingerprinting and comparison.
- Structural and strict release-readiness validation.
- Concurrent citation-link auditing with private-network protection.
- Reproducible ZIP packaging with integrity and SHA-256 reporting.
- Editorial, model-handoff, visual and publication-safety documentation.
- Eighteen unit and integration tests.
- Pinned GitHub Actions CI across Python 3.11, 3.12 and 3.13.
