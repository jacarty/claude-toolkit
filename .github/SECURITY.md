# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do not open a public issue.**

Instead, please use [GitHub's private vulnerability reporting](../../security/advisories/new) to submit a report. Include:

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

You should receive a response within a few days. The maintainer will work with you to understand the issue and coordinate a fix before any public disclosure.

> **Note:** Private vulnerability reporting must be enabled on the repository for the link above to work. Enable it under **Settings → Code security → Private vulnerability reporting**.

## Supported Versions

Only the latest version on the `main` branch is actively maintained.

## Security Best Practices

This repository includes several security measures:

- **Claude Code deny rules** (`permissions.deny` in `.claude/settings.json`) — stop Claude Code reading or editing environment files, keys, credentials and Terraform state. This is best-effort: a script, or a command like `grep -r`, that reads files without naming them isn't covered, so enable Claude Code's sandbox where you need enforcement. Other AI tools (Codex, Antigravity) don't read these rules. The cross-model review skills run them in a clean git worktree, which keeps out uncommitted and gitignored files such as `.env`. It doesn't keep out anything already committed: a secret in the repo's files or history would still be sent to the vendor, so it needs removing from history, not just from the working tree.
- **`.gitignore`** — excludes environment files (except committed templates like `.env.example`), keys, credentials files and Terraform state from version control
- **Pre-commit hooks** — scan for secrets and credentials before they enter git history
- **Dependency management** — keep dependencies updated and audit regularly

## Disclosure Policy

Once a vulnerability is confirmed and fixed, a security advisory will be published with appropriate details.
