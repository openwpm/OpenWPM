---
name: crosslink-guide
description: Use when working in any repo that has `.crosslink/` and the workflow involves issue tracking, sessions, locks, swarms, kickoff, or knowledge pages. Reference for the full crosslink CLI surface plus the harness footguns (auto-CHANGELOG entries on issue close, --no-changelog flag, label-based skip rules, session lifecycle). Trigger when the user mentions crosslink commands, when the crosslink-behavioral-guard hook fires asking for issue creation, or when a session needs to be started/ended/handed off.
---

# Crosslink Guide

Crosslink is a local-first issue tracker designed for AI-assisted development. Data lives in `.crosslink/issues.db` (SQLite); state syncs via the `crosslink/hub` git branch. Read this skill when the workflow involves any crosslink command, when the `crosslink-behavioral-guard` hook fires, or when starting/ending a session.

## Hook awareness — the things that bite

These are not in the CLI `--help` output but matter constantly:

### `crosslink issue close` auto-appends to CHANGELOG.md

Closing an issue triggers a hook that adds a one-line entry to the workspace's `CHANGELOG.md` under `### Changed` (or `### Fixed` for `bug`-labeled issues). For meta-work that shouldn't be in the release notes (skill edits, settings tweaks, CHANGELOG cleanup itself), this is pollution.

**Fix:** pass `--no-changelog` to skip:

```bash
crosslink issue close 643 --no-changelog
```

The recursive trap: if you close an issue without `--no-changelog`, then close a follow-up issue to clean up the entry, *that* close also auto-appends. Either use `--no-changelog` from the start, or remove the line directly via `Edit` rather than another `crosslink close`.

### `crosslink quick` doesn't take `--no-changelog`

Only `close` triggers the auto-CHANGELOG hook. `quick` and `create` do not, so no `--no-changelog` flag exists on them.

### Session must be started before `session work <id>` succeeds

```
crosslink session work 642
# Error: No active session. Use 'crosslink session start' first.
```

Always pair them:

```bash
crosslink session start && crosslink session work <id>
```

### `--work` flag on `quick` is silently a no-op without an active session

```
crosslink quick "..." -p high -l bug
# WARN: --work specified but no active session
```

The issue gets created but isn't marked as the current focus. Same fix: `session start` first.

### Labels matter for hook routing

Bug-labeled issues land under `### Fixed` in CHANGELOG; everything else under `### Changed`. The `chore`, `docs`, `refactor` labels currently do *not* exempt the entry from CHANGELOG (use `--no-changelog`).

## Core workflow

```bash
# 1. Start session (see what the last session handed off)
crosslink session start

# 2. Create or pick an issue to work on
crosslink quick "Title" -p high -l bug                  # create + claim lock + start working
# OR
crosslink issue list -s open                            # see existing issues
crosslink session work <id>                             # pick one

# 3. Document as you work
crosslink issue comment <id> "Approach: ..." --kind plan
crosslink issue comment <id> "Chose X over Y because ..." --kind decision

# 4. End session with handoff notes
crosslink session end --notes "What's done, what's next, blockers"
```

## Issue management

### Creating

```bash
crosslink issue create "Title" -p medium                # basic
crosslink quick "Title" -p high -l bug                  # create + auto-claim lock + work
crosslink subissue <parent-id> "Child title"            # create under a parent
```

### Querying

```bash
crosslink issue list                                    # open issues (default)
crosslink issue list -s all                             # include closed
crosslink issue list -l bug -p high                     # filter by label and priority
crosslink issue search "keyword"                        # full-text
crosslink issue show <id>                               # full details
crosslink issue tree                                    # hierarchy view
crosslink issue next                                    # suggest what to work on
```

### Lifecycle

```bash
crosslink issue update <id> -t "new title" -p high      # update title/priority
crosslink issue close <id>                              # close + add to CHANGELOG
crosslink issue close <id> --no-changelog               # close + skip CHANGELOG
crosslink issue close-all                               # close all matching filters
crosslink issue reopen <id>                             # reopen if needed
crosslink issue delete <id> --force                     # permanent delete
crosslink issue tested <id>                             # mark tests run (resets reminder)
```

### Comments — typed for audit trails

