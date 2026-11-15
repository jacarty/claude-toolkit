---
name: antigravity
description: "Get a second opinion from Google's Gemini through Antigravity (the `agy` CLI): an independent code review of a diff, branch or commit, or a cross-model check of a plan, design, ADR, finding or bug theory. Use when the user asks for Antigravity, agy, Gemini, a second opinion, another model's view or a cross-model review, or as the pre-PR gate that docs/process.md runs on every PR. Local, interactive sessions only: never in an unattended or scheduled agent run."
---

# Antigravity second opinion

Antigravity runs Gemini, a model family with its own blind spots, so it catches things Claude, the Claude subagents and Codex miss (and vice versa). Treat it like the other review agents in `docs/process.md`: a second pair of eyes, not an authority.

**Local only.** This skill uses the `agy` CLI on the user's machine, under their own Antigravity login. If you are running unattended (a scheduled task, CI, a cloud agent), stop here and don't use this skill.

This skill is the gate that `docs/process.md` runs on every PR before it opens, trivial PRs included. Use it ad hoc as well, on plans, ADRs and scope changes.

## Preconditions

- `agy --version` works and `agy models` lists models. `agy` has no login-status command, so a failing `agy models` means it's missing or logged out. Tell the user and skip the review (note it in the PR body if this was pre-PR); don't try to log in. It never blocks a PR.
- Run the git setup from the repo root, and `agy` itself only inside the clean worktree (Setup). It reads `AGENTS.md` there, so don't restate project context it can read; give it the task.

## Hard rules

