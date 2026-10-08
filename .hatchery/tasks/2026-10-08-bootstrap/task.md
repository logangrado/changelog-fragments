# Task: bootstrap

**Status**: in-progress
**Branch**: hatchery/bootstrap
**Created**: 2026-10-08 10:15

## Objective

We are bootstrapping this repo.

The goal of this repo is to provide a plug-and-play fragments based changelog and release system.

The idea:

Automate the process of creating releases, based on changelog fragment files.

- Each PR must have a `CHANGELOG.d/<name>.md` file.
- we parse the conetnts to determine the release type:
  - fix/refactor/chore -> patch
  - feat ->  minor
  - antyhgin ending in ! -> major
  - ex:
    fix: some bug
    feat: add a feature
- PR pipeline:
  - validates that a changelog fragment exists
    - PRs must only create a single fragment, cannot modify existing (if any)
  - Determines the bump type
  - Posts a comment on the PR with a table showing:
    - bump type
    - current version
    - next version
    - changelog preview
  - Also makes available some evars for downstream workflows:
    - curent version (e.g. 1.2.3), next version (e.g. 1.3.0), and a snapshot (1.3.0+<CURRENT_SHA>)
    - the snapshot version is used for publishing ephemeral packages/images/etc
- Merge pipeline
  - Need to run the same pipeline to determine the version, must be made available for downstream pipelins so they can publish pypi packages/images/etc
  - After merge, we CONSOLIDATE the fragments into the changelog.md
    - Create a new section # v1.2.3 <date>, with feat/fix/whatever sections
    - each line should also link to the PR that created it
    - create a new commit on top of the target branch
    - then tags that commit (or perhaps we tag the merge commit, not the consolidated changelog commit).

This must be exposed as an easy PR action or actions that can just be added to any repo
- may have some configuration:
  - the base branch where we update/consolidate changelog
  - if we are not merging to the base branch, we can leave fragments alone -> support a dev/main workflow?
- all logic/code shoudl be written in python, exposed as a simple CLI
- this gets packaged into an image, and the action just calls functions from that CLI

I included the seekr-hatchery repo for reference, it uses conventional commits, and has a pipeline similar to this. We can use it as reference

## Agreed Plan

*(To be filled in after planning discussion)*

## Progress Log

*(Steps will appear here once the plan is agreed)*

## Summary

*(Fill in on completion — then remove Agreed Plan and Progress Log above.
Cover: key decisions made, patterns established, files changed, gotchas,
and anything a future agent working in this repo should know.)*
