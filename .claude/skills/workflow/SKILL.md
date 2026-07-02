---
name: workflow
description: Use to walk the user through a guided policy review of the project's crosslink configuration — tracking mode, security policies, language rules, hook implementations, and workflow conventions. Identifies drift from defaults via `crosslink workflow diff` and offers targeted fixes or a `crosslink init --force` reset. Trigger when the user says "review the crosslink config", "audit the workflow policies", "/workflow", or asks whether the hook/rules setup is right.
---

# Workflow — guided crosslink policy review

You are conducting a guided policy review of this project's crosslink configuration. Walk the user through each section, explain what's configured, and suggest improvements.

## Step 1: Gather current state

First, run these commands to understand the current configuration:

```bash
crosslink workflow diff
```

Then read the key policy files:

- `.crosslink/hook-config.json` — tracking mode and command restrictions
- `.crosslink/rules/global.md` — core behavioral rules
- `.crosslink/rules/project.md` — project-specific conventions

## Step 2: Review tracking mode

Read `.crosslink/hook-config.json` and the active tracking mode rule file (`.crosslink/rules/tracking-strict.md`, `tracking-normal.md`, or `tracking-relaxed.md`).

Ask the user:

- Is the current tracking mode (`strict`/`normal`/`relaxed`) appropriate for your workflow?
- Are there commands in `blocked_git_commands` (git/jj commands the hooks block) that should be allowed, or allowed commands that should be blocked?
- Are the `allowed_bash_prefixes` complete for your toolchain?

## Step 3: Review security policies

Read `.crosslink/rules/global.md` (the security section), `.crosslink/rules/web.md`, and `.crosslink/rules/sanitize-patterns.txt`.

Ask the user:

- Are the OWASP/injection prevention rules current for your stack?
- Does `sanitize-patterns.txt` cover your application's sensitive patterns?
- For web projects: are the RFIP (Recursive Framing Interdiction Protocol) rules in `web.md` appropriate?

## Step 4: Review language rules

List all `.md` files in `.crosslink/rules/` and identify which languages are relevant to this project (check for source files in the repo).

Ask the user:

- Are rules deployed for all languages used in this project?
- Are there language rules deployed that aren't relevant (unnecessary noise)?
- Do any language-specific rules need updates for newer framework versions?

## Step 5: Review hook implementations

Read each hook file in `.claude/hooks/`:

- `work-check.py` — enforces issue tracking before code changes
- `session-start.py` — loads context on session start
- `prompt-guard.py` — guards against prompt injection
- `post-edit-check.py` — validates edits
- `pre-web-check.py` — validates web requests

For any files that `crosslink workflow diff` flagged as customized, highlight the differences and ask if they're still needed.

## Step 6: Review workflow conventions

Read `.crosslink/rules/global.md` (workflow sections) and `.crosslink/rules/project.md`.

Ask the user:

- Are the commit message conventions right?
- Are the code review and testing expectations appropriate?
- Should any workflow rules be added or relaxed?

## Step 7: Summary and recommendations

Summarize findings:

1. List any files that have drifted from defaults (from `crosslink workflow diff`)
2. Recommend specific changes based on the discussion
3. Offer to apply approved changes using `crosslink init --force` (resets to defaults) or targeted edits

If the user wants to reset customized files to defaults:

```bash
crosslink init --force
```

If they want targeted edits, make the specific changes they approve.
