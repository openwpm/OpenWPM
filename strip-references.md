---
title: "Strip Internal References Before Push/PR"
tags: ["procedure", "pre-push"]
sources: []
contributors: ["8LcK"]
created: 2026-04-20
updated: 2026-04-20
---

Before any `git push` or `gh pr create`, all internal design-doc references must be stripped from commit messages, PR title/body, code comments, and docstrings.

## What to Strip

### Reference Tags
- `AC-N` (acceptance criteria references, e.g. AC-1, AC-3)
- `REQ-N` (requirement references, e.g. REQ-2, REQ-5)
- `CL-N` (crosslink issue references, e.g. CL-4, CL-6)

Replace each with plain English describing the intent. For example:
- `[CL-4]` → remove the tag or replace with a descriptive phrase like "extract predicate for testability"
- `[REQ-2]` → describe the requirement in natural language

### VDD-Specific Jargon
Remove or rephrase any of the following:
- "VDD methodology"
- "VDD Review History"
- "VDD pipeline"
- "convergence loop"
- Any other internal process terminology that would be meaningless to external contributors

## Where to Check
1. **Commit messages**: `git log --oneline` on the branch
2. **PR title and body**: review before submitting
3. **Code comments and docstrings**: grep the diff for reference patterns
4. **Branch name**: should not contain internal reference tags

## Quick Grep
```bash
git diff master...HEAD | grep -iE "(AC-[0-9]+|REQ-[0-9]+|CL-[0-9]+|VDD)"
git log master..HEAD --oneline | grep -iE "(AC-[0-9]+|REQ-[0-9]+|CL-[0-9]+|VDD)"
```

If matches are found, amend commits or reword before pushing.
