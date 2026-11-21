#!/usr/bin/env bash
#
# PostToolUse hook: format and lint each file Claude edits, using the
# project's own tools. Replaces the old `linter` subagent, so routine
# cleanup costs no model tokens.
#
# - Auto-fixes what the tools can fix (formatting, import order, unused imports).
# - Anything left over goes back to Claude on stderr with exit 2, trimmed to
#   20 lines of at most 300 characters, so it can fix it.
# - A tool runs only when the project has installed it AND configured it.
#   Nothing is downloaded: no bare `npx`, no `uv run` (which can sync).
# - It runs the project's own tooling and config files (node_modules/.bin,
#   .venv, eslint.config.js, ...), so only use it in repos you trust.
#
# Wired up in .claude/settings.json. Needs bash; `jq` or `python3` to read
# the hook input. Tested on Linux; macOS should work; on Windows use WSL.
# Add languages in the case statement below.

set -u

input=$(cat)
if command -v jq >/dev/null 2>&1; then
    file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
elif command -v python3 >/dev/null 2>&1; then
    file=$(printf '%s' "$input" | python3 -I -c \
        'import json,sys; print((json.load(sys.stdin).get("tool_input") or {}).get("file_path") or "")' 2>/dev/null)
else
    echo "lint hook: needs jq or python3; skipping" >&2
    exit 0
fi

# Resolve a path to its physical location (follows symlinks and ..).
# Portable: no `realpath -e`, which older macOS lacks.
physical() {
    local dir base
    dir=$(CDPATH='' cd -- "$(dirname -- "$1")" 2>/dev/null && pwd -P) || return 1
    base=$(basename -- "$1")
    if [ -L "$dir/$base" ]; then
        local target
        target=$(readlink -- "$dir/$base") || return 1
        case "$target" in /*) ;; *) target="$dir/$target" ;; esac
        physical "$target"
    else
        printf '%s/%s\n' "$dir" "$base"
    fi
}

root=$(CDPATH='' cd -- "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null && pwd -P) || exit 0

# Only real files that physically live inside the project.
[ -n "$file" ] && [ -f "$file" ] || exit 0
file=$(physical "$file") || exit 0
case "$file" in "$root"/*) ;; *) exit 0 ;; esac
CDPATH='' cd -- "$root" || exit 0

problems=""
note() { problems+="$1"$'\n'; }

# A project-local Node tool from node_modules/.bin, if installed.
nodebin() { [ -x "node_modules/.bin/$1" ] && echo "node_modules/.bin/$1"; }
# True if any of the given paths exists (globs allowed).
has() { local f; for f in "$@"; do [ -e "$f" ] && return 0; done; return 1; }
# True if package.json has the given top-level key (e.g. a "prettier" config
# block), not just a dependency of that name.
pkg_has() {
    [ -f package.json ] || return 1
    if command -v jq >/dev/null 2>&1; then
        jq -e --arg k "$1" 'has($k)' package.json >/dev/null 2>&1
    elif command -v python3 >/dev/null 2>&1; then
        python3 -I -c 'import json,sys; sys.exit(0 if sys.argv[1] in json.load(open("package.json")) else 1)' "$1" 2>/dev/null
    else
        return 1
    fi
}

has_biome()    { has biome.json biome.jsonc; }
has_prettier() { has .prettierrc .prettierrc.* prettier.config.* || pkg_has prettier; }
has_eslint()   { has eslint.config.* .eslintrc .eslintrc.* || pkg_has eslintConfig; }

# ruff: the project's own copy in .venv if there is one; otherwise ruff on
# PATH, but only when the project configures ruff (so a project that uses
# black or flake8 isn't reformatted).
ruff_bin() {
    if [ -x .venv/bin/ruff ]; then echo .venv/bin/ruff
    elif command -v ruff >/dev/null 2>&1 &&
         { has ruff.toml .ruff.toml || { [ -f pyproject.toml ] && grep -q '^\[tool\.ruff' pyproject.toml; }; }
    then echo ruff
    fi
}

# Biome replaces prettier + eslint when the project configures it.
js_tools() {
    if has_biome && b=$(nodebin biome); then
        out=$("$b" check --write --no-errors-on-unmatched "$file" 2>&1) || note "$out"
        return
    fi
    if has_prettier && p=$(nodebin prettier); then
        out=$("$p" --write --log-level warn "$file" 2>&1) || note "$out"
    fi
    if [ "${1:-}" = lint ] && has_eslint && e=$(nodebin eslint); then
        # --no-warn-ignored stops ignored files failing, but only flat config
        # (eslint.config.*) accepts it; legacy .eslintrc rejects the flag.
        # (A plain string, not an array: an empty array under set -u aborts
        # on bash < 4.4, which includes stock macOS bash.)
        local quiet=""
        has eslint.config.* && quiet="--no-warn-ignored"
        # $quiet is empty or one flag, so it's left unquoted on purpose.
        # shellcheck disable=SC2086
        "$e" --fix $quiet "$file" >/dev/null 2>&1
        # shellcheck disable=SC2086
        out=$("$e" $quiet "$file" 2>&1) || note "$out"
    fi
}

case "$file" in
    *.py)
        if r=$(ruff_bin) && [ -n "$r" ]; then
            "$r" format --quiet "$file" >/dev/null 2>&1
            "$r" check --fix --quiet "$file" >/dev/null 2>&1
            out=$("$r" check --quiet "$file" 2>&1) || note "$out"
        fi
        ;;
    *.js|*.jsx|*.ts|*.tsx|*.mjs|*.cjs|*.mts|*.cts|*.vue|*.svelte)
        js_tools lint
        ;;
    *.json|*.jsonc|*.css|*.scss|*.html|*.yml|*.yaml)
        js_tools
        ;;
    *.go)
        if command -v gofmt >/dev/null 2>&1; then
            out=$(gofmt -w "$file" 2>&1) || note "$out"
        fi
        ;;
    *.rs)
        if command -v rustfmt >/dev/null 2>&1; then
            out=$(rustfmt --quiet "$file" 2>&1) || note "$out"
        fi
        ;;
    *.tf)
        if command -v terraform >/dev/null 2>&1; then
            out=$(terraform fmt "$file" 2>&1) || note "$out"
        fi
        ;;
    *.sh)
        if command -v shellcheck >/dev/null 2>&1; then
            out=$(shellcheck "$file" 2>&1) || note "$out"
        fi
        ;;
esac

if [ -n "$problems" ]; then
    {
        echo "Lint issues left in $file after auto-fix:"
        printf '%s' "$problems" | head -n 20 | cut -c1-300
        [ "$(printf '%s' "$problems" | wc -l)" -gt 20 ] && echo "(truncated)"
    } >&2
    exit 2
fi
exit 0
