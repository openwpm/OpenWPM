---
name: commit
description: Use to create a jj commit AND auto-document the result on the active crosslink issue. Writes a conventional-style message with the issue ref, and adds a `--kind result` comment so the audit trail closes. Trigger whenever the user asks to "commit", "commit changes", "commit and push", or finishes a unit of work in a crosslink-tracked repo.
---

# Commit — jj commit + crosslink result comment

The user wants to commit their current changes. Create a well-formed commit AND automatically record a result comment on the active crosslink issue.

## 1. Review changes

Run `jj diff --stat` to see what has changed in the working copy. jj auto-snapshots the working copy — there is no staging area. If the diff looks right, proceed.

## 2. Write the commit message

- Summarize what changed and why (1-2 sentences)
- Follow conventional commit style if the project uses it
- Never use jj/Jujutsu terminology in the message (project policy) — use version-control-neutral language.
- Optionally include the crosslink issue reference if an active issue exists (e.g. `[CL-5]`). Note: OpenWPM enforces conventional-commits via a commitlint `commit-msg` hook, so a leading `[CL-…]` prefix can fight that gate — keep it out of the type/scope header (e.g. append it to the body) or omit it.

## 3. Create the commit

```bash
jj commit -m "<message>"
```

Always pass `-m` — jj opens an editor if no message is given.

## 4. Auto-document the result on the active crosslink issue

After a successful commit, check if there's an active crosslink session with an active issue:

```bash
crosslink session status
```

If an active issue exists, record the commit as a result comment:

```bash
crosslink issue comment <issue-id> "Committed: <first line of commit message> | Files: <shortstat summary>" --kind result
```

For example:

```bash
crosslink issue comment 5 "Committed: Add typed comment support to schema | Files: 14 files changed, 312 insertions(+), 48 deletions(-)" --kind result
```

If no active session or issue, skip the comment silently.

## 5. Show summary

Display:
- The commit hash and message
- Files changed summary
- Whether the result was recorded on a crosslink issue

## Constraints

- Never force-push or rewrite commits without explicit user request.
- There is no staging area in jj — do not attempt `git add`. jj tracks the working copy automatically.
- Always record the result comment after a successful commit when an active issue exists.
- Always pass `-m` to `jj commit` — never let jj open an editor.
- If the commit fails (e.g. pre-commit hook), fix the issue and retry — do NOT record a result comment for failed commits.
