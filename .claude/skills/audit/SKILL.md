---
name: audit
description: Use when stuck, confused, or disoriented in a crosslink-tracked project — dumps the full context (session state, active issue, locks, blockers, hook config, git state, project rules) so you can re-orient and decide a next action. Trigger when the user says "I'm stuck", "audit", "what's going on", or asks for a context dump.
---

# Audit — full context dump for re-orientation

Use this when you (or the user) have lost the plot in a crosslink-tracked project. The skill walks through every state surface and prints results so the next decision is grounded in real data, not guesses.

## 1. Project grounding (same as preflight)

Read core rules:

```
Read .crosslink/rules/global.md
```

Detect languages and read relevant rule files (check for `Cargo.toml`, `package.json`, `tsconfig.json`, `pyproject.toml`, `go.mod`, etc.).

Read project-specific rules:

```
Read .crosslink/rules/project.md
```

Read tracking rules based on current mode:

```bash
crosslink config get tracking_mode
```

Then read `.crosslink/rules/tracking-<mode>.md`.

## 2. Project tree scan

```bash
ls -1
```

Scan the project tree (max depth 3, max 50 entries) to ground yourself on actual paths.

## 3. Dependency versions

Read the primary manifest file to confirm actual dependency versions.

## 4. Session state

```bash
crosslink session status
```

What issue is being worked on? What was the last action?

## 5. Active issue details

If working on an issue, get full details:

```bash
crosslink issue show <issue-id>
```

Review all comments, especially plan and decision comments.

## 6. Related issues and blockers

```bash
crosslink issue blocked
crosslink issue ready
```

Are there blocking dependencies? What's unblocked and available?

## 7. Lock state

```bash
crosslink locks list 2>/dev/null
```

Are any issues locked by other agents?

## 8. Recent interventions

Check if there have been recent hook blocks or driver redirects by reviewing recent issue comments.

## 9. Hook configuration

```bash
crosslink config show
```

What tracking mode is active? What commands are blocked/gated?

## 10. VCS state

```bash
jj status
jj log -r '..@' --limit 5
jj diff --stat
```

What's the current change state? Any uncommitted working-copy changes?

## 11. Print diagnostic summary

```
Audit summary:
  Session:    active / working on #<id>
  Change:     <current change / bookmark>
  Tracking:   <mode>
  Languages:  <list>
  Open issues: <count>
  Blocked:    <count>
  Locks:      <count>
  Uncommitted: <count> files changed

Loaded rules: global.md, <lang>.md, tracking-<mode>.md, project.md
```

You are now fully re-oriented. Decide your next action based on this context.
