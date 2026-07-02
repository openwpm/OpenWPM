---
name: preflight
description: Use BEFORE implementing code in a crosslink-tracked project — loads `.crosslink/rules/global.md`, the language rules for detected manifests, the project rules, and the active `tracking-<mode>.md`. Replaces the heavy context that would otherwise be re-injected on every prompt. Trigger when the user says "preflight", "load the rules", "ground yourself", or before starting a fresh implementation session.
---

# Preflight — load rules and grounding context

You are preparing to implement code. Load the project's rules and grounding context so you have the right constraints in mind. This replaces the heavy context that would otherwise be injected on every prompt.

## 1. Read core rules

Read the project's global rules file:

```
Read .crosslink/rules/global.md
```

## 2. Detect active languages and load rules

Check for project manifests and load the corresponding rule files:

| Manifest | Language | Rule file |
|----------|----------|-----------|
| `Cargo.toml` | Rust | `.crosslink/rules/rust.md` |
| `package.json` | JavaScript | `.crosslink/rules/javascript.md` |
| `tsconfig.json` | TypeScript | `.crosslink/rules/typescript.md` |
| `pyproject.toml` / `requirements.txt` | Python | `.crosslink/rules/python.md` |
| `go.mod` | Go | `.crosslink/rules/go.md` |
| `pom.xml` / `build.gradle` | Java | `.crosslink/rules/java.md` |
| `Gemfile` | Ruby | `.crosslink/rules/ruby.md` |
| `composer.json` | PHP | `.crosslink/rules/php.md` |
| `Package.swift` | Swift | `.crosslink/rules/swift.md` |
| `mix.exs` | Elixir | `.crosslink/rules/elixir.md` |

Also load `.crosslink/rules/elixir-phoenix.md` if `mix.exs` contains `:phoenix`.

Only read rule files for languages actually detected in this project.

## 3. Read project-specific and tracking rules

```
Read .crosslink/rules/project.md
```

Check the tracking mode from hook-config.json and read the matching tracking rules:

```bash
crosslink config get tracking_mode
```

Then read `.crosslink/rules/tracking-<mode>.md` (e.g., `tracking-strict.md`).

## 4. Scan project tree

Build spatial awareness of the project (max depth 3, max 50 entries):

```bash
find . -maxdepth 3 -not -path '*/.git/*' | head -50
```

## 5. Check dependency versions

Read the primary manifest file (e.g., `Cargo.toml`, `package.json`) to ground yourself on actual dependency versions. Do not guess versions.

## 6. Print summary

Print a brief summary of what was loaded:

```
Preflight loaded:
  - Global rules
  - Language rules: Rust, TypeScript
  - Tracking mode: strict
  - Project tree scanned (N entries)
  - Dependencies: Cargo.toml (N deps)
```

You are now grounded. Proceed with implementation.
