---
name: featree
description: Use to create a `feat/<slug>` bookmark AND spin up a new git worktree under `<repo-root>/.worktrees/<slug>`, then initialize crosslink hooks and an agent identity in the worktree so a child agent can work there. Trigger when the user says "make a worktree for <feature>", "/featree …", or asks to spin up an isolated workspace for a feature.
---

# Featree — feature bookmark + git worktree

The user provides a human-readable feature description (e.g. "add batch retry logic"). First create a feature bookmark using the `feature` skill, then move it into a new git worktree.

> This repo is colocated jj+git. Child-agent isolation uses **git worktrees** (this is what `crosslink kickoff` creates), not jj workspaces — a git worktree is a plain checked-out branch directory. The `feature` skill's jj bookmark auto-exports to a git branch, so `git worktree add … feat/<slug>` resolves it.

## 1. Create the feature bookmark

- Invoke the `feature` skill with the user's description as the argument.
- This creates the `feat/<slug>` bookmark and a new change on top of it.
- Note the bookmark name that was created.

## 2. Generate worktree path

- The worktree directory is `<repo-root>/.worktrees/<slug>` (inside the repo, gitignored).
- Extract the slug from the bookmark name by stripping the `feat/` prefix.
- Create the `.worktrees` directory if it doesn't exist: `mkdir -p <repo-root>/.worktrees`
- Ensure `.worktrees/` is gitignored: check if it's already in `.gitignore`, and if not, append it.

## 3. Create the git worktree

```bash
git worktree add <repo-root>/.worktrees/<slug> feat/<slug>
```

This checks out `feat/<slug>` into an isolated directory with its own working tree and HEAD. Changes made there do not affect the parent checkout until they land on the shared branch.

List worktrees to confirm: `git worktree list`

## 4. Initialize crosslink in the worktree

After creating the worktree, initialize crosslink so the child agent has proper hooks, skills, and access to shared state:

```bash
# In the worktree directory:
cd <worktree-path>

# Set up crosslink hooks and skills in the worktree
crosslink init --force
# NOTE: `crosslink init --force` REPLACES (does not merge) the project's
# `.claude/settings.json` hooks — re-add the project's RTK rewrite hook afterward.

# Initialize agent identity for this worktree
# Format: <parent-agent>--<feature-slug>
crosslink agent init <parent-agent>--<feature-slug>

# Sync latest issues from the coordination branch
crosslink sync
```

The agent ID should be derived from the parent agent name and the feature slug. For example, if the parent agent is `m1` and the feature slug is `add-retry`, the agent ID would be `m1--add-retry`.

To get the parent agent name, check `crosslink agent status --json` in the parent repo, or default to the machine hostname.

## 5. Report to user

Print a summary:

```
Worktree: <path>
Branch:   feat/<slug>

To start working:
  cd <worktree-path>

To return to the main checkout, just work from the original directory.
To remove this worktree when done: git worktree remove <path>
```

## Constraints

- Never force-push or delete branches.
- Do not push the branch to a remote — the user will do that when ready.
- Worktrees MUST be placed inside `<repo-root>/.worktrees/` to inherit the project's Claude Code trust scope and settings hierarchy.
