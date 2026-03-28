---
title: "RTK hook must be in project settings.json"
tags: [tooling]
sources: []
contributors: [claude]
created: 2026-03-28
updated: 2026-03-28
---

Claude Code does NOT merge global (~/.claude/settings.json) and project-level (.claude/settings.json) hooks — project hooks REPLACE global hooks entirely. No inherit flag exists.

RTK's rewrite hook is installed globally by `rtk init -g` but will NOT fire in projects that have their own .claude/settings.json (which crosslink creates).

## Fix

Add the RTK entry explicitly to .claude/settings.json (gitignored), as the last entry in the PreToolUse array (after crosslink's work-check entry):

```json
{
  "hooks": [
    {"command": "~/.claude/hooks/rtk-rewrite.sh", "timeout": 5, "type": "command"}
  ],
  "matcher": "Bash"
}
```

## WARNING

`crosslink init -f` overwrites .claude/settings.json and removes the RTK entry. Re-add it afterwards.

## Verification

Verified empirically 2026-03-28: removed entry → rtk gain count frozen; re-added → count incremented.
