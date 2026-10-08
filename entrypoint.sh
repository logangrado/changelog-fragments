#!/bin/sh
set -eu

# Arguments mean direct CLI use (`docker run IMAGE --help`). GitHub Docker actions
# provide inputs through INPUT_* variables and invoke the image without arguments.
if [ "$#" -gt 0 ]; then
  exec changelog-fragments "$@"
fi

action_input() {
  # Action input IDs use underscores so POSIX shells preserve their INPUT_* variables.
  printenv "INPUT_$1" 2>/dev/null || true
}

git config --global --add safe.directory "${GITHUB_WORKSPACE:-/github/workspace}"
cd "${GITHUB_WORKSPACE:-/github/workspace}"

fragment_dir=$(action_input FRAGMENT_DIR)
fragment_dir=${fragment_dir:-CHANGELOG.d}
command=$(action_input COMMAND)
: "${command:?The command input must be preview or release}"

case "$command" in
  preview)
    base_ref=$(action_input BASE_REF)
    : "${base_ref:?The base-ref input is required for preview}"
    head_ref=$(action_input HEAD_REF)
    head_ref=${head_ref:-HEAD}
    pr_number=$(action_input PR_NUMBER)
    post_comment=$(action_input POST_COMMENT)
    post_comment=${post_comment:-true}
    set -- preview --base-ref "$base_ref" --head-ref "$head_ref" --fragment-dir "$fragment_dir"
    if [ -n "$pr_number" ]; then
      set -- "$@" --pr-number "$pr_number"
    fi
    if [ -n "${GITHUB_REPOSITORY:-}" ]; then
      set -- "$@" --repository "$GITHUB_REPOSITORY"
      set -- "$@" --repository-url "${GITHUB_SERVER_URL:-https://github.com}/$GITHUB_REPOSITORY"
    fi
    if [ "$post_comment" = "true" ]; then
      set -- "$@" --post-comment
    fi
    changelog-fragments "$@"
    ;;
  release)
    changelog=$(action_input CHANGELOG)
    changelog=${changelog:-CHANGELOG.md}
    push=$(action_input PUSH)
    push=${push:-true}
    git_user_name=$(action_input GIT_USER_NAME)
    git_user_name=${git_user_name:-github-actions[bot]}
    git_user_email=$(action_input GIT_USER_EMAIL)
    git_user_email=${git_user_email:-41898282+github-actions[bot]@users.noreply.github.com}
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

    git config user.name "$git_user_name"
    git config user.email "$git_user_email"
    git add --all -- "$changelog" "$fragment_dir"
    git commit -m "chore(release): $tag"
    release_sha=$(git rev-parse HEAD)
    git tag -a "$tag" -m "Release $tag"

    if [ "$push" = "true" ]; then
      # Never leave an orphan tag when branch protection rejects the release commit.
      if ! git push --atomic origin \
        "HEAD:${GITHUB_REF_NAME:?GITHUB_REF_NAME is required}" "$tag"; then
        cat >&2 <<EOF

error: could not atomically push the release commit and tag.

If ${GITHUB_REF_NAME} requires pull requests, the built-in GITHUB_TOKEN cannot bypass
that rule. Configure a write-enabled deploy key with an Always allow ruleset bypass,
run this action with push: false, and atomically push the resulting commit and tag from
a host workflow step where actions/checkout configured the SSH key.

Also check the Git output above for an existing $tag or other repository rules.
See README.md: "Authentication and protected branches".
EOF
        exit 1
      fi
    fi
    printf 'release_sha=%s\nrelease_tag=%s\n' "$release_sha" "$tag" >> "$GITHUB_OUTPUT"
    ;;
  *)
    echo "error: command must be preview or release" >&2
    exit 2
    ;;
esac
