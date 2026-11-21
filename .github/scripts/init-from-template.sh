#!/usr/bin/env bash
#
# First-run setup for a repo created from this template. Fills in the
# template's placeholders, installs the git hooks, and points you at the
# remaining steps. Run it once from a fresh clone; it's safe to re-run.
#
#   .github/scripts/init-from-template.sh            show what would change
#   .github/scripts/init-from-template.sh --apply    make the changes
#   options: --name "Project Name"   default: the repo's name
#            --owner HANDLE          CODEOWNERS owner, a user or org/team; default: your gh login
#            --author "Your Name"    LICENSE copyright holder; default: git config user.name
#            --skip-template-check   apply without gh confirming this isn't the template
#
# It edits only files git tracks (never symlinks or untracked files), so
# `git diff` shows every change and `git checkout -- <file>` undoes it. It
# also sets core.hooksPath. It refuses to apply in the template itself: gh
# must confirm the repo isn't a template, or you pass --skip-template-check.
#
# Needs: git and python3; gh for the defaults and the template check.

set -euo pipefail

usage() { sed -n '3,12p' "$0" | sed 's/^# \{0,1\}//'; }

NAME=""; OWNER=""; AUTHOR=""; APPLY=0; SKIP_TEMPLATE_CHECK=0
while [ $# -gt 0 ]; do
    case "$1" in
        --name) NAME=${2:?--name needs a value}; shift 2 ;;
        --owner) OWNER=${2:?--owner needs a value}; shift 2 ;;
        --author) AUTHOR=${2:?--author needs a value}; shift 2 ;;
        --apply) APPLY=1; shift ;;
        --skip-template-check) SKIP_TEMPLATE_CHECK=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
done

ROOT=$(cd "$(dirname "$0")/../.." && pwd -P)
cd "$ROOT"
command -v git >/dev/null || { echo "needs git" >&2; exit 1; }
command -v python3 >/dev/null || { echo "needs python3" >&2; exit 1; }
HAVE_GH=0
if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then HAVE_GH=1; fi

# Never rewrite the template's own placeholders. Fail closed: if gh can't
# confirm this isn't the template, refuse to apply unless told to skip.
TEMPLATE_STATE=unknown
if [ "$HAVE_GH" = 1 ]; then
    TEMPLATE_STATE=$(gh repo view --json isTemplate -q 'if .isTemplate then "template" else "not-template" end' 2>/dev/null || echo unknown)
fi
if [ "$TEMPLATE_STATE" = template ]; then
    echo "This repo is the template itself; run this in a repo created from it." >&2
    exit 1
fi
if [ "$TEMPLATE_STATE" = unknown ] && [ "$SKIP_TEMPLATE_CHECK" = 0 ]; then
    if [ "$APPLY" = 1 ]; then
        echo "Can't confirm this isn't the template (gh is missing, signed out, or couldn't read the repo)." >&2
        echo "Sign in with 'gh auth login', or re-run with --skip-template-check if you're sure." >&2
        exit 1
    fi
    echo "Note: can't confirm this isn't the template; --apply will need gh or --skip-template-check."
    echo
fi

if [ -z "$NAME" ]; then
    if [ "$HAVE_GH" = 1 ]; then NAME=$(gh repo view --json name -q .name 2>/dev/null || true); fi
    [ -n "$NAME" ] || NAME=$(basename "$ROOT")
fi
if [ -z "$OWNER" ] && [ "$HAVE_GH" = 1 ]; then
    OWNER=$(gh api user -q .login 2>/dev/null || true)
fi
[ -n "$AUTHOR" ] || AUTHOR=$(git config user.name || true)
YEAR=$(date +%Y)

# Every value must be one line: they go into Markdown, LICENSE and CODEOWNERS.
case "$NAME$OWNER$AUTHOR" in
    *$'\n'*|*$'\r'*) echo "--name, --owner and --author must each be one line" >&2; exit 2 ;;
