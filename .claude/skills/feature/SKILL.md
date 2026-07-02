---
name: feature
description: Use to create a `feat/<slug>` branch from a human-readable description and register a matching crosslink issue (priority medium, label `feature`). Slugifies the description, validates preconditions (no uncommitted changes, branch doesn't already exist), and checks out the new branch. Trigger when the user says "new feature branch for X", "make a feature branch", or "/feature …".
---

# Feature — create a feature branch + crosslink issue

The user will provide a human-readable description of the feature (e.g. "add batch retry logic"). Create a feature branch following the project's naming convention.

## 1. Derive the branch name

- Slugify the description: lowercase, strip non-alphanumeric characters (except hyphens), replace spaces with hyphens, collapse consecutive hyphens.
- The branch name is `feat/<slug>` (e.g. `feat/add-batch-retry-logic`), matching the repo convention (e.g. `feat/stealth-js-instrument-v2`).
- If the slug is empty or the branch already exists, ask the user for a different name.

## 2. Validate preconditions

- Confirm there are no unexpected working-copy changes (`jj status`). In jj the working copy is always a commit, so changes don't block branching — but warn the user if the diff is unexpectedly large and ask whether to proceed.
- Identify the base revision. Default to `@` (the current change). If the user provides a `--from <ref>` argument, use that instead.

## 3. Create the bookmark

```bash
jj bookmark create feat/<slug> -r <base-ref>
jj new feat/<slug> -m "wip: start feat/<slug>"
```

This creates the `feat/<slug>` bookmark and starts a new change on top of it. Always pass `-m` to `jj new`. Print the created bookmark name so the user can confirm.

## 4. Track in crosslink

- Create a crosslink issue for the feature work with the user's original description as the title.
- Set priority to `medium` (unless the user specifies otherwise).
- Use: `crosslink issue create "<description>" -p medium --label feature`

## Constraints

- Never force-push or delete bookmarks.
- Do not push the bookmark to a remote — the user will do that when ready.
- Keep the slug concise. If the description is very long, truncate to the first 6-8 meaningful words.
- Always pass `-m` to jj commands — never let jj open an editor.
