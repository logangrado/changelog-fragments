fix: support releases to protected branches

Adds optional fine-grained PAT authentication with `GITHUB_TOKEN` fallback and makes
release commit and tag publication atomic.
