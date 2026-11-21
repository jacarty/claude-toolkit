#!/usr/bin/env python3
"""Checks for the toolkit's own config and docs. Standard library only.

Usage: python3 -I .github/scripts/check_toolkit.py [settings|frontmatter|links|all]

- settings:    .claude/settings.json is strict JSON (Claude Code skips the whole
               file on a `//` comment or trailing comma), its hooks are shaped
               right and point at scripts that exist, and settings.example.jsonc
               parses as JSONC.
- rulesets:    .github/rulesets/*.json are valid, and every required status
               check names a job in .github/workflows/ (a renamed job would
               otherwise block every merge).
- frontmatter: every skill and agent has a `name` that matches its folder or
               file, and a `description` (for skills, one that fits the listing).
- links:       relative links and images in Markdown files point at files that
               exist.

Checks the repo this script lives in, wherever it's run from. Exits 1 if any
check fails. CI runs it on the runner's Python 3.14.
Tests: .github/scripts/test_check_toolkit.py.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
import urllib.parse
from pathlib import Path
from typing import NamedTuple

# The repo root: this file lives at .github/scripts/check_toolkit.py.
REPO_ROOT = Path(__file__).resolve().parents[2]

# Never docs, at any depth.
SKIP_ANYWHERE = {".git", "node_modules", ".venv", ".trees", "__pycache__"}
# Build output, at the repo root only (a docs/build/ folder is still checked).
SKIP_AT_ROOT = {"dist", "build"}
MARKDOWN_SUFFIXES = {".md", ".markdown"}

# Claude Code truncates a skill's `description` plus `when_to_use` at this
# length in the skill listing.
SKILL_LISTING_LIMIT = 1536

# A relative link that climbs out of the repo is fine when it's a GitHub web
# route, such as ../../security/advisories/new in .github/SECURITY.md.
GITHUB_ROUTES = {"security", "issues", "pulls", "discussions", "wiki", "actions", "releases", "projects", "settings"}


class Finding(NamedTuple):
    path: str
    line: int | None
    message: str


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ── settings ─────────────────────────────────────────────────────────────


def strip_jsonc(text: str) -> str:
    """Turn JSONC into JSON: drop `//` and `/* */` comments and trailing commas.

    A small scanner, so comment markers and commas inside strings are left alone.
    """
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            out.append(text[i : j + 1])
            i = j + 1
        elif text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
        elif c == ",":
            j = i + 1
            # Look past whitespace and comments for a closing bracket.
            while j < n:
                if text[j].isspace():
                    j += 1
                elif text.startswith("//", j):
                    while j < n and text[j] != "\n":
                        j += 1
                elif text.startswith("/*", j):
                    end = text.find("*/", j + 2)
                    j = n if end == -1 else end + 2
                else:
                    break
            if j >= n or text[j] not in "]}":
                out.append(c)
            i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


PROJECT_SCRIPT = re.compile(r"^\$\{?CLAUDE_PROJECT_DIR\}?/(.+)$")


def check_hooks(hooks: object, where: str, root: Path) -> list[Finding]:
    found: list[Finding] = []
    if not isinstance(hooks, dict):
        return [Finding(where, None, "`hooks` must be an object of event names")]
    for event, groups in hooks.items():
        if not isinstance(groups, list):
            found.append(Finding(where, None, f"`hooks.{event}` must be a list"))
            continue
        for group in groups:
            entries = group.get("hooks") if isinstance(group, dict) else None
            if not isinstance(entries, list):
                found.append(Finding(where, None, f"each `hooks.{event}` entry needs a `hooks` list"))
                continue
            for hook in entries:
                if not isinstance(hook, dict) or hook.get("type") != "command" or not hook.get("command"):
                    continue
                try:
                    tokens = shlex.split(hook["command"])
                except ValueError as exc:
                    found.append(Finding(where, None, f"can't parse hook command ({exc}): {hook['command']}"))
                    continue
                for position, token in enumerate(tokens):
                    match = PROJECT_SCRIPT.match(token)
                    if not match:
                        continue
                    script = root / match.group(1)
                    if not script.is_file():
                        found.append(Finding(where, None, f"hook script not found: {match.group(1)}"))
                    elif position == 0 and not os.access(script, os.X_OK):
                        # Run directly, so it must be executable. After an
                        # interpreter (`bash script.sh`) it needn't be.
                        found.append(Finding(where, None, f"hook script not executable: {match.group(1)}"))
    return found


def check_settings(root: Path) -> list[Finding]:
    found: list[Finding] = []
    live = root / ".claude" / "settings.json"
    if live.exists():
        where = rel(live, root)
        try:
            settings = json.loads(read(live))
        except json.JSONDecodeError as exc:
            found.append(Finding(where, exc.lineno, f"not valid JSON ({exc.msg}). Claude Code skips the whole file."))
            settings = None
        if settings is not None:
            if not isinstance(settings, dict):
                found.append(Finding(where, None, "top level must be a JSON object"))
            elif "hooks" in settings:
                found.extend(check_hooks(settings["hooks"], where, root))

    example = root / ".claude" / "settings.example.jsonc"
    if example.exists():
        try:
            json.loads(strip_jsonc(read(example)))
        except json.JSONDecodeError as exc:
            found.append(Finding(rel(example, root), exc.lineno, f"doesn't parse as JSONC ({exc.msg})"))
    return found


# ── rulesets ─────────────────────────────────────────────────────────────

# Only checks bound to GitHub Actions are verified against workflow jobs. A
# check from another app (CircleCI, Vercel, ...) or with no integration_id
# (which any app can satisfy) is left alone rather than raise a false alarm.
GITHUB_ACTIONS_APP_ID = 15368
JOBS_LINE = re.compile(r"^jobs:\s*(?:#.*)?$")
KEY_LINE = re.compile(r"""^( *)("[^"]*"|'[^']*'|[A-Za-z0-9_-]+):(?:\s+(.*?))?\s*$""")
BLOCK_SCALAR_HEADER = re.compile(r"^[|>][+-]?\d*\s*(?:#.*)?$")
EXPRESSION = re.compile(r"\$\{\{.*?\}\}")