esac
OWNER=${OWNER#@}
if [ -n "$OWNER" ] && ! [[ "$OWNER" =~ ^[A-Za-z0-9][A-Za-z0-9-]*(/[A-Za-z0-9][A-Za-z0-9._-]*)?$ ]]; then
    echo "--owner must be a GitHub user or org/team, e.g. octocat or my-org/platform" >&2; exit 2
fi

if [ "$APPLY" = 1 ]; then MODE="applying"; else MODE="dry run: nothing is changed; add --apply to apply"; fi
echo "Setting up \"$NAME\", $MODE"
echo

# Replace placeholders in tracked files. Exits 3 if a placeholder is (or
# would be) left because a value is missing; any other non-zero is an error.
status=0
NAME=$NAME OWNER=$OWNER AUTHOR=$AUTHOR YEAR=$YEAR APPLY=$APPLY ROOT=$ROOT python3 -I - <<'PY' || status=$?
import os, re, subprocess, sys
from pathlib import Path

env = os.environ
root = Path(env["ROOT"])
apply = env["APPLY"] == "1"
missing = []

def safe_to_edit(rel):
    """A regular file git tracks, inside the repo, reached through no symlink."""
    path = root / rel
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "--", rel], cwd=root, capture_output=True).returncode == 0
    if not tracked or not path.is_file():
        return False
    parts = [root.joinpath(*Path(rel).parts[: i + 1]) for i in range(len(Path(rel).parts))]
    return not any(p.is_symlink() for p in parts)

def edit(rel, changes, needs=None):
    if not (root / rel).exists():
        return
    if not safe_to_edit(rel):
        print(f"  - {rel}: skipped (not a tracked regular file)")
        return
    path = root / rel
    with open(path, encoding="utf-8", newline="") as f:  # keep CRLF files CRLF
        text = f.read()
    new = text
    for pattern, value in changes:
        new = re.sub(pattern, lambda m: value, new)
    if new == text:
        print(f"  ✓ {rel}: nothing to fill in")
        return
    if needs and not env[needs]:
        missing.append(f"{rel} (pass --{needs.lower()})")
        print(f"  ! {rel}: placeholder left; pass --{needs.lower()}")
        return
    if apply:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new)
    print(f"  {'✓' if apply else '→'} {rel}: filled in")

print("Placeholders:")
for doc in ("AGENTS.md", "docs/prd/v1.0-prd.md", "docs/build-guides/v1.0-build-guide.md"):
    edit(doc, [(r"\[Project Name\]", env["NAME"])])
edit("LICENSE", [(r"\[year\]", env["YEAR"]), (r"\[your name\]", env["AUTHOR"])], needs="AUTHOR")
edit(
    ".github/CODEOWNERS",
    [
        (r"(?m)^# Replace YOUR-GITHUB-USERNAME[^\n]*\n# for team ownership\. ", "# "),
        (r"@YOUR-GITHUB-USERNAME", "@" + env["OWNER"]),
    ],
    needs="OWNER",
)
if missing:
    print("\n  Still to fill in: " + "; ".join(missing))
sys.exit(3 if missing else 0)
PY
if [ "$status" != 0 ] && [ "$status" != 3 ]; then
    echo "Stopped: filling in the placeholders failed (exit $status)." >&2
    exit "$status"
fi
echo

echo "Git hooks:"
if [ "$(git config core.hooksPath || true)" = .githooks ]; then
    echo "  ✓ installed"
elif [ "$APPLY" = 1 ]; then
    if sh .githooks/setup-hooks.sh >/dev/null; then
        echo "  ✓ installed (core.hooksPath = .githooks)"
    else
        echo "  ! not installed: run .githooks/setup-hooks.sh to see why"
        [ "$status" != 0 ] || status=4
    fi
else
    echo "  → install (.githooks/setup-hooks.sh)"
fi
echo

cat <<'EOF'
Next:
  1. Review and commit:  git diff, then commit on a branch and open a PR
     (main isn't protected yet, but the hooks now check branch names).
  2. Protect main and set the repo defaults, once CI has reported
     toolkit-checks:    .github/scripts/apply-repo-defaults.sh  (then --apply)
  3. Fill in AGENTS.md (architecture, conventions) and the PRD.
  4. Optional: copy permissions you need from .claude/settings.example.jsonc
     into .claude/settings.json.
EOF

if [ "$status" = 3 ]; then
    echo; echo "Not finished: some placeholders still need a value (marked !). Re-run with the options shown."
fi
if [ "$APPLY" = 0 ]; then echo; echo "Re-run with --apply to make these changes."; fi
exit "$status"
