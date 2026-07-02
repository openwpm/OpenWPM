---
name: check
description: Use to check on background feature agents launched via /kickoff — running in tmux sessions or docker/podman containers. Reports each agent's state (Working / Idle / Waiting / Done / Error), captures recent output, and offers next-step commands. Trigger when the user says "check on the agent(s)", "how's the kickoff going", or names a `feat-*` / `crosslink-task-*` session.
---

# Check — status of background feature agents

The user optionally provides an agent name (e.g. `crosslink-task-add-batch-retry` or `feat-add-batch-retry`). If no name is given, check **all** active feature agents (both containers and tmux sessions) and report a summary for each.

## 1. Identify agents to check

### a. Find container-based agents

1. Get this repo's worktree paths: `git worktree list --porcelain | grep '^worktree ' | sed 's/^worktree //'` (`crosslink kickoff` isolates each agent in a git worktree under `.worktrees/`).
2. List crosslink containers: `docker ps -a --filter label=crosslink-agent=true --format '{{.Names}} {{.Status}} {{.Label "crosslink-task"}}' 2>/dev/null`
3. Match containers to this repo: for each container, check if its `crosslink-task` label value matches any of this repo's worktree directory names (the last path component)
4. If the user provided a name starting with `crosslink-task-`, filter to that specific container

### b. Find tmux-based agents

1. Get `feat-*` tmux sessions: `tmux list-sessions -F '#{session_name} #{session_path}' 2>/dev/null | grep '^feat-'`
2. Only include sessions whose `session_path` matches one of this repo's worktree paths
3. If the user provided a name starting with `feat-`, filter to that specific session

If no agents found in either mode, report "No active feature agents for this repo."

## 2. For each agent, perform these checks

### For container-based agents

#### a. Check the sentinel file

Get the worktree path by matching the container's `crosslink-task` label to a worktree directory name from `git worktree list`.

- Check: `cat <worktree-path>/.kickoff-status 2>/dev/null`
- If it contains `DONE`, mark as finished.
- If it contains `CI_FAILED`, mark as CI failure.

#### b. Check container status

```bash
docker inspect --format '{{.State.Status}} (exit {{.State.ExitCode}})' <container-name>
```

Possible states: `running`, `exited` (check exit code), `restarting`, `paused`.

#### c. Capture recent output

```bash
docker logs --tail 80 <container-name> 2>&1
```

#### d. Analyze state

- **Working**: Container status is `running`, no sentinel file, recent tool calls visible in logs
- **Idle**: Container is `running` but no recent output changes — may be thinking or waiting for API
- **Error**: Container `exited` with non-zero exit code, or error messages in recent logs
- **Done**: Sentinel file says `DONE`, or container exited with code 0
- **CI Failed**: Sentinel file says `CI_FAILED`

### For tmux-based agents

#### a. Check the sentinel file

Get the worktree path for this session from tmux: `tmux display-message -t <session-name> -p '#{session_path}'`. Alternatively, match the session name to a feature branch in `git worktree list`.

- Check if `.kickoff-status` exists in the worktree: `cat <worktree-path>/.kickoff-status 2>/dev/null`
- If it contains `DONE`, mark this session as finished.

#### b. Capture the terminal state

```bash
tmux capture-pane -t <session-name> -p -S -80
```

This captures the last ~80 lines of visible output.

#### c. Analyze state

Read the captured output and determine the agent's current state:

- **Working**: Tool calls in progress, code being written/read
- **Waiting for input**: A question or prompt is displayed (look for `?`, option lists, or input prompts)
- **Error/stuck**: Error messages, repeated failures, or no recent activity
- **Completed**: The sentinel file says DONE, or the claude process has exited

## 3. Report

When checking **multiple agents**, use a compact table format with a backend indicator:

```
Feature Agents:

  crosslink-task-add-retry    [container]  Working    Implementing retry logic in _sources.py
  crosslink-task-fix-lens     [container]  Done       All changes committed and reviewed
  feat-new-cli-cmd            [tmux]       Waiting    Asking about CLI argument format
```

When checking a **single agent**, use the detailed format:

```
Agent:    <name>
Backend:  <container|tmux>
Status:   <Working | Idle | Waiting | Done | Error>

<2-3 sentence summary of what the agent is currently doing or has accomplished>
```

For container agents, also show resource usage:

```bash
docker stats --no-stream --format '  CPU: {{.CPUPerc}}  Memory: {{.MemUsage}}' <container-name> 2>/dev/null
```

## 4. Offer actions

### For container agents

- **If working/idle**: "Check back later, or view live logs: `crosslink container logs <name> -f`"
- **If done**: "Agent finished. Review the changes: `cd <worktree-path> && git log --oneline <base-branch>..HEAD`"
- **If error**: Show the relevant error output. Suggest: "Debug with: `crosslink container shell <name>` or view full logs: `crosslink container logs <name> --tail 500`"
- **If exited (non-zero)**: "Container exited with error. View logs: `crosslink container logs <name>`. Restart with: `crosslink container kill <name> && crosslink container start <worktree-path>`"

### For tmux agents

- **If working**: "Check back later, or attach directly: `tmux attach -t <name>`"
- **If waiting for input**: Read the question, and ask the user what to answer. If the user provides an answer, send it: `tmux send-keys -t <session-name> "<response>" Enter`
- **If done**: "Agent finished. Review the changes: `cd <worktree-path> && git log --oneline <base-branch>..HEAD`"
- **If error**: Show the relevant error output and suggest the user attach to debug: `tmux attach -t <name>`

## Constraints

- Do not modify any files in the worktree — this is a read-only check.
- Do not kill containers or tmux sessions unless the user explicitly asks.
- When relaying a user's answer to a waiting tmux prompt, send exactly what the user provides — do not embellish or modify.
