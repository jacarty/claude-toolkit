---
name: codex
description: "Get a second opinion from OpenAI Codex (the `codex` CLI): an independent code review of a diff, branch or commit, or a cross-model check of a plan, design, ADR, finding or bug theory. Use when the user asks for Codex, a second opinion, another model's view or a cross-model review. Local, interactive sessions only: never in an unattended or scheduled agent run."
---

# Codex second opinion

Codex is a different model family with its own blind spots, so it catches things Claude and the Claude subagents miss (and vice versa). Treat it like the other review agents in `docs/process.md`: a second pair of eyes, not an authority.

**Local only.** This skill uses the `codex` CLI on the user's machine, under their own ChatGPT login. If you are running unattended (a scheduled task, CI, a cloud agent), stop here and don't use this skill.

This skill is **ad hoc**: use it when asked, on uncommitted work, or on plans, ADRs and scope changes before any code exists. `antigravity` is the pre-PR gate (`docs/process.md`). If the repo has Codex's GitHub integration reviewing every PR, this adds Codex's view before the PR exists; if it doesn't, consider running this alongside `antigravity` on high-risk PRs.

## Preconditions

- `codex --version` and `codex login status` (expect "Logged in"). If either fails, tell the user and skip the Codex review; don't try to log in. It never blocks a PR.
- Run the git setup from the repo root, and `codex` itself only inside the clean worktree (Setup). Codex reads `AGENTS.md` there, so don't restate project context it can read; give it the task.

## Hard rules

- **Read-only, always.** Every call passes `-c sandbox_mode='"read-only"'` (the `RO` variable below). Without it, `review` and `resume` fall back to the user's default sandbox (often `workspace-write`); neither takes `-s`. After each run, check the log's `sandbox:` line says `read-only`. Never use `workspace-write`, `danger-full-access`, `--approve-for-me` or any `--dangerously-*` flag unless the user explicitly asks for Codex to edit, and then only `workspace-write` on a branch.
- **Run it in a clean worktree, never in the checkout.** The read-only sandbox stops writes, not reads: Codex can read any file in its workspace, gitignored ones included, and whatever it reads goes to OpenAI. A checkout typically holds `.env` files, local config with real identifiers, Terraform state and other private files. A `git worktree` of `HEAD` has only committed files (Setup).
- **It sends content to OpenAI** under the user's account. Never point it at secrets, `.env*`, `*.tfstate*`, `*.tfvars`, keys, cloud CLI output, raw production or CI logs, security-scanner findings, or anything holding account IDs, project numbers or service-account emails. Don't ask it to run cloud CLIs, `gh`, or anything that calls an external service.
- **Don't anchor it.** For an independent opinion, don't put your own conclusion in the prompt. Ask the question; compare answers afterwards.
- **Verify before relaying.** Every Codex finding gets checked against the code before you present it or act on it.

## Setup

Set these first; write output to the scratchpad with `-o` and keep the log separate (the log is noisy):

```bash
RO=(-c 'sandbox_mode="read-only"')
SP=<absolute scratchpad path>   # absolute: the paths below are used from inside $TREE
OUT=$SP/codex-<slug>.md; LOG=$SP/codex-<slug>.log; DIFF=$SP/codex-<slug>.diff
TREE=$SP/codex-<slug>-tree
git worktree add --detach "$TREE" HEAD     # committed files only: no ignored or private files
```

Run every `codex` call from inside `$TREE`, in a subshell so your own shell never sits in a directory that's later removed: `(cd "$TREE" && codex ...)`. Committed branches and commits are visible there (the worktree shares the repo's history); uncommitted changes aren't, so they travel as a diff in the prompt (mode 2). Afterwards:

```bash
(cd "$TREE" && git status --porcelain --ignored)   # must print nothing: no edits, no new files
git worktree remove --force "$TREE"
```

