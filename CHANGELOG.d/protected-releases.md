fix: support releases to protected branches

Adds optional repository deploy-key authentication with `GITHUB_TOKEN` fallback and
makes release commit and tag publication atomic.
