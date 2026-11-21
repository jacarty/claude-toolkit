#!/usr/bin/env bash
#
# Apply this template's GitHub repo defaults to a repo created from it.
# "Use this template" copies files, not settings, so a new repo starts with
# no branch protection. Run this once after creating it, then again whenever
# .github/rulesets/ changes.
#
#   .github/scripts/apply-repo-defaults.sh                 show what would change (read-only)
#   .github/scripts/apply-repo-defaults.sh --apply         apply it
#   options: --repo OWNER/NAME   default: the repo of the current checkout
#            --approvals N       required PR approvals (default 0, solo-friendly; 1+ for teams)
#
# What it sets, in this order:
#   - merge settings: merge commits and squash (no rebase), and head branches
#     deleted automatically on merge (first, because the ruleset only allows
#     methods the repo allows)
#   - every ruleset in .github/rulesets/*.json, created or updated in place by
#     name (main-protection: PRs only, merge or squash, no force-push or
#     deletion, toolkit-checks must pass, admins may bypass on PRs only)
#   - secret scanning and push protection
#   - Dependabot alerts and security updates
#   - private vulnerability reporting (the form SECURITY.md links to; public
#     repos only)
#
# Apply the ruleset only once the default branch's CI reports every check it
# requires (for a new repo, after its first push); otherwise open PRs wait
# for a check that never runs.
#
# Each setting is applied on its own, and what GitHub refuses is reported.
# Rulesets on private repos need GitHub Pro, Team or Enterprise; secret
# scanning on private repos needs GitHub Secret Protection, so there a refusal
# is a note, not a failure. It never deletes rulesets it doesn't manage.
#
# Needs: gh (signed in, with admin on the repo) and python3.

set -euo pipefail

usage() { sed -n '3,11p' "$0" | sed 's/^# \{0,1\}//'; }

REPO=""; APPROVALS=0; APPLY=0
while [ $# -gt 0 ]; do
    case "$1" in
        --repo) REPO=${2:?--repo needs OWNER/NAME}; shift 2 ;;
        --approvals) APPROVALS=${2:?--approvals needs a number}; shift 2 ;;
        --apply) APPLY=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
done
case "$APPROVALS" in ''|*[!0-9]*) echo "--approvals must be a whole number" >&2; exit 2 ;; esac

ROOT=$(cd "$(dirname "$0")/../.." && pwd -P)
command -v gh >/dev/null || { echo "needs the GitHub CLI (gh)" >&2; exit 1; }
command -v python3 >/dev/null || { echo "needs python3" >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "gh isn't signed in: run 'gh auth login'" >&2; exit 1; }

[ -n "$REPO" ] || REPO=$(cd "$ROOT" && gh repo view --json nameWithOwner -q .nameWithOwner)
INFO=$(gh api "repos/$REPO") || { echo "can't read $REPO" >&2; exit 1; }

# A dotted field from the repo JSON: True/False for booleans, JSON for
# objects, lists and null, so a missing or null parent never crashes.
field() {
    printf '%s' "$INFO" | python3 -I -c '
import json, sys
value = json.load(sys.stdin)
for key in sys.argv[1].split("."):
    value = value.get(key) if isinstance(value, dict) else None
print(json.dumps(value) if value is None or isinstance(value, (dict, list)) else value)' "$1"
}

if [ "$(field permissions.admin)" != "True" ]; then
    echo "you need admin on $REPO to change its settings" >&2; exit 1
fi
if [ "$(field private)" = True ]; then PRIVATE=1; VISIBILITY=private; else PRIVATE=0; VISIBILITY=public; fi

if [ "$APPLY" = 1 ]; then MODE="applying"; else MODE="dry run: nothing is changed; add --apply to apply"; fi
echo "Repo: $REPO ($VISIBILITY), $MODE"
echo

FAILED=0
ok()   { echo "  ✓ $*"; }
plan() { echo "  → $*"; }
note() { echo "  - $*"; }
warn() { echo "  ! $*"; }

# GitHub's error message from gh's output: the JSON body, then gh's own line.
github_message() {
    python3 -I -c '
import json, sys
text = sys.stdin.read()
start = text.find("{")
try:
    print(json.JSONDecoder().raw_decode(text[start:])[0].get("message", "").strip() or text.strip())
except Exception:
    print(text.strip().splitlines()[-1] if text.strip() else "unknown error")'
}

# write WHAT BODY [optional] -- GH_API_ARGS...
# Runs one gh api write (BODY on stdin when it isn't empty). On failure it
# reports GitHub's message and carries on, counting it as a failure. With
# `optional`, a refusal because the feature isn't in the repo's plan is only
# a note; any other error (permissions, timeouts, 5xx) is still a failure.
# It runs in the current shell, so FAILED sticks.
write() {
    local what=$1 body=$2 optional=0 out msg
    shift 2
    if [ "$1" = optional ]; then optional=1; shift; fi
    [ "$1" = -- ] && shift
    if [ -n "$body" ]; then
        out=$(printf '%s' "$body" | gh api "$@" --input - 2>&1) && { ok "$what"; return; }
    else
        out=$(gh api "$@" 2>&1) && { ok "$what"; return; }
    fi
    msg=$(printf '%s' "$out" | github_message)
    if [ "$optional" = 1 ] && printf '%s' "$msg" | grep -qiE 'not available|advanced security|secret protection|upgrade|purchase|not enabled for this'; then
        note "$what: not available here ($msg)"
    else
        warn "$what: not applied: $msg"
        FAILED=1
    fi
}