Long reviews: `run_in_background: true` with a generous timeout (diff reviews take ~15 s for a small commit, minutes for a large branch).

## Modes

### 1. Plain diff review (native reviewer)

```bash
(cd "$TREE" && codex exec review "${RO[@]}" --base main    -o "$OUT" > "$LOG" 2>&1)   # branch vs main
(cd "$TREE" && codex exec review "${RO[@]}" --commit <sha> -o "$OUT" > "$LOG" 2>&1)   # one commit
```

These presets **cannot take a custom prompt** (`--base`/`--commit` conflict with `[PROMPT]`). For a focused review, or for uncommitted work, use mode 2. Don't use `--uncommitted`: it only works in the checkout, where Codex can read private files.

### 2. Focused review or second opinion (`codex exec`)

For uncommitted work, write the diff first (`git diff HEAD > "$DIFF"`, plus `git diff --no-index /dev/null <file> >> "$DIFF" || true` for each untracked file) and check it for secrets and private identifiers (Hard rules). Pass the prompt on stdin, with the instructions from a quoted heredoc so nothing in them expands:

```bash
(cd "$TREE" && { cat <<'EOF'; [ ! -f "$DIFF" ] || cat "$DIFF"; } | codex exec "${RO[@]}" -o "$OUT" - > "$LOG" 2>&1)
<task: what to review or answer, and why>
<scope: the diff below, `git diff main...HEAD`, specific files, or a question>
<focus: e.g. auth, data leakage, IAM, CI permissions>
Do not modify any files.
Output: findings ranked most severe first, each with file:line, severity
(blocking / non-blocking / nit), confidence (high / medium / low) and a
one-line fix. Say "no findings" if there are none. No preamble.
EOF
```

With no `$DIFF` file (a plan, a question, or a committed branch Codex can read with `git`), only the instructions go in. Use a new slug for each review, or `rm -f "$DIFF"` first, so a diff left over from an earlier run isn't sent.

Good generic focus lines (add project-specific ones from the triggers in `docs/process.md`):
- Auth, IAM, permissions: "Is every role or permission the minimum, scoped to one resource? Is there any path that skips the auth check?"
- Anything published or logged: "Could anything private reach logs, public output or the repo (secrets, identifiers, request bodies, raw logs)?"
- `.github/workflows/`: "Are job permissions minimal and third-party actions SHA-pinned? Could a PR from a fork run with elevated permissions or secrets?"
- Plans, ADRs, scope changes: "What's the strongest argument against this decision? What would fail first in production?"

### 3. Follow-up

Ask a follow-up in the same Codex session (it keeps its context). Take the id from the `session id:` line of the first run's log; don't use `--last`, which can pick up one of the user's own Codex sessions:

```bash
(cd "$TREE" && codex exec resume "${RO[@]}" <session-id> -o "$OUT" - > "$LOG" 2>&1 <<'EOF'
<follow-up, e.g. "Finding 2: I think X because Y. Do you still hold it?">
EOF
)
```

Keep `$TREE` until the last follow-up, then check it and remove it (Setup).

## Handling the output

1. Confirm `grep '^sandbox' "$LOG"` says `read-only`, and that the worktree check printed nothing before you removed it. Read `$OUT` in full; if it's empty or missing, check the tail of `$LOG` for the error.
2. Check each finding against the code. Classify: **confirmed**, **disputed** (say why) or **unverified**.
3. Report to the user with Codex named as the source. Lead with confirmed blocking findings, then non-blocking ones, then disputed ones in a line each. Don't dump the raw output unless asked.
4. Where Claude and Codex disagree on something that matters, say so plainly and give your recommendation; optionally run mode 3 to put the counter-argument to Codex.
5. Fold accepted findings in following `docs/process.md` ("When an agent or gate flags something"): blocking ones are fixed before push; non-blocking ones are fixed inline, or noted under "Known gaps" in the PR body and added to `docs/tech-debt.md`.
