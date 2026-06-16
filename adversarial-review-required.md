---
title: "Adversarial review required per implementation issue"
tags: ["procedure", "process", "design-doc"]
sources: []
contributors: ["claude"]
created: 2026-06-16
updated: 2026-06-16
---


## Design Specification

### mechanism (the per-issue reminder)

- When an implementation/fix issue is created or started, label it **`needs-adversarial-review`**:
  `crosslink issue label <id> needs-adversarial-review`
- Clear the label **only** after a the-hater verdict that is either clean, or whose findings are all addressed + re-verified (FAIL-before/PASS-after where applicable):
  `crosslink issue unlabel <id> needs-adversarial-review`
- Do **not** close an issue still carrying `needs-adversarial-review`.
- `crosslink issue list` / `show` then surface the label as a standing gate, so the review isn't held only in working memory.

### proportionality

The default for any logic/behavior change is a the-hater pass. A genuinely trivial change (docs, comment removal, a one-line type fix) with FAIL-before/PASS-after + green CI may skip a *formal* the-hater — but record the skip + rationale as an issue comment, don't silently drop it.

### verify the verdict

the-hater has also been **wrong** (it once inverted the window.name diagnosis). VERIFY findings before acting — measure page-side, ground Xray/Firefox claims in the actual source, and reproduce the failure (revert the fix → test fails) to prove a guard is non-vacuous.