class Job(NamedTuple):
    name: str  # the check name GitHub reports: `name:` if set, else the job id
    matrix: bool  # has strategy.matrix: reports as "name (values)"
    reusable: bool  # calls a reusable workflow: reports as "name / inner job"


def yaml_scalar(raw: str | None) -> str | None:
    """A plain, quoted or commented one-line YAML value."""
    raw = (raw or "").strip()
    if not raw:
        return None
    if raw[0] == '"':
        end = raw.find('"', 1)
        return raw[1:end] if end > 0 else raw[1:]
    if raw[0] == "'":
        value, i = [], 1
        while i < len(raw):
            if raw[i] == "'":
                if raw[i + 1 : i + 2] == "'":  # '' is an escaped quote
                    value.append("'")
                    i += 2
                    continue
                break
            value.append(raw[i])
            i += 1
        return "".join(value)
    return re.sub(r"\s+#.*$", "", raw).strip() or None


def jobs_in(text: str) -> dict[str, Job]:
    """Map each job id in a workflow to how GitHub reports its check.

    Handles any indentation, comments, quoted names and block-scalar names.
    Doesn't handle flow-style YAML or anchors, and doesn't check that the
    workflow runs on PRs (triggers, `paths:` filters).
    """
    jobs: dict[str, Job] = {}
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if JOBS_LINE.match(line))
    except StopIteration:
        return jobs
    job_indent = child_indent = None
    job: str | None = None
    block: list[str] | None = None  # lines of a block-scalar `name:` being read
    block_indent = 0

    def finish_block() -> None:
        nonlocal block
        if job is not None and block is not None:
            jobs[job] = jobs[job]._replace(name=" ".join(block).strip() or job)
        block = None

    for line in lines[start + 1 :]:
        indent = len(line) - len(line.lstrip(" "))
        if block is not None:
            if not line.strip() or indent > block_indent:
                if line.strip():
                    block.append(line.strip())
                continue
            finish_block()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if indent == 0:
            break  # the next top-level key: jobs: has ended
        if job_indent is None:
            job_indent = indent
        key = KEY_LINE.match(line)
        if indent == job_indent:
            job = yaml_scalar(key.group(2)) if key else None
            child_indent = None
            if job:
                jobs[job] = Job(job, matrix=False, reusable=False)
            continue
        if job is None:
            continue
        if child_indent is None:
            child_indent = indent
        if indent != child_indent or not key:
            continue
        field, value = key.group(2), key.group(3)
        if field == "name":
            if value and BLOCK_SCALAR_HEADER.match(value.strip()):
                block, block_indent = [], child_indent
            elif yaml_scalar(value):
                jobs[job] = jobs[job]._replace(name=yaml_scalar(value))
        elif field == "uses":
            jobs[job] = jobs[job]._replace(reusable=True)
        elif field == "strategy":
            jobs[job] = jobs[job]._replace(matrix=True)  # a strategy without a matrix is rare
    finish_block()
    return jobs


