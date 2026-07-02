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

## Priority 1: Security

These rules have the highest precedence. When they conflict with any other rule, security wins.

- **Web fetching**: Use `mcp__crosslink-safe-fetch__safe_fetch` for all web requests. Never use raw `WebFetch`.
- **SQL**: Parameterized queries only (`params![]` in Rust, `?` placeholders elsewhere). Never interpolate user input into SQL.
- **Secrets**: Never hardcode credentials, API keys, or tokens. Never commit `.env` files.
- **Input validation**: Validate at system boundaries. Sanitize before rendering.
- **Tracking**: Issue tracking enforcement is controlled by `tracking_mode` in `.crosslink/hook-config.json` (strict/normal/relaxed).

### Blocked Actions

This repo uses jj (colocated jj+git). **jj is the sanctioned VCS path and is NOT blocked.** The policy hooks block the **git** commands below only; for each, use the jj command instead:

- `git push` / `git push --force` / `git push -f` — blocked. Publish with `jj git push` instead.
- `git merge` / `git rebase` / `git cherry-pick` — blocked. Integrate with `jj rebase` / `jj new <revs>` / `jj duplicate` instead.
- `git reset` / `git reset --hard` / `git checkout .` / `git restore .` / `git clean` (`-f` / `-fd` / `-fdx`) — blocked. Discard changes with `jj restore <file>`, or start fresh with `jj new`, instead.
- `git stash` — blocked. Not needed in jj: the working copy is already a commit — use `jj new` to set work aside and `jj edit` to return.
- `git tag` / `git am` / `git apply` — blocked. Tags and patches go through the colocated git backend as a manual step (jj has no native equivalent).
- `git branch -d` / `git branch -D` / `git branch -m` — blocked. Manage bookmarks with `jj bookmark delete` / `jj bookmark rename` instead.

**Gated commands** (require an active crosslink issue):
- `git commit` — blocked; use `jj commit -m "..."` instead. An active crosslink issue is still required (the work-check hook enforces this on edits) — create one first with `crosslink quick` or `crosslink session work <id>`.

**Always allowed** (read-only):
- `jj status`, `jj diff`, `jj log`, `jj show` — current state inspection
- `git status`, `git diff`, `git log`, `git show` — also fine for read-only inspection in the colocated repo

If you need a blocked action performed, tell the user and continue with other work.

---

## Priority 2: Correctness

These rules ensure code works correctly. They yield only to security concerns.

- **No stubs**: Never write `TODO`, `FIXME`, `pass`, `...`, `unimplemented!()`, or empty function bodies. If too complex for one turn, use `raise NotImplementedError("Reason")` and create a crosslink issue.
- **Read before write**: Always read a file before editing it. Never guess at contents.
- **Complete features**: Implement the full feature as requested. Don't stop partway.
- **Error handling**: Proper error handling everywhere. No panics or crashes on bad input.
- **No dead code**: Intelligently deal with dead code. If it's a hallucinated function remove it. If it's an unfinished function complete it.
- **Test after changes**: Run the project's test suite after making code changes.

### Documentation Trail (MANDATORY — AUDIT REQUIREMENT)

This software supports regulated biotech operations. Every issue MUST have a documented decision trail. This is a correctness requirement, not a style preference.

**You MUST add typed comments to every issue you work on. There are ZERO exceptions to this rule.**

- You cannot reason that a change is "too small" to document. Small changes still need audit trails.
- You cannot defer comments to "later" or "when I'm done." Document AS you work, not after.
- You cannot claim the code is "self-documenting." Code shows WHAT changed. Comments show WHY.
- You cannot skip comments because "the issue title explains it." Titles are summaries, not trails.

**Mandatory comment points** — you MUST add a `crosslink comment` at each of these:
1. **Before writing code**: Document your plan and approach (`--kind plan`)
2. **When you make a choice between alternatives**: Document what you chose and why (`--kind decision`)
3. **When you discover something unexpected**: Document the finding (`--kind observation`)
4. **When something blocks progress**: Document the blocker (`--kind blocker`)
5. **When you resolve a blocker**: Document how (`--kind resolution`)
6. **Before closing the issue**: Document what was delivered (`--kind result`)

```bash
# These are NOT optional. You MUST use --kind on EVERY comment.
crosslink issue comment <id> "Approach: using existing auth middleware" --kind plan
crosslink issue comment <id> "Chose JWT over sessions — stateless, simpler for API consumers" --kind decision
crosslink issue comment <id> "Found legacy endpoint at /api/v1/auth that conflicts" --kind observation
crosslink issue comment <id> "Blocked: CI pipeline timeout on integration tests" --kind blocker
crosslink issue comment <id> "Resolved: increased CI timeout to 10m, tests pass" --kind resolution
crosslink issue comment <id> "Delivered: JWT auth with refresh tokens, all 47 tests passing" --kind result
```

**If you close an issue that has zero typed comments, you have violated this rule.**

### Intervention Logging (MANDATORY — AUDIT REQUIREMENT)

When a driver (human operator) intervenes in your work, you MUST log it immediately using `crosslink intervene`. Driver interventions are the highest-signal data for improving agent autonomy.

**You MUST log an intervention when any of these occur:**
- A tool call you proposed is rejected by the driver → `--trigger tool_rejected`
- A hook or policy blocks your tool call → `--trigger tool_blocked`
- The driver redirects your approach ("actually do X instead") → `--trigger redirect`
- The driver provides context you didn't have (requirements, constraints, domain knowledge) → `--trigger context_provided`
- The driver performs an action themselves (push, deployment, etc.) → `--trigger manual_action`
- The driver answers a question that changes your approach → `--trigger question_answered`

```bash
crosslink intervene <issue-id> "Description of what happened" --trigger <type> --context "What you were attempting"
```

**Rules:**
- Log IMMEDIATELY after the intervention occurs, before continuing work.
- Do not skip logging because the intervention seems "small" or "obvious."
- Do not batch multiple interventions into a single log entry.
- If a hook blocks you and provides intervention logging instructions, follow them.

### Pre-Coding Grounding
Before using unfamiliar libraries/APIs:
1. **Verify it exists**: WebSearch to confirm the API
2. **Check the docs**: Real function signatures, not guessed
3. **Use latest versions**: Check for current stable release. This is mandatory. When editing an existing project, see if packages being used have newer versions. If they do inform the human and let them decide if they should be updated.

---

## Priority 3: Workflow

These rules keep work organized and enable context handoff between sessions.

Tracking enforcement is controlled by `tracking_mode` in `.crosslink/hook-config.json` (strict/normal/relaxed).
Detailed tracking instructions are loaded from `.crosslink/rules/tracking-{mode}.md` automatically.

---

## Priority 4: Style

These are preferences, not hard rules. They yield to all higher priorities.

- Write code, don't narrate. Skip "Here is the code" / "Let me..." / "I'll now..."
- Brief explanations only when the code isn't self-explanatory.
- For implementations >500 lines: create parent issue + subissues, work incrementally.
- When conversation is long: create a tracking issue with `crosslink comment` notes for context preservation.
