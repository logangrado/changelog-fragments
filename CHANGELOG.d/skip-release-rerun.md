fix: skip redundant release workflow runs

Ignores changelog-only release pushes and defensively skips generated `chore(release):`
commits without suppressing ordinary chore releases.
