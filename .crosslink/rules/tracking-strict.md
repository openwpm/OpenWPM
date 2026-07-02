## Crosslink Task Management (MANDATORY — ABSOLUTE RULE)

**You MUST use crosslink to track ALL work. This is NOT optional. This is NOT a suggestion. This is an ABSOLUTE REQUIREMENT.**

**YOU MUST CREATE A CROSSLINK ISSUE BEFORE WRITING ANY CODE. NO EXCEPTIONS.**

Before your FIRST Write, Edit, or Bash tool call that modifies code:
1. Run `crosslink quick "title" -p <priority> -l <label>` to create an issue AND start working on it
2. The PreToolUse hook WILL BLOCK your tool calls if no issue is active
3. NEVER skip this step. NEVER proceed without an issue. NEVER treat this as optional.

### On Every User Request
1. Create issue(s) BEFORE starting work — ON ALL ISSUES NO MATTER WHAT. THIS IS A CRITICAL OVERRIDE.
2. When creating the issue, add as much detail as possible with comments so any new agent instance will understand the plan.

### Issue Title Requirements (CHANGELOG-READY)
Issue titles are automatically added to CHANGELOG.md when closed. Write titles that:
- Describe the user-visible change (not implementation details)
- Start with a verb: "Add", "Fix", "Update", "Remove", "Improve"
- Are complete sentences (but no period)

**GOOD titles** (changelog-ready):
- "Add dark mode toggle to settings page"
- "Fix authentication timeout on slow connections"
- "Update password requirements to include special characters"

**BAD titles** (implementation-focused):
- "auth.ts changes"
- "Fix bug"
- "Update code"
- "WIP feature"

### Labels for Changelog Categories
Add labels to control CHANGELOG.md section:
- `bug`, `fix` → **Fixed**
- `feature`, `enhancement` → **Added**
- `breaking`, `breaking-change` → **Changed**
- `security` → **Security**
- `deprecated` → **Deprecated**
- `removed` → **Removed**
- (no label) → **Changed** (default)

### Task Breakdown Rules
```bash
# Single task — use quick for create + label + work in one step
crosslink quick "Fix login validation error on empty email" -p medium -l bug

# Or use create with flags
crosslink issue create "Fix login validation error on empty email" -p medium --label bug --work

# Multi-part feature → Epic with subissues
crosslink issue create "Add user authentication system" -p high --label feature
crosslink issue subissue 1 "Add user registration endpoint"
crosslink issue subissue 1 "Add login endpoint with JWT tokens"
crosslink issue subissue 1 "Add session middleware for protected routes"

# Mark what you're working on
crosslink session work 1

# Add context as you discover things
crosslink issue comment 1 "Found existing auth helper in utils/auth.ts" --kind observation

# Close when done — auto-updates CHANGELOG.md
crosslink issue close 1

# Skip changelog for internal/refactor work
crosslink issue close 1 --no-changelog

# Batch close
crosslink issue close-all --no-changelog

# Quiet mode for scripting
crosslink -q create "Fix bug" -p high  # Outputs just the ID number
```

### Memory-Driven Planning (CRITICAL)

Your auto-memory directory (`~/.claude/projects/.../memory/`) contains plans, architecture notes, and context from prior sessions. **You MUST consult memory before creating issues.**

1. **Read memory first**: At session start, read `MEMORY.md` and any linked topic files. These contain the current plan of record.
2. **Translate plans to issues**: Break memory plans into small, concrete crosslink issues/epics/subissues. Each subissue should be completable in a single focused session.
3. **Verbose comments are mandatory**: When creating issues from a memory plan, add comments that quote or reference the specific plan section, rationale, and acceptance criteria so any new agent instance can pick up the work without re-reading memory.
4. **Stay on track**: Before starting new work, check if it aligns with the plan in memory. If the user's request diverges from the plan, update memory AND issues together — never let them drift apart.
5. **Close the loop**: When closing an issue, update memory to reflect what was completed and what changed from the original plan.

```bash
# Example: translating a memory plan into tracked work
crosslink issue create "Implement webhook retry system" -p high --label feature
crosslink issue comment 1 "Per memory/architecture.md: retry with exponential backoff, max 5 attempts, dead-letter queue after exhaustion. See 'Webhook Reliability' section." --kind plan
crosslink issue subissue 1 "Add retry queue with exponential backoff (max 5 attempts)"
crosslink issue comment 2 "Backoff schedule: 1s, 5s, 25s, 125s, 625s. Store attempt count in webhook_deliveries table." --kind plan
crosslink issue subissue 1 "Add dead-letter queue for exhausted retries"
crosslink issue comment 3 "Failed webhooks go to dead_letter_webhooks table with full payload + error history for manual inspection." --kind plan
crosslink issue subissue 1 "Add webhook delivery dashboard endpoint"
```

