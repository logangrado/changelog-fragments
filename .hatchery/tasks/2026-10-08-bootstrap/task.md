# Task: bootstrap

**Status**: in-progress
**Branch**: hatchery/pr-ci-only
**Created**: 2026-10-08 10:15

## Objective

Bootstrap a plug-and-play, fragment-based changelog and release system. Pull requests
must introduce one conventional-header fragment, receive a semantic-version preview,
and expose version outputs. Merges to a configured release branch must consolidate all
pending fragments into a linked changelog release, commit it, and tag it for downstream
package and image publishing.

## Context

The repository started with only a title README. The requested first version targets
GitHub Actions and puts release logic in a Python CLI packaged as a Docker action.
Fragments live at `CHANGELOG.d/<name>.md`; patch types are `fix`, `refactor`, `chore`,
`perf`, `revert`, and `test`, `feat` is minor, and a `!` header is major. Stable versions
come from `vX.Y.Z` tags and default to `v0.0.0`.

Preview automation must reject missing, multiple, modified, deleted, or non-Markdown
fragment changes; post a sticky PR comment; and export current, next, snapshot, bump,
and changelog values. Release automation must process every pending fragment, link
entries to introducing PRs, and support release-branch-only consolidation for dev/main
workflows.

## Agreed Plan

1. Remove the redundant `push` trigger from CI so lint, tests, and image smoke tests run only for pull requests.
2. Add one changelog fragment and validate the complete PR preview and local CI contract.
3. Run all checks and restore the completed ADR.

## Progress Log

- [x] Step 1: Pull-request-only CI and fragment
- [x] Step 2: Preview and CI validation
- [ ] Step 3: Final verification and ADR

## Summary

- Added the dependency-free `changelog_fragments` Python package and CLI with strict
  conventional-header parsing, semantic version calculation, full-SHA snapshots,
  deterministic changelog rendering, Git adapters, GitHub PR metadata, sticky comments,
  and multiline-safe Actions outputs.
- `preview` reads the proposed fragment directly from the selected Git ref and validates
  its three-dot diff. `consolidate` prepends a dated release to `CHANGELOG.md`, requires
  resolvable PR metadata in GitHub mode, and removes released fragments.
- Added a Docker action (`action.yml`, `Dockerfile`, and `entrypoint.sh`) with `preview`
  and `release` modes. `gh` is included only for API access. Release mode commits the
  consolidated changelog, tags that consolidation commit, optionally pushes both, and
  exports `release_sha` so downstream jobs build the definitive tagged source. Supplying
  container arguments bypasses Action dispatch and runs the CLI directly. Action input
  IDs use underscores because the Docker runtime preserves IDs in environment names and
  POSIX shells discard names containing hyphens; regression coverage exercises the exact
  `INPUT_BASE_REF`-style environment.
- Added secure preview and serialized release workflow examples. Branch filters own the
  base/release-branch policy, allowing fragments to pass through a development branch
  untouched until they reach the release branch.
- Installed those workflows and added the bootstrap fragment. The first merge exposed
  that production and CI filters incorrectly targeted `master`; the follow-up corrected
  them to `main`. Its CI and image build passed, but release consolidation was rejected
  by the PR-required ruleset after Git accepted an orphan `v0.1.0` tag. That tag is left
  in place by decision; pending feature fragments will make the next release `v0.2.0`.
- Added independent repository CI jobs for Ruff formatting/linting, pytest, and Docker
  image build/smoke testing, plus 41 tests covering domain behavior, Git repositories,
  CLI workflows, output formatting, and sticky-comment updates. CLI tests remove ambient
  GitHub runner variables so local expectations remain deterministic in Actions.
- The release workflow publishes the exact `release_sha` image to GHCR as both the
  immutable `vX.Y.Z` tag and `latest`, with pinned Docker actions and OCI source,
  revision, and version labels. Release branch and tag updates are atomic, preventing
  future branch-protection failures from leaving partial tags. Failed pushes print
  actionable deploy-key, ruleset-bypass, existing-tag, and README guidance.
- Protected releases use an optional repository-scoped write deploy key stored as
  `CHANGELOG_RELEASE_DEPLOY_KEY`; checkout falls back to `GITHUB_TOKEN` when it is absent.
  The Docker action prepares the commit and tag with `push: false`, and the host runner
  atomically pushes them using checkout's SSH configuration. The key is an environment
  secret, and the release job targets a `release` environment restricted to `main`, so
  pull requests and arbitrary branches cannot receive it. This keeps unprotected
  repositories configuration-free while protected repositories need one secret, one
  deploy key, one environment, and a deploy-key ruleset bypass.
- Documented fragment authoring, permissions, action inputs/outputs, publishing from the
  release SHA, protected-branch deploy-key creation and rotation, main-only environment
  restrictions, secret migration, optional approval, ruleset bypass, fork safety, direct
  image use, GHCR visibility, CLI use, and development. Instructions keep
  private keys outside the repository, and common local key filenames are ignored.
- Final verification passed the protected-release branch through its own patch preview
  (`v0.1.0` to `v0.1.1`), formatting, linting, all 41 tests, package sdist/wheel builds,
  shell syntax checks, YAML parsing, and whitespace checks. Consolidating all pending
  fragments should instead produce `v0.2.0` due to their feature entries. No container
  runtime was available in the sandbox, so the Dockerfile was not built
  locally; CI now performs that build and executes the image's `--help` smoke test.

Future maintainers should preserve the output names because consuming workflows use them
as the public contract. Release workflows need full Git history/tags, serialization, and
permission to push to the release branch. A remotely pinned action must be used with
`pull_request_target`; never execute code from the untrusted PR checkout.
