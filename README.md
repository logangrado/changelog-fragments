# Changelog Fragments

Plug-and-play, fragment-based changelog and semantic-release automation for GitHub.
Every pull request adds one small Markdown file; the action validates it, previews the
release, and later consolidates all pending fragments into a tagged `CHANGELOG.md`
release.

## Fragment format

Add exactly one new `CHANGELOG.d/<name>.md` file in every pull request. Existing
fragments cannot be edited or deleted by a pull request. The first non-empty line is a
[Conventional Commits](https://www.conventionalcommits.org/) style header:

```markdown
feat(search): add fuzzy matching

Search now tolerates minor spelling errors.
```

The header determines the version bump:

| Header | Bump |
|---|---|
| `fix`, `refactor`, `chore`, `perf`, `revert`, `test` | patch |
| `feat` | minor |
| Any supported or unsupported type ending in `!` | major |

Examples include `fix: handle an empty response`, `feat(api): add filters`, and
`feat!: remove the legacy endpoint`. Unknown non-breaking types are rejected so every
fragment has an unambiguous release effect.

## How releases work

The current version is the highest stable `vX.Y.Z` Git tag, or `v0.0.0` when no such
tag exists. A pull request preview uses its one fragment. A release uses **all** files
currently in `CHANGELOG.d`, taking the highest requested bump. This makes queued or
closely timed merges safe when the release workflow uses the documented concurrency
group.

On the configured release branch, the action:

1. calculates the next version;
2. resolves the pull request that introduced each fragment;
3. prepends a dated, grouped section to `CHANGELOG.md`, linking every entry to its PR;
4. deletes the consolidated fragments;
5. creates and pushes a `chore(release): vX.Y.Z` commit; and
6. creates an annotated `vX.Y.Z` tag on that consolidation commit and pushes it.

Tagging the consolidation commit ensures the tagged source contains its own changelog.
Downstream package and image jobs should depend on the release job and check out its
`release_sha` output. They still run in the workflow triggered by the original merge.
A push made with the repository `GITHUB_TOKEN` does not recursively start another
workflow.

## GitHub Actions setup

Copy the examples from [`examples/workflows`](examples/workflows) and replace
`your-org/changelog-fragments@v1` with the owner and pinned release of this action.

### Pull request preview

The preview workflow should run on `pull_request_target` so its token can update the
sticky PR comment. It needs:

```yaml
permissions:
  contents: read
  pull-requests: write
```

For fork safety, use this remotely pinned action and never execute scripts or other code
from the checked-out PR. The action only reads the proposed fragment. The complete
configuration is in
[`examples/workflows/changelog-preview.yml`](examples/workflows/changelog-preview.yml).

The preview validates that exactly one Markdown fragment was added and no existing
fragment was changed. Its sticky comment shows bump type, current version, next version,
snapshot version, and a rendered changelog preview.

### Release and publish

Trigger the release workflow only for the branch that owns releases (for example,
`main`) and grant:

```yaml
permissions:
  contents: write
  pull-requests: read
```

See [`examples/workflows/changelog-release.yml`](examples/workflows/changelog-release.yml).
That example serializes releases, exports job outputs, and checks out `release_sha` in a
downstream publishing job. Repository settings must permit GitHub Actions to push the
release commit and tag; adjust branch rules or use an appropriately scoped token if the
release branch disallows `GITHUB_TOKEN` pushes.

For a `dev`/`main` flow, run previews for PRs into either branch if desired, but trigger
the release action only on pushes to `main`. Fragments remain untouched while changes
are merged through `dev`, then are consolidated after they reach `main`. The base branch
is therefore configured by each workflow's `branches` filter rather than by hidden tool
state.

### Action inputs

| Input | Default | Purpose |
|---|---|---|
| `command` | required | `preview` or `release` |
| `base-ref` | — | Base SHA/ref for preview diff validation |
| `head-ref` | `HEAD` | PR head SHA/ref |
| `pr-number` | — | PR number for links and the sticky comment |
| `post-comment` | `true` | Post/update the preview comment |
| `fragment-dir` | `CHANGELOG.d` | Fragment directory |
| `changelog` | `CHANGELOG.md` | Consolidated changelog path |
| `push` | `true` | Push the release commit and tag |
| `git-user-name`, `git-user-email` | GitHub Actions bot | Release commit identity |

The action exposes `bump_type`, `current_version`, `next_version`, `snapshot_version`,
`skip_release`, and `changelog_preview`. Preview also exposes `fragment` and `comment`;
release also exposes `release_sha` and `release_tag`. Versions omit the `v` prefix except
`release_tag`. A snapshot has the form `1.3.0+<full-git-sha>` and is suitable for
PR-scoped ephemeral package/image versioning where the target ecosystem accepts SemVer
build metadata.

`gh` is included in the action image. It is used only for GitHub API operations: sticky
comments and PR metadata used by changelog links. Authentication comes from `GH_TOKEN`
in the workflow; credentials are not included in the image.

## Container image

This repository publishes each release from the tagged consolidation commit to GitHub
Container Registry. The immutable release tag and moving convenience tag are:

```text
ghcr.io/logangrado/changelog-fragments:v0.1.0
ghcr.io/logangrado/changelog-fragments:latest
```

The same image supports direct CLI invocation:

```console
$ docker run --rm ghcr.io/logangrado/changelog-fragments:v0.1.0 --help
$ docker run --rm \
    -v "$PWD:/work" -w /work \
    ghcr.io/logangrado/changelog-fragments:v0.1.0 \
    preview --base-ref origin/main --head-ref HEAD
```

The release workflow needs `packages: write`; it authenticates to `ghcr.io` with the
repository `GITHUB_TOKEN`. After the first publication, verify the package is linked to
this repository and set its visibility to **Public** in the package settings if anonymous
pulls should be allowed. The CI image job builds the Dockerfile and runs `--help` for
every pull request before publication.

## CLI

The release logic is available independently of Actions:

```console
$ pip install .
$ changelog-fragments preview --base-ref origin/main --head-ref HEAD
$ changelog-fragments consolidate --repository owner/repository
```

Both commands print JSON. When `GITHUB_OUTPUT` is set (or `--github-output` is passed),
they also emit multiline-safe GitHub Actions outputs. `consolidate` changes the working
tree but does not itself commit or tag; the container action performs that Git plumbing.
Use `--help` for path, date, PR, and comment options.

## Development

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/):

```console
$ uv sync --locked --group dev
$ uv run ruff format --check .
$ uv run ruff check .
$ uv run pytest
```

Repository CI runs formatting, linting, tests, and an image build/smoke test. The Docker
action can be built locally with `docker build -t changelog-fragments .` when a container
runtime is available.