def name_pattern(job: Job) -> re.Pattern[str]:
    """Match the check name(s) a job reports.

    `${{ ... }}` expressions match anything. A matrix job also reports as
    `name (values)`, and a reusable-workflow call as `name / inner job`.
    """
    core = ".+".join(re.escape(part) for part in EXPRESSION.split(job.name))
    suffixes = ([r" \(.+\)"] if job.matrix else []) + ([r" / .+"] if job.reusable else [])
    return re.compile(core + (f"(?:{'|'.join(suffixes)})?" if suffixes else ""))


def workflow_jobs(root: Path) -> tuple[list[Job], list[Finding]]:
    """Every job in the repo's workflows, plus files that couldn't be read."""
    jobs: list[Job] = []
    problems: list[Finding] = []
    workflows = root / ".github" / "workflows"
    if not workflows.is_dir():
        return jobs, problems
    for workflow in sorted(list(workflows.glob("*.yml")) + list(workflows.glob("*.yaml"))):
        try:
            jobs.extend(jobs_in(read(workflow)).values())
        except UnicodeDecodeError:
            problems.append(Finding(rel(workflow, root), None, "not UTF-8, so its jobs couldn't be read"))
    return jobs, problems


def check_exists(context: str, jobs: list[Job]) -> bool:
    return any(name_pattern(job).fullmatch(context) for job in jobs)


def line_of(text: str, needle: str) -> int | None:
    index = text.find(needle)
    return text.count("\n", 0, index) + 1 if index != -1 else None


def check_rulesets(root: Path) -> list[Finding]:
    found: list[Finding] = []
    folder = root / ".github" / "rulesets"
    if not folder.is_dir():
        return found
    jobs, found = workflow_jobs(root)
    for path in sorted(folder.glob("*.json")):
        where = rel(path, root)
        text = read(path)
        try:
            ruleset = json.loads(text)
        except json.JSONDecodeError as exc:
            found.append(Finding(where, exc.lineno, f"not valid JSON ({exc.msg})"))
            continue
        if not isinstance(ruleset, dict) or not isinstance(ruleset.get("rules"), list):
            found.append(Finding(where, None, "a ruleset must be an object with a `rules` list"))
            continue
        for key in ("name", "target", "enforcement"):
            if not ruleset.get(key):
                found.append(Finding(where, None, f"ruleset has no `{key}`"))
        for rule in ruleset["rules"]:
            if not isinstance(rule, dict) or rule.get("type") != "required_status_checks":
                continue
            params = rule.get("parameters")
            required = params.get("required_status_checks") if isinstance(params, dict) else None
            if not isinstance(required, list):
                found.append(Finding(where, None, "`required_status_checks` needs `parameters.required_status_checks` as a list"))
                continue
            for check in required:
                context = check.get("context") if isinstance(check, dict) else None
                app = check.get("integration_id") if isinstance(check, dict) else None
                if not context or app != GITHUB_ACTIONS_APP_ID:
                    continue  # another app, or any app: not ours to verify
                if not check_exists(context, jobs):
                    found.append(
                        Finding(
                            where,
                            line_of(text, f'"{context}"'),
                            f"required check `{context}` isn't reported by any job in .github/workflows/; merges would wait for it forever",
                        )
                    )
    return found