- **Pinned model.** Every call passes `--model gemini-4-hydrogen-high` (Gemini 4 Hydrogen at Google's recommended default level). `agy` also serves Claude and GPT models, and without the pin the review may not come from a different family. When a newer Gemini ships, check `agy models` and update the pin here.
- **Read-only, always.** Every call passes `--mode plan --sandbox`. With both, edits and shell commands are refused and listed under `denied_actions` in the JSON output. Never use `--mode accept-edits`, `--mode auto` or `--dangerously-skip-permissions`, even if asked: this skill is for reviews only, and dropping the sandbox would let it read and write outside the worktree.
- **No shell, so put the diff in the prompt.** With `--sandbox` it can't run `git`, so write the diff yourself and paste it into the prompt. Don't hand it a path to a diff outside the workspace: in testing it misread scratchpad paths, couldn't find the file, and reviewed nothing. Don't ask it to run `git`, cloud CLIs, `gh` or anything that calls an external service.
- **Run it in a clean worktree, never in the checkout.** It can read any file in its workspace, gitignored ones included, and whatever it reads goes to Google. A checkout typically holds `.env` files, local config with real identifiers, Terraform state and other private files the diff scan never sees. A `git worktree` of `HEAD` has only committed files, and an edit there can't touch the checkout (Setup).
- **It sends content to Google** under the user's Antigravity account. Never point it at secrets, `.env*`, `*.tfstate*`, `*.tfvars`, keys, cloud CLI output, raw production or CI logs, security-scanner findings, or anything holding account IDs, project numbers or service-account emails. Check the diff file for these before sending it.
- **Don't anchor it.** For an independent opinion, don't put your own conclusion in the prompt. Ask the question; compare answers afterwards.
- **Verify before relaying.** Check every Antigravity finding against the code before you present it or act on it.

## Setup

```bash
AGY=(--model gemini-4-hydrogen-high --mode plan --sandbox --output-format json --print-timeout 1500s)
SP=<absolute scratchpad path>   # absolute: the paths below are used from inside $TREE
OUT=$SP/agy-<slug>.json; DIFF=$SP/agy-<slug>.diff; LOG=$SP/agy-<slug>.log
TREE=$SP/agy-<slug>-tree
git worktree add --detach "$TREE" HEAD     # committed files only: no ignored or private files
```

Run every `agy` call from inside `$TREE`, in a subshell so your own shell never sits in a directory that's later removed: `(cd "$TREE" && agy ...)`. Uncommitted changes aren't in the worktree, so they travel in the diff (section 1). Afterwards:

```bash
(cd "$TREE" && git status --porcelain --ignored)   # must print nothing: no edits, no new files
git worktree remove --force "$TREE"
```

Always use `run_in_background: true` with a generous timeout. A 900-line diff took about 40 s in testing, but run times vary, and the JSON is written only at the end, so an empty output file just means it's still running.

## 1. Code review

Write the diff first:

```bash
git diff main...HEAD > "$DIFF"        # branch vs main
git diff HEAD > "$DIFF"               # uncommitted, tracked files; add untracked ones with
                                      #   git diff --no-index /dev/null <file> >> "$DIFF" || true
                                      #   (it exits 1 whenever there's a difference)
git show <sha> > "$DIFF"              # one commit
```

Check the diff for secrets and private identifiers (Hard rules), then build the prompt: the instructions from a quoted heredoc, so nothing in them expands, with the diff appended after them:

```bash
PROMPT="$(cat <<'EOF'
Review the diff below against the code in this workspace. Read files; don't run commands.
<task: what changed and why, in a line, without your own verdict>
<focus: e.g. auth, data leakage, IAM, CI permissions>
Do not modify any files.
Output: findings ranked most severe first, each with file:line, severity
(blocking / non-blocking / nit), confidence (high / medium / low) and a
one-line fix. Say "no findings" if there are none. No preamble.

The diff:
EOF
)
$(cat "$DIFF")"
(cd "$TREE" && agy -p "$PROMPT" "${AGY[@]}" > "$OUT" 2> "$LOG")
```

The prompt must come straight after `-p`. `agy` doesn't read a prompt from stdin (`-p -` is taken as an empty task), so it travels as one argument, and Linux caps one argument at 128 KB. If `wc -c "$DIFF"` is over about 120 KB, split the diff by file group (`git diff main...HEAD -- src/ tests/`, then the rest) and run one review per part.

Good generic focus lines (add project-specific ones from the triggers in `docs/process.md`):
- Auth, IAM, permissions: "Is every role or permission the minimum, scoped to one resource? Is there any path that skips the auth check?"
- Anything published or logged: "Could anything private reach logs, public output or the repo (secrets, identifiers, request bodies, raw logs)?"
- `.github/workflows/`: "Are job permissions minimal and third-party actions SHA-pinned? Could a PR from a fork run with elevated permissions or secrets?"

## 2. Second opinion on a plan, ADR or theory

Same call with no diff: name the repo files to read by their path from the repo root (an ADR, a PRD section), paste in anything that isn't in the repo (a plan in the scratchpad), and ask the question. Good ones: "What's the strongest argument against this decision? What would fail first in production?" Check anything you paste in for secrets and private identifiers first, as for a diff (Hard rules).

## 3. Follow-up

Resume the conversation so it keeps its context. Take the id from the previous run's JSON; the reply carries a new `conversation_id`, so use the latest one for the next follow-up:

```bash
CID=$(python3 -I -c 'import json,sys;print(json.load(open(sys.argv[1]))["conversation_id"])' "$OUT")
(cd "$TREE" && agy -p "$(cat <<'EOF'
<follow-up, e.g. "Finding 2: I think X because Y. Do you still hold it?">
EOF
)" --conversation "$CID" "${AGY[@]}" > "$SP/agy-<slug>-2.json" 2>> "$LOG")
```

Don't use `-c`/`--continue`, which can pick up one of the user's own Antigravity conversations. Keep `$TREE` until the last follow-up, then check it and remove it (Setup).

## Handling the output

1. Read the JSON: `status` should be `SUCCESS` and `response` holds the review. `SUCCESS` doesn't mean it reviewed anything: a `response` that is only a preamble ("I am inspecting..."), or that says it couldn't read a file, is a failed review. Check that the prompt has the diff in it and asks it to read files, not run commands or edit, and rerun once. If it fails again, report it as failed.
2. Confirm the worktree check printed nothing, then remove the worktree. `denied_actions` lists anything it tried and was refused; a denied edit is worth mentioning. If `$OUT` is empty or isn't JSON, read `$LOG`: auth expiry, a bad flag or an over-long prompt show there.
3. Check each finding against the code. Classify it as **confirmed**, **disputed** (say why) or **unverified**.
4. Report to the user with Antigravity (and the pinned Gemini model) named as the source. Lead with confirmed blocking findings, then non-blocking ones, then disputed ones in a line each. Don't dump the raw output unless asked.
5. Where Claude and Antigravity disagree on something that matters, say so plainly and give your recommendation; optionally use a follow-up (section 3) to put the counter-argument to it.
6. Fold accepted findings in following `docs/process.md` ("When an agent or gate flags something"): blocking ones are fixed before push; non-blocking ones are fixed inline, or noted under "Known gaps" in the PR body and added to `docs/tech-debt.md`.
