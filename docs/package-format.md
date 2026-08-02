# Machine-readable package format

## Authority files

The canonical evidence records are:

- `evidence/sources.json`
- `evidence/claims.json`
- `evidence/model-provenance.json`
- `visuals/manifest.json`
- `article-pipeline.toml`

`sources.md` and `claim-ledger.md` are generated review views. Rebuild them with:

```bash
article-pipeline sync my-article
```

## Claim markers

Place a marker directly before the paragraph that expresses a verified claim:

```markdown
<!-- claims: CLM-001 -->
The bounded result may vary by environment.
```

Multiple claims can share a paragraph:

```markdown
<!-- claims: CLM-001, CLM-002 -->
```

Every verified claim must appear in the article. Every marker must resolve to a claim record. Terms in `required_qualifiers` are checked inside that claim's marked paragraph, preventing a qualifier from being moved to an unrelated sentence while preserving a global token count.

## Visual manifest

Each required visual role records:

- stable asset ID;
- role;
- editable source path;
- web export path;
- caption;
- alt text;
- provenance.

Strict validation rejects missing, empty, malformed or path-traversing asset files. SVG exports are parsed as XML; PNG, JPEG and WebP exports are checked by file signature.

## Configuration

`article-pipeline.toml` controls editorial and release policy. A value of `0` for `maximum_words` means no maximum. Link responses blocked by authentication or rate limiting pass only when `links.allow_blocked = true`.

## Archive manifest

Every reproducible package ZIP contains `MANIFEST.json` with:

- pipeline version;
- validation results;
- relative path, byte size and SHA-256 for every included file.

The manifest excludes itself to avoid a recursive checksum. The command also reports the ZIP and manifest SHA-256 values.
