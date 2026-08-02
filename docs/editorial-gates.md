# Deterministic editorial gates

These checks catch mechanical regressions. They do not replace a semantic evidence audit.

## `lint-dashes`

Counts em dashes in reader-facing prose and front matter while excluding HTML comments, fenced code and publication-status lines such as `DRAFT — NOT PUBLISHED`. The default limit is zero and can be changed with `--limit`.

## `wordcount`

Produces two counts after removing front matter, private HTML comments, image embeds, bare URLs, fenced code and publication-status lines. The reported `conservative_count` is the larger result.

A platform may count content differently. Record the basis used for an editorial limit instead of presenting a recommendation as an official platform rule.

## `distinctness`

Finds normalized sentences copied verbatim between two editions when they meet the configured minimum word count. It is designed for platform adaptations that must be materially rewritten rather than pasted.

Required-verbatim captions or legal text can produce legitimate overlaps. Review every hit rather than weakening the global threshold silently.

## `check-fabrication`

Scans for unsupported experience claims. Default phrases include `our customers`, `customer story`, `in production`, `real caller` and `real user`. Repeat `--term` to supply an article-specific list.

Explicit negations such as `no real callers` are ignored. The scanner is intentionally simple and can produce domain-specific false positives. Treat each hit as a review requirement, not proof of fabrication.

## Exit codes

- `0`: the gate passed or an informational command completed.
- `1`: the selected gate found a violation.
- `2`: invalid input, missing file or another execution error.

## Aggregate release gate

`article-pipeline check <package>` loads `article-pipeline.toml` and runs structural
validation, source/claim integrity, claim-local qualifier checks, visual validation,
dash policy, word policy, fabrication scanning and link auditing. Use `--skip-links`
for a deterministic offline run and `--master` to compare the final article against a
pre-edit evidence fingerprint.
