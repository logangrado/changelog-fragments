# v0.2.0 - 2026-10-08

## Features

- bootstrap fragment-based changelog releases ([#1](https://github.com/logangrado/changelog-fragments/pull/1))
  Adds the Python CLI, Docker-based GitHub Action, release preview and consolidation
  workflows, tests, and adoption documentation.
- publish release images from the main branch ([#2](https://github.com/logangrado/changelog-fragments/pull/2))
  Corrects the CI, preview, and release workflow branch filters, validates the Docker image
  in CI, and publishes tagged release images to GitHub Container Registry.

## Fixes

- support releases to protected branches ([#3](https://github.com/logangrado/changelog-fragments/pull/3))
  Adds optional repository deploy-key authentication with `GITHUB_TOKEN` fallback and
  makes release commit and tag publication atomic.
