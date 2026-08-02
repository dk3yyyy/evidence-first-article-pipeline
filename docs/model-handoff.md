# Model handoff contract

## Durable evidence package

Before drafting, the research role should produce:

1. `brief.md`
2. `sources.md`
3. `claim-ledger.md`
4. `outline.md`
5. `unresolved-questions.md`

The writing role receives this package rather than an unbounded research transcript. This reduces context noise and makes the evidence boundary reviewable.

## Writing permissions

The writing role may change:

- narrative order;
- explanation and analogy;
- sentence rhythm and transitions;
- headings and hooks when permitted by the brief;
- wording that does not alter claim scope.

It may not invent:

- sources or quotations;
- people, events or experiments;
- numbers, dates or benchmark results;
- first-person experience;
- causal confidence absent from the ledger.

Any new factual claim returns to research.

## Evidence-safe humanization

Humanization is an editorial pass, not detector evasion. Require the editor to preserve facts, qualifiers, citations, code, numbers, units, captions, alt text and status markers. If naturalness conflicts with fidelity, leave the sentence unchanged and flag it.

Run `article-pipeline fingerprint` before editing and `article-pipeline compare` afterward. Then perform a semantic claim audit because deterministic token preservation cannot detect every meaning change.
