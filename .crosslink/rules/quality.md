---
name: code-quality
description: Universal code quality and architecture standards that all generated code must follow. Inject this skill on ANY code generation, refactoring, debugging, or review task — regardless of language, framework, or domain. Triggers on requests to write code, build features, create scripts, fix bugs, refactor, review PRs, scaffold projects, or any task where source code is the output. If the deliverable contains code, this skill applies.
---

# Code Quality Standards

Apply all of the following to every piece of code you produce.

## File & Module Structure
- One concept/concern per file. Split at ~200 lines.
- Organize by feature/domain, not by type (`users/` > `models/` + `services/` + `routes/`).
- Small public API per module, hidden internals. If changing internals breaks other modules, boundaries are wrong.

## Functions
- One job per function. If the description needs "and", split it.
- Under 25 lines. Past 40, justify it.
- Guard clauses and early returns — max 3 levels of indentation.
- No side effects in getter-named functions. `get_user()` must not also cache, log, or fire webhooks. Name side effects explicitly.

## Naming
- Names reveal intent. `calculate_monthly_revenue()` not `processData()`.
- No tribal-knowledge abbreviations. `user_manager` not `usr_mgr`.
- Booleans read as questions: `is_active`, `has_permission`, `should_retry`.
- One naming convention per codebase. Pick it and enforce it.

## Separation of Concerns
- **Transport layer**: parse input, call service, format output.
- **Service layer**: orchestrate domain logic, enforce rules.
- **Data layer**: read/write storage, nothing else.
- **Domain layer**: business concepts, validation, rules.
- If a route handler touches the DB, runs business logic, sends emails, and formats responses — refactor immediately.

## Error Handling
- One strategy per codebase. Don't mix exceptions, error codes, and nulls.
- Never swallow errors silently. No bare `except: pass` or empty `catch {}`.
- Fail fast and loud with descriptive messages. Catch problems at the boundary, not three layers deep.
- Use typed/domain-specific errors: `UserNotFoundError` not `Error("something went wrong")`.

## Dependencies
- Inject dependencies, don't reach out and grab them. Functions receive what they need as arguments.
- Depend on abstractions, not concretions. Business logic doesn't know or care about Postgres vs. flat file.

## DRY — Intelligently
- Extract on actual duplication (changes for the same reason), not coincidental similarity.
- Rule of three: tolerate it twice, extract on the third occurrence.
- Premature abstraction is as damaging as duplication.

## Configuration
- No hardcoded strings, URLs, ports, timeouts, or thresholds in logic.
- Extract to named constants, config, or env vars.
- If a value might change or its meaning isn't obvious, name it.

## Immutability & Purity
- Default to `const` / `final` / `readonly`. Mutate only with justification.
- Separate pure computation from I/O. Push side effects to the edges.

## Composition Over Inheritance
- Inheritance hierarchies deeper than 2 levels are a smell. Prefer composition, interfaces, or traits.

## Logging
- Structured logging with consistent fields (timestamp, level, correlation ID).
- Appropriate levels — not everything is INFO.
- Useful context: what failed, what input, what state. `"Error occurred"` is worthless.

## Testing
- Test behavior, not implementation. Refactoring internals shouldn't break tests.
- One scenario per test.
- Tests are first-class code — same quality standards apply.

## Code Smells to Block
- **Monolith files**: split by concern from the start.
- **God functions**: 100+ lines doing everything. Break them up.
- **Stringly-typed data**: use enums, types, or structured objects.
- **Comment-heavy code**: rename until *what* is obvious; comments explain *why*.
- **Boolean params**: `createUser(data, true, false, true)` is unreadable. Use named params or option objects.
- **Returning null for errors**: use the language's error mechanism.

## Output Checklist
Before finalizing any code output:
1. Multiple files organized by concern — not one megafile.
2. Every name reveals intent.
3. Consistent error handling pattern throughout.
4. Magic values extracted to named constants.
5. Functions under 25 lines, guard clauses over nesting.
6. Composition over inheritance.
7. Basic test structure included or suggested where warranted.

Single-file output is fine if explicitly requested — still apply all other standards within it.
