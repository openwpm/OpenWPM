## Crosslink Task Management

Create issues before starting work to keep things organized and enable context handoff between sessions.

### Creating Issues
- Use `crosslink quick "title" -p <priority> -l <label>` for one-step create+label+work.
- Issue titles should be changelog-ready: start with a verb ("Add", "Fix", "Update"), describe the user-visible change.
- Add labels for changelog categories: `bug`/`fix` → Fixed, `feature`/`enhancement` → Added, `breaking` → Changed, `security` → Security.
- For multi-part features: create parent issue + subissues. Work one at a time.
- Add context as you discover things: `crosslink issue comment <id> "..." --kind observation`

### Labels for Changelog Categories
- `bug`, `fix` → **Fixed**
- `feature`, `enhancement` → **Added**
- `breaking`, `breaking-change` → **Changed**
- `security` → **Security**
- `deprecated` → **Deprecated**
- `removed` → **Removed**
- (no label) → **Changed** (default)

### Quick Reference
```bash
# One-step create + label + start working
crosslink quick "Fix auth timeout" -p high -l bug

# Or use create with flags
crosslink issue create "Add dark mode" -p medium --label feature --work

# Multi-part feature
crosslink issue create "Add user auth" -p high --label feature
crosslink issue subissue 1 "Add registration endpoint"
crosslink issue subissue 1 "Add login endpoint"

# Track progress
crosslink session work <id>
crosslink issue comment <id> "Found existing helper in utils/" --kind observation

# Close (auto-updates CHANGELOG.md)
crosslink issue close <id>
crosslink issue close <id> --no-changelog    # Skip changelog for internal work
crosslink issue close-all --no-changelog     # Batch close

# Quiet mode for scripting
crosslink -q create "Fix bug" -p high  # Outputs just the ID number
```

### Session Management
Sessions auto-start. End them properly when you can:
```bash
crosslink session work <id>              # Mark current focus
crosslink session end --notes "..."      # Save handoff context
```

End sessions when: context is getting long, user indicates stopping, or you've completed significant work.

Handoff notes should include: what was accomplished, what's in progress, what's next.

### Typed Comments (REQUIRED)

Every `crosslink comment` MUST include `--kind` to categorize the comment for audit trails. This is not optional.

**Kinds**: `plan`, `decision`, `observation`, `blocker`, `resolution`, `result`, `handoff`

**Minimum required comments per issue:**
1. `--kind plan` — before writing code (what you intend to do)
2. `--kind result` — before closing (what you delivered)

**Also required when applicable:**
- `--kind decision` — when choosing between approaches
- `--kind blocker` / `--kind resolution` — when blocked and unblocked
- `--kind observation` — when you discover something noteworthy

```bash
crosslink issue comment <id> "Will refactor auth module to use middleware pattern" --kind plan
crosslink issue comment <id> "Chose middleware over decorator — matches existing patterns" --kind decision
crosslink issue comment <id> "Auth module refactored, 12 tests pass" --kind result
```

**You cannot omit `--kind`.** Even for brief comments, categorize them. The audit trail depends on it.

### Priority Guide
- `critical`: Blocking other work, security issue, production down
- `high`: User explicitly requested, core functionality
- `medium`: Standard features, improvements
- `low`: Nice-to-have, cleanup, optimization

### Dependencies
```bash
crosslink issue block 2 1     # Issue 2 blocked by issue 1
crosslink issue ready         # Show unblocked work
```

### Large Implementations (500+ lines)
1. Create parent issue: `crosslink issue create "<feature>" -p high`
2. Break into subissues: `crosslink issue subissue <id> "<component>"`
3. Work one subissue at a time, close each when done

### Context Window Management
When conversation is long or task needs many steps:
1. Create tracking issue: `crosslink issue create "Continue: <summary>" -p high`
2. Add notes: `crosslink issue comment <id> "<what's done, what's next>"`
