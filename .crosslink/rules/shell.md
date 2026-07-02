### Shell/Bash Best Practices

#### Script Header
Every script MUST start with a strict preamble:
```bash
#!/usr/bin/env bash
set -o errexit   # -e: Abort on nonzero exitstatus
set -o nounset   # -u: Abort on unbound variable
set -o pipefail  # Don't hide errors within pipes
IFS=$'\n\t'      # Safe word splitting
```

#### Scoping & Immutability
- Global constants: always `readonly`, use `UPPER_CASE`
- Every variable inside functions MUST be `local`
- Use `return` for status codes, `echo` to "return" data via command substitution
- Use guard clauses (early returns) to flatten control flow — max 3 levels of indentation

#### Syntax & Safety
```bash
# GOOD: Double brackets, quoted vars, $() subshells
if [[ -n "${my_var}" ]]; then
    result="$(some_command)"
fi

# BAD: Single brackets, unquoted vars, backticks
if [ -n $my_var ]; then
    result=`some_command`
fi
```
- Always use `[[ ... ]]` for conditionals, not `[ ... ]`
- Use `(( ... ))` for arithmetic
- Use `$(...)` for subshells, never backticks
- Quote EVERYTHING: `"${var}"`, not `$var`
- Check tool dependencies with `command -v`, not `which`

#### Logging & Error Handling
- Use a `die()` function for fatal errors
- All logging (info, warn, error) goes to `stderr` (`>&2`); `stdout` is for data/results only
- Respect XDG: `"${XDG_CONFIG_HOME:-$HOME/.config}"`
- Temp files: use `mktemp -t` or `mktemp -d`, clean up with `trap`

#### Portability
- Avoid `sed -i` (differs on macOS vs Linux) — use a temp file and `mv`
- Use `printf` instead of `echo -e` or `echo -n`
- Test on both bash 3.2 (macOS default) and 5.x (modern Linux)

#### Verification
- All scripts MUST pass `shellcheck` with zero warnings
- Run `shellcheck -x script.sh` before committing