```bash
crosslink issue comment <id> "text" --kind plan         # what you intend to do
crosslink issue comment <id> "text" --kind decision     # why you chose this approach
crosslink issue comment <id> "text" --kind observation  # something you discovered
crosslink issue comment <id> "text" --kind blocker      # what's blocking progress
crosslink issue comment <id> "text" --kind resolution   # how a blocker was resolved
crosslink issue comment <id> "text" --kind result       # what was delivered
```

### Labels and relations

```bash
crosslink issue label <id> bug                          # add label
crosslink issue unlabel <id> bug                        # remove label
crosslink issue block <id> <blocker-id>                 # mark dependency
crosslink issue unblock <id> <blocker-id>               # remove blocking
crosslink issue blocked                                 # show blocked
crosslink issue ready                                   # show unblocked
crosslink issue relate <id1> <id2>                      # link related
crosslink issue related <id>                            # list related
```

### Interventions

For recording when you had to deviate from the planned approach:

```bash
crosslink issue intervene <id> "description" --trigger <type> --context "what you were doing"
```

## Sessions

```bash
crosslink session start                                 # begin work, see last handoff
crosslink session work <id>                             # set current focus
crosslink session status                                # check what you're working on
crosslink session last-handoff                          # show previous session's notes
crosslink session action "did X"                        # breadcrumb before context compression
crosslink session end --notes "context for next session"
```

**Always end with `--notes`.** The next session reads them via `session start` — terse notes there save real reorientation time.

## Locks

Crosslink uses optimistic locking on issues so multiple agents don't collide.

```bash
crosslink locks list                                    # active locks
crosslink locks check <id>                              # is this issue locked?
crosslink locks claim <id>                              # claim
crosslink locks release <id>                            # release
crosslink locks steal <id>                              # take a stale lock (be careful)
```

`crosslink quick` and `crosslink session work` auto-claim. `crosslink issue close` releases.

## Time tracking

```bash
crosslink timer start <id>                              # start
crosslink timer stop                                    # stop current
crosslink timer show                                    # current status
```

## Knowledge base

Shared markdown pages on the `crosslink/knowledge` branch:

```bash
crosslink knowledge add "page-slug" --body "content"
crosslink knowledge show <slug>
crosslink knowledge list
crosslink knowledge edit <slug> --body "new content"
crosslink knowledge remove <slug>
crosslink knowledge search "query"
crosslink knowledge sync                                # pull from remote
crosslink knowledge import <path>                       # bulk import markdown
```

## Kickoff (agent launcher)

```bash
crosslink kickoff run <issue-id>                        # launch agent in worktree
crosslink kickoff launch                                # interactive pipeline wizard
crosslink kickoff status                                # check running
crosslink kickoff logs <id>
crosslink kickoff stop <id>
crosslink kickoff list                                  # all agents (worktrees/tmux/docker)
crosslink kickoff cleanup                               # remove completed/stale
crosslink kickoff graph                                 # branch topology
```

Design-driven workflow:

```bash
crosslink kickoff plan <design-doc>                     # gap analysis vs codebase
crosslink kickoff show-plan <slug>                      # display gap report
crosslink kickoff report <id>                           # spec validation report
```

## Swarm (multi-agent coordination)

```bash
# Lifecycle
crosslink swarm init <design-doc>                       # init from design doc
crosslink swarm status                                  # agents, phases, progress
crosslink swarm resume                                  # reconstruct + show next
crosslink swarm list                                    # active + archived
crosslink swarm archive
crosslink swarm reset

# Phases
crosslink swarm launch                                  # launch all agents for a phase
crosslink swarm gate                                    # run test suite as gate
crosslink swarm checkpoint                              # record after phase done
crosslink swarm merge                                   # merge worktrees into one branch

# Planning
crosslink swarm plan                                    # multi-phase across budget windows
crosslink swarm plan-show
crosslink swarm config                                  # budget params
crosslink swarm estimate                                # wall-clock cost estimate
crosslink swarm harvest                                 # update cost history

# Review pipeline
crosslink swarm review                                  # parallel review agents
crosslink swarm fix                                     # parallel fix agents
crosslink swarm pipeline                                # full review→fix
crosslink swarm review-status
crosslink swarm review-continue
```

## Container execution

```bash
crosslink container build                               # build agent image
crosslink container start <worktree>                    # start for a worktree
crosslink container ps                                  # list running
crosslink container logs <id>                           # stream
crosslink container stop <id>
crosslink container rm <id>
crosslink container kill <id>                           # stop + remove
crosslink container shell <id>                          # exec shell
crosslink container snapshot <id>                       # save as cached image
```