### When to Create Issues
| Scenario | Action |
|----------|--------|
| User asks for a feature | Create epic + subissues if >2 components |
| User reports a bug | Create issue, investigate, add comments |
| Task has multiple steps | Create subissues for each step |
| Work will span sessions | Create issue with detailed comments |
| You discover related work | Create linked issue |
| Memory contains a plan | Translate plan into epic + subissues with verbose comments |

### Session Management (MANDATORY)

Sessions are auto-started by the SessionStart hook. **You MUST end sessions properly.**

```bash
crosslink session work <id>          # Mark current focus — ALWAYS
crosslink session end --notes "..."  # REQUIRED before stopping — ALWAYS
```

**You MUST run `crosslink session end --notes "..."` when:**
- Context is getting long (conversation > 30-40 messages)
- User says goodbye, done, thanks, or indicates stopping
- Before any natural stopping point
- You've completed a significant piece of work

**Handoff notes MUST include:**
- What was accomplished this session
- What's in progress or blocked
- What should be done next

### Typed Comment Discipline (ABSOLUTE REQUIREMENT — NO EXCEPTIONS)

**Every comment MUST use the `--kind` flag. A comment without `--kind` is an incomplete comment. You are NOT ALLOWED to omit it.**

This is not guidance. This is not a suggestion. This is a hard requirement that exists because this tooling supports regulated biotech operations where audit completeness is legally mandated. You cannot opt out.

#### Comment Kinds

| Kind | When to use | You MUST use this when... |
|------|-------------|---------------------------|
| `plan` | Before writing any code | You are about to start implementation. EVERY issue gets at least one plan comment. |
| `decision` | Choosing between approaches | You picked option A over option B. Document both options and WHY you chose A. |
| `observation` | Discovering something | You found existing code, unexpected behavior, a pattern, or a constraint. |
| `blocker` | Something prevents progress | A test fails, a dependency is missing, an API doesn't work as expected. |
| `resolution` | Unblocking progress | You fixed the blocker. Document HOW. |
| `result` | Work is complete | Before closing: what was delivered, what tests pass, what changed. |
| `handoff` | Ending a session | Context for the next agent/session. What's done, what's next. |

#### Mandatory Comment Checkpoints

These are non-negotiable. You MUST add a comment at EACH of these points. Skipping ANY of them is a rule violation.

1. **Issue created** → `--kind plan` comment documenting your approach BEFORE you write a single line of code
2. **Each significant choice** → `--kind decision` comment. "Significant" means: if someone asked "why did you do it this way?", you should have already answered that in a decision comment
3. **Before closing** → `--kind result` comment summarizing deliverables
4. **Session ending** → `--kind handoff` comment (via `crosslink session end --notes "..."`)

#### Anti-Evasion Rules

You are explicitly forbidden from using any of the following rationalizations to skip typed comments:

- **"This is a small/trivial change"** → Small changes STILL need plan + result comments. Size does not exempt you.
- **"I'll add comments when I'm done"** → NO. Comments are added AS YOU WORK. Plan comments come BEFORE code. Decision comments come WHEN you decide. This is not negotiable.
- **"The commit message/PR description covers it"** → Commit messages are not crosslink comments. They serve different purposes. You must do both.
- **"The issue title is self-explanatory"** → Titles are one line. They cannot capture reasoning, alternatives considered, or findings.
- **"I'm just fixing a typo/formatting"** → Even trivial fixes get a plan comment ("fixing typo in X") and result comment ("fixed"). The overhead is seconds. The audit value is permanent.
- **"There's only one possible approach"** → Document that observation. If it's truly obvious, the comment takes 5 seconds.

#### Examples

```bash
# Starting work on a bug fix
crosslink quick "Fix authentication timeout on slow connections" -p high -l bug
crosslink issue comment 1 "Plan: The timeout is hardcoded to 5s in auth_middleware.rs:47. Will make it configurable via AUTH_TIMEOUT_SECS env var with 30s default." --kind plan

# You discover something while investigating
crosslink issue comment 1 "Found that the timeout also affects the health check endpoint, which has its own 10s timeout that masks the auth timeout on slow connections" --kind observation

# You make a design choice
crosslink issue comment 1 "Decision: Using env var over config file. Rationale: other timeouts in this service use env vars (see DATABASE_TIMEOUT, REDIS_TIMEOUT). Consistency > flexibility here." --kind decision

# Something blocks you
crosslink issue comment 1 "Blocked: The test suite mocks the auth middleware in a way that bypasses the timeout entirely. Need to update test fixtures first." --kind blocker

# You resolve it
crosslink issue comment 1 "Resolved: Updated test fixtures to use real timeout behavior. Added integration test for slow-connection scenario." --kind resolution

# Before closing
crosslink issue comment 1 "Result: AUTH_TIMEOUT_SECS env var now controls auth timeout (default 30s). Updated 3 test fixtures, added 2 integration tests. All 156 tests pass." --kind result
crosslink issue close 1
```

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
