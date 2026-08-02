# Security policy

## Reporting

Please report vulnerabilities privately through GitHub's security-advisory interface rather than a public issue.

## Data handling

The core CLI processes local Markdown and makes no model-provider requests. `audit-links` performs outbound HTTP GET requests to URLs extracted from the selected article. It rejects loopback and private-network destinations by default. Treat articles containing secret or internal URLs as sensitive.

The project does not accept committed credentials, access tokens, private correspondence, unlicensed source documents or confidential drafts.

## Model boundary

Prompt files and local command-line tools do not guarantee local inference. Article privacy depends on the selected model provider, endpoint retention policy and agent environment. Review those boundaries before sending unpublished or confidential material to a model.