# The current security settings, for the dry run.
security_now() {
    local settings alerts pvr
    settings=$(field security_and_analysis | python3 -I -c '
import json, sys
data = json.load(sys.stdin) or {}
print(", ".join(k + "=" + str(v.get("status")) for k, v in data.items() if isinstance(v, dict)) or "not reported")')
    if gh api "repos/$REPO/vulnerability-alerts" >/dev/null 2>&1; then alerts=on; else alerts=off; fi
    pvr=$(gh api "repos/$REPO/private-vulnerability-reporting" -q 'if .enabled then "on" else "off" end' 2>/dev/null || echo unknown)
    echo "$settings, dependabot_alerts=$alerts, private_vulnerability_reporting=$pvr"
}

# ── Merge settings (before the ruleset, which only allows enabled methods) ──
echo "Merge settings:"
echo "  now: squash=$(field allow_squash_merge) merge commits=$(field allow_merge_commit) rebase=$(field allow_rebase_merge) delete branch on merge=$(field delete_branch_on_merge)"
if [ "$APPLY" = 0 ]; then
    plan "merge commits and squash, no rebase; delete head branches on merge"
else
    write "merge commits and squash, no rebase; delete head branches on merge" "" -- -X PATCH "repos/$REPO" \
        -F allow_squash_merge=true -F allow_merge_commit=true -F allow_rebase_merge=false \
        -F delete_branch_on_merge=true
fi
echo

# ── Rulesets ─────────────────────────────────────────────────────────────
echo "Rulesets (.github/rulesets/):"
if ! EXISTING=$(gh api --paginate "repos/$REPO/rulesets?includes_parents=false" \
        -q '.[] | select(.source_type == "Repository") | "\(.name)\t\(.id)"' 2>&1); then
    warn "can't list the repo's rulesets, so none were changed: $(printf '%s' "$EXISTING" | github_message)"
    FAILED=1
else
    shopt -s nullglob
    for file in "$ROOT"/.github/rulesets/*.json; do
        body=$(APPROVALS=$APPROVALS python3 -I - "$file" <<'PY'
import json, os, sys
ruleset = json.load(open(sys.argv[1], encoding="utf-8"))
for rule in ruleset.get("rules", []):
    if rule.get("type") == "pull_request":
        rule["parameters"]["required_approving_review_count"] = int(os.environ["APPROVALS"])
print(json.dumps(ruleset))
PY
)
        name=$(printf '%s' "$body" | python3 -I -c 'import json,sys; print(json.load(sys.stdin)["name"])')
        ids=$(printf '%s\n' "$EXISTING" | awk -F'\t' -v n="$name" '$1 == n {print $2}')
        if [ "$(printf '%s' "$ids" | grep -c .)" -gt 1 ]; then
            warn "$name: more than one ruleset has this name; fix it by hand"; FAILED=1; continue
        fi
        if [ "$APPLY" = 0 ]; then
            if [ -n "$ids" ]; then action="update ruleset $ids"; else action="create"; fi
            plan "$name: $action (approvals: $APPROVALS)"
        elif [ -n "$ids" ]; then
            write "$name: update ruleset $ids" "$body" -- -X PUT "repos/$REPO/rulesets/$ids"
        else
            write "$name: create" "$body" -- -X POST "repos/$REPO/rulesets"
        fi
    done
fi
echo

# ── Security ─────────────────────────────────────────────────────────────
echo "Security:"
echo "  now: $(security_now)"
SCANNING='{"security_and_analysis":{"secret_scanning":{"status":"enabled"},"secret_scanning_push_protection":{"status":"enabled"}}}'
if [ "$APPLY" = 0 ]; then
    if [ "$PRIVATE" = 1 ]; then plan "secret scanning and push protection (private repo: needs GitHub Secret Protection)"
    else plan "secret scanning and push protection"; fi
    plan "Dependabot alerts and security updates"
elif [ "$PRIVATE" = 1 ]; then
    write "secret scanning and push protection" "$SCANNING" optional -- -X PATCH "repos/$REPO"
else
    write "secret scanning and push protection" "$SCANNING" -- -X PATCH "repos/$REPO"
fi
if [ "$APPLY" = 1 ]; then
    write "Dependabot alerts" "" -- -X PUT "repos/$REPO/vulnerability-alerts"
    write "Dependabot security updates" "" -- -X PUT "repos/$REPO/automated-security-fixes"
fi
if [ "$PRIVATE" = 1 ]; then
    note "private vulnerability reporting: skipped (public repos only)"
elif [ "$APPLY" = 0 ]; then
    plan "private vulnerability reporting"
else
    write "private vulnerability reporting" "" -- -X PUT "repos/$REPO/private-vulnerability-reporting"
fi
echo

if [ "$FAILED" = 1 ]; then
    echo "Done, but some settings weren't applied (marked !). Fix them in the repo's Settings, or re-run after resolving the cause."
    exit 1
fi
if [ "$APPLY" = 1 ]; then echo "Done."; else echo "Re-run with --apply to make these changes."; fi
