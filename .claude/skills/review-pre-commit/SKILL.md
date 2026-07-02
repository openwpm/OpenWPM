---
name: review-pre-commit
description: Use as a pre-commit quality gate — review the working diff for stub patterns (TODO/FIXME/`unimplemented!()`/`todo!()`), debug leftovers (`dbg!`, stray `console.log`/`println!`, commented-out code), then run the project's lint, format, and test suites and verify the active crosslink issue is documented. Prints a PASS/FAIL checklist and hands off to `commit`. Trigger when the user says "review my changes", "/review", "ready to commit?", or asks for a final pass before committing.
---

# Review — pre-commit quality gate

You are about to commit. Run through this structured review to catch issues before they land.

## 1. Review full diff

```bash
jj diff
```

Read through every change. Look for:

- Correctness: does the logic do what it should?
- Edge cases: are boundary conditions handled?
- Security: any injection, hardcoded secrets, or unsafe patterns?

## 2. Scan for stub patterns

Search the diff for patterns that indicate incomplete work:

- `TODO`, `FIXME`, `HACK`, `XXX`
- `pass` (Python), `unimplemented!()` / `todo!()` (Rust)
- `throw new Error("not implemented")`
- Empty function bodies or placeholder returns
- `...` as implementation

If found: fix them now. Do not commit stubs.

## 3. Check for debug leftovers

Search for debug code that shouldn't be committed:

- `dbg!()` (Rust)
- `console.log` used for debugging (not logging)
- `print(` / `println!` used for debugging
- Commented-out code blocks (more than 2 consecutive commented lines)

If found: remove them.

## 4. Run lint and format checks

Detect the project's toolchain and run the appropriate checks:

**Rust** (if `Cargo.toml` exists):

```bash
cargo clippy -- -D warnings
cargo fmt --check
```

**Python** (OpenWPM — black/isort/mypy via pre-commit):

```bash
jj-precommit
```

**Extension** (TypeScript — run from the `Extension/` dir; root `package.json` has no lint script):

```bash
cd Extension && npm run lint
```

**Go** (if `go.mod` exists):

```bash
go vet ./...
gofmt -l .
```

**Elixir** (if `mix.exs` exists):

```bash
mix format --check-formatted
mix credo --strict
```

Fix any issues found before proceeding.

## 5. Run test suite

Run the project's test suite:

- Python (OpenWPM): `pytest` (markers `pyonly` / `slow`; spins a local HTTP server + real Firefox)
- Extension: `cd Extension && npm test` (build + lint)
- Rust: `cargo test`
- Go: `go test ./...`
- Elixir: `mix test --seed 0`

All tests must pass before committing.

## 6. Verify crosslink issue documentation

Check that the active crosslink issue has appropriate documentation:

```bash
crosslink session status
```

If working on an issue, verify it has a plan comment and will get a result comment:

```bash
crosslink issue show <issue-id>
```

## 7. Print checklist

Print a pass/fail summary:

```
Review checklist:
  [PASS] No stub patterns
  [PASS] No debug leftovers
  [PASS] Lint clean
  [PASS] Format clean
  [PASS] Tests pass
  [PASS] Issue documented

Ready to commit. Proceeding to commit skill.
```

If any items fail, fix them first, then re-run the failed checks.

Once all checks pass, hand off to the `commit` skill.