## Agent identity and trust

```bash
# Agent
crosslink agent init                                    # initialize identity
crosslink agent status                                  # show current
crosslink agent prompt <session> "message"              # send to tmux agent
crosslink agent bootstrap                               # bootstrap in new repo

# Trust (signing keys)
crosslink trust approve <fingerprint>
crosslink trust revoke <fingerprint>
crosslink trust list
crosslink trust pending                                 # awaiting approval
crosslink trust check <agent>
```

## Design documents

```bash
crosslink design "feature description"                  # start design session
crosslink design --issue <id>                           # context from crosslink issue
crosslink design --gh-issue <num>                       # context from GitHub issue
crosslink design --continue <slug>                      # resume existing draft
```

## Milestones

```bash
crosslink milestone create "v1.0"
crosslink milestone list
crosslink milestone show <id>
crosslink milestone add <milestone-id> <issue-id>
crosslink milestone remove <milestone-id> <issue-id>
crosslink milestone close <id>
crosslink milestone delete <id>
```

## Archive

```bash
crosslink archive add <id>                              # archive a closed issue
crosslink archive remove <id>                           # unarchive
crosslink archive list
crosslink archive older <days>                          # bulk-archive old closed
```

## Configuration

```bash
crosslink config                                        # interactive walkthrough
crosslink config --preset team                          # team preset
crosslink config --preset solo                          # solo preset
crosslink config show                                   # all values + defaults
crosslink config get <key>
crosslink config set <key> <value>
crosslink config list                                   # keys with descriptions
crosslink config reset
crosslink config diff                                   # drift from defaults
```

## Workflow and diagnostics

```bash
crosslink workflow diff                                 # policy files vs embedded defaults
crosslink workflow trail <id>                           # chronological comment trail
crosslink context measure                               # context injection token cost
crosslink context check                                 # files deployed correctly?
crosslink cpitd scan                                    # scan for code clones
crosslink cpitd status
crosslink cpitd clear
```

## Style syncing

```bash
crosslink style set <repo-url>                          # set house style source
crosslink style sync                                    # pull latest
crosslink style diff                                    # drift from house
crosslink style show                                    # current config
crosslink style unset
```

## Infrastructure

```bash
crosslink init                                          # initialize in a repo
crosslink sync                                          # sync from remote
crosslink compact                                       # event compaction
crosslink prune                                         # prune hub/knowledge history
crosslink export                                        # JSON/markdown export
crosslink import <file>                                 # import from JSON
crosslink daemon start|stop|status                      # background daemon
crosslink migrate to-shared|from-shared|rename-branch   # schema migrations
```

## Integrity / troubleshooting

```bash
crosslink integrity counters --repair                   # fix counter drift
crosslink integrity hydration --repair                  # rehydrate SQLite from JSON
crosslink integrity locks                               # find stale/orphan locks
crosslink integrity schema                              # verify schema version
crosslink integrity layout                              # detect mixed V1/V2 hub layout
crosslink integrity sign-backfill                       # sign unsigned with human key
```

## UI

```bash
crosslink tui                                           # interactive terminal dashboard
crosslink mc                                            # tmux mission control
crosslink serve                                         # web dashboard server
```

## Issue ID formats

- `#42` — hub-synced, positive display ID
- `L3` — local-only (not yet pushed to hub)
- Both formats work everywhere: `crosslink show 42`, `crosslink show L3`

## Priorities

`critical` > `high` > `medium` > `low`

## Global flags (work on most subcommands)

- `--quiet` / `-q` — minimal output (for scripting)
- `--json` — machine-readable output
- `--log-level <error|warn|info|debug|trace>` — diagnostic output level
- `--log-format <text|json>` — log format

## When meta-work shouldn't go in CHANGELOG

Tag the close with `--no-changelog` for any of these:
- Skill edits in `~/.claude/`
- Settings.json changes
- CHANGELOG cleanup itself
- Documentation-only PRs that don't ship to users
- Issue tracker hygiene (closing audit/tracking issues whose deliverables already shipped)
- Any `chore`-labeled work (the auto-routing currently doesn't exempt these)

If the auto-entry already landed, remove it via `Edit` on `CHANGELOG.md` directly. Don't open another issue to "fix the CHANGELOG entry" — that just adds another entry. The recursion is real.
