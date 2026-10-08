#!/bin/sh
set -eu

git config --global --add safe.directory "${GITHUB_WORKSPACE:-/github/workspace}"
cd "${GITHUB_WORKSPACE:-/github/workspace}"

fragment_dir=${INPUT_FRAGMENT_DIR:-CHANGELOG.d}
command=${INPUT_COMMAND:?The command input must be preview or release}

case "$command" in
  preview)
    base_ref=${INPUT_BASE_REF:?The base-ref input is required for preview}
    head_ref=${INPUT_HEAD_REF:-HEAD}
    set -- preview --base-ref "$base_ref" --head-ref "$head_ref" --fragment-dir "$fragment_dir"
    if [ -n "${INPUT_PR_NUMBER:-}" ]; then
      set -- "$@" --pr-number "$INPUT_PR_NUMBER"
    fi
    if [ -n "${GITHUB_REPOSITORY:-}" ]; then
      set -- "$@" --repository "$GITHUB_REPOSITORY"
      set -- "$@" --repository-url "${GITHUB_SERVER_URL:-https://github.com}/$GITHUB_REPOSITORY"
    fi
    if [ "${INPUT_POST_COMMENT:-true}" = "true" ]; then
      set -- "$@" --post-comment
    fi
    changelog-fragments "$@"
    ;;
  release)
    changelog=${INPUT_CHANGELOG:-CHANGELOG.md}
    result=$(mktemp)
    changelog-fragments consolidate \
      --fragment-dir "$fragment_dir" \
      --changelog "$changelog" \
      --repository "${GITHUB_REPOSITORY:-}" | tee "$result"

    skip_release=$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["skip_release"])' "$result")
    if [ "$skip_release" = "true" ]; then
      exit 0
    fi
    next_version=$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["next_version"])' "$result")
    tag="v$next_version"

    git config user.name "${INPUT_GIT_USER_NAME:-github-actions[bot]}"
    git config user.email "${INPUT_GIT_USER_EMAIL:-41898282+github-actions[bot]@users.noreply.github.com}"
    git add --all -- "$changelog" "$fragment_dir"
    git commit -m "chore(release): $tag"
    release_sha=$(git rev-parse HEAD)
    git tag -a "$tag" -m "Release $tag"

    if [ "${INPUT_PUSH:-true}" = "true" ]; then
      git push origin "HEAD:${GITHUB_REF_NAME:?GITHUB_REF_NAME is required}" "$tag"
    fi
    printf 'release_sha=%s\nrelease_tag=%s\n' "$release_sha" "$tag" >> "$GITHUB_OUTPUT"
    ;;
  *)
    echo "error: command must be preview or release" >&2
    exit 2
    ;;
esac