# ── frontmatter ──────────────────────────────────────────────────────────

BLOCK_SCALAR = re.compile(r"^[>|][+-]?\d*$")
TOP_KEY = re.compile(r"^([A-Za-z_][\w-]*):(?:\s+(.*))?$")


def frontmatter(text: str) -> dict[str, str] | None:
    """Parse the simple YAML frontmatter skills and agents use.

    Handles plain, quoted and `>`/`|` block values, continuation lines, and
    `# comments` after plain values. Not a general YAML parser.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if end is None:
        return None
    fields: dict[str, str] = {}
    key: str | None = None
    open_quote: str | None = None
    for line in lines[1:end]:
        top = TOP_KEY.match(line)
        if top and open_quote is None:
            key, value = top.group(1), (top.group(2) or "").strip()
            if not value or BLOCK_SCALAR.match(value):
                fields[key] = ""
            elif value[0] in "\"'":
                quote = value[0]
                if len(value) > 1 and value.endswith(quote):
                    fields[key] = value[1:-1]
                else:  # a quoted value that runs onto the next lines
                    fields[key], open_quote = value[1:], quote
            else:
                fields[key] = re.sub(r"\s+#.*$", "", value)
        elif key is not None and (line.startswith((" ", "\t")) or open_quote or not line.strip()):
            part = line.strip()
            if open_quote and part.endswith(open_quote):
                part, open_quote = part[:-1], None
            fields[key] = (fields[key] + " " + part).strip()
    return fields


def check_entry(path: Path, expected_name: str, root: Path, is_skill: bool) -> list[Finding]:
    where = rel(path, root)
    fields = frontmatter(read(path))
    if fields is None:
        return [Finding(where, 1, "missing frontmatter (a `---` block at the top)")]
    found = []
    name = fields.get("name", "")
    if not name:
        found.append(Finding(where, None, "frontmatter has no `name`"))
    elif name != expected_name:
        found.append(Finding(where, None, f"`name: {name}` doesn't match `{expected_name}`"))
    description = fields.get("description", "")
    if not description:
        found.append(Finding(where, None, "frontmatter has no `description`"))
    elif is_skill:
        listed = len(description) + len(fields.get("when_to_use", ""))
        if listed > SKILL_LISTING_LIMIT:
            found.append(
                Finding(where, None, f"description + when_to_use is {listed} characters; the skill listing truncates at {SKILL_LISTING_LIMIT}")
            )
    return found


def check_frontmatter(root: Path) -> list[Finding]:
    found: list[Finding] = []
    skills = root / ".claude" / "skills"
    if skills.is_dir():
        for folder in sorted(p for p in skills.iterdir() if p.is_dir()):
            skill = folder / "SKILL.md"
            if not skill.is_file():
                found.append(Finding(rel(folder, root), None, "skill folder has no SKILL.md"))
            else:
                found.extend(check_entry(skill, folder.name, root, is_skill=True))
    agents = root / ".claude" / "agents"
    if agents.is_dir():
        for agent in sorted(agents.glob("*.md")):
            found.extend(check_entry(agent, agent.stem, root, is_skill=False))
    return found


# ── links ────────────────────────────────────────────────────────────────

FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)")
HTML_COMMENT = re.compile(r"<!--.*?-->")
# An inline link or image destination after `](`: <angle brackets>, or a run
# with balanced parentheses, then an optional "title", 'title' or (title).
INLINE_LINK = re.compile(
    r"\]\(\s*(?:<([^>\n]*)>|((?:[^()\s]|\([^()\s]*\))+))"
    r"(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
)
REFERENCE_DEF = re.compile(r"^ {0,3}\[[^\]]+\]:\s*(?:<([^>\n]*)>|(\S+))")
SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)


def markdown_files(root: Path) -> list[Path]:
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        at_root = Path(dirpath) == root
        dirnames[:] = [d for d in dirnames if d not in SKIP_ANYWHERE and not (at_root and d in SKIP_AT_ROOT)]
        found.extend(Path(dirpath) / f for f in filenames if Path(f).suffix.lower() in MARKDOWN_SUFFIXES)
    return sorted(found)


def prose_lines(text: str):
    """Yield (line number, text) for prose, skipping code and HTML comments."""
    fence: tuple[str, int] | None = None
    in_comment = False
    for number, line in enumerate(text.splitlines(), 1):
        if fence is None and not in_comment:
            opened = FENCE.match(line)
            # A backtick fence's info string can't contain a backtick; if it
            # does, the line is inline code, not a fence.
            if opened and not (opened.group(1)[0] == "`" and "`" in opened.group(2)):
                fence = (opened.group(1)[0], len(opened.group(1)))
                continue
        elif fence is not None:
            closed = FENCE.match(line)
            if closed and closed.group(1)[0] == fence[0] and len(closed.group(1)) >= fence[1] and not closed.group(2).strip():
                fence = None
            continue

        if in_comment:
            end = line.find("-->")
            if end == -1:
                continue
            line, in_comment = line[end + 3 :], False
        line = HTML_COMMENT.sub("", line)
        start = line.find("<!--")
        if start != -1:
            line, in_comment = line[:start], True
        yield number, INLINE_CODE.sub("", line)


def link_targets(line: str):
    for match in INLINE_LINK.finditer(line):
        yield match.group(1) if match.group(1) is not None else match.group(2)
    ref = REFERENCE_DEF.match(line)
    if ref:
        yield ref.group(1) if ref.group(1) is not None else ref.group(2)


def check_target(target: str, page: Path, root: Path) -> str | None:
    """Return an error message for a broken relative link, or None."""
    target = target.strip()
    if not target or target.startswith("#") or target.startswith("//") or SCHEME.match(target):
        return None  # same-page anchor, protocol-relative or external
    path_part = urllib.parse.unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not path_part:
        return None
    # GitHub resolves /path from the repo root.
    resolved = (root / path_part.lstrip("/")) if path_part.startswith("/") else (page.parent / path_part)
    resolved = Path(os.path.normpath(resolved))
    try:
        resolved.relative_to(root)
    except ValueError:
        if GITHUB_ROUTES & set(Path(path_part).parts):
            return None
        return f"link points outside the repo: {target}"
    if not resolved.exists():
        return f"broken link: {target}"
    return None


def check_links(root: Path) -> list[Finding]:
    found = []
    for page in markdown_files(root):
        for number, line in prose_lines(read(page)):
            for target in link_targets(line):
                problem = check_target(target, page, root)
                if problem:
                    found.append(Finding(rel(page, root), number, problem))
    return found


# ── output ───────────────────────────────────────────────────────────────

CHECKS = {"settings": check_settings, "rulesets": check_rulesets, "frontmatter": check_frontmatter, "links": check_links}


def annotate(finding: Finding) -> str:
    """A GitHub Actions error annotation, which attaches to the file and line."""

    def escape(value: str, prop: bool = False) -> str:
        value = value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        return value.replace(":", "%3A").replace(",", "%2C") if prop else value

    props = f"file={escape(finding.path, True)}"
    if finding.line:
        props += f",line={finding.line}"
    return f"::error {props}::{escape(finding.message)}"


def plain(finding: Finding) -> str:
    where = f"{finding.path}:{finding.line}" if finding.line else finding.path
    return f"error: {where}: {finding.message}"


def main(argv: list[str]) -> int:
    wanted = argv[1:] or ["all"]
    names = list(CHECKS) if "all" in wanted else wanted
    unknown = [n for n in names if n not in CHECKS]
    if unknown:
        print(f"unknown check: {', '.join(unknown)}. Choose from: {', '.join(CHECKS)}, all", file=sys.stderr)
        return 2
    findings = [f for name in names for f in CHECKS[name](REPO_ROOT)]
    in_actions = os.environ.get("GITHUB_ACTIONS") == "true"
    for finding in findings:
        print(annotate(finding) if in_actions else plain(finding))
    if not findings:
        print(f"ok: {', '.join(names)}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
