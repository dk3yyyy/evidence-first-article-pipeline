# Contributing

Contributions are welcome when they strengthen evidence integrity, reproducibility, visual accessibility or publication safety.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Change requirements

- Add a regression test before changing validator behavior.
- Keep the core CLI dependency-free unless a dependency has a clear security and maintenance justification.
- Do not weaken a fail-closed check merely to accept a particular draft.
- Distinguish deterministic validation from semantic editorial judgment.
- Do not add platform automation that bypasses required disclosures or human approval.
- Do not include private article drafts, credentials or copyrighted source material.

Run before opening a pull request:

```bash
python -m unittest discover -s tests -v
python -m compileall -q article_pipeline tests
```
