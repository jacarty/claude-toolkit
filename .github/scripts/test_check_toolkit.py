"""Tests for check_toolkit.py. Standard library only.

Run: python3 -I -m unittest discover -s .github/scripts -p 'test_*.py'
"""

from __future__ import annotations

import json
import os
import tempfile
import textwrap
import unittest
from pathlib import Path

import check_toolkit as ck


class RepoTestCase(unittest.TestCase):
    """Each test gets an empty throwaway repo root."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, path: str, text: str, executable: bool = False) -> Path:
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(textwrap.dedent(text), encoding="utf-8")
        if executable:
            file.chmod(0o755)
        return file

    def messages(self, findings: list[ck.Finding]) -> list[str]:
        return [f.message for f in findings]


class JsoncTests(unittest.TestCase):
    def parse(self, text: str):
        return json.loads(ck.strip_jsonc(text))

    def test_full_line_inline_and_block_comments(self) -> None:
        text = '{\n  // full line\n  "a": 1, // inline\n  /* block */ "b": [1, 2,],\n}\n'
        self.assertEqual(self.parse(text), {"a": 1, "b": [1, 2]})

    def test_strings_are_left_alone(self) -> None:
        text = '{"url": "https://x.y/z", "odd": "x, ]", "c": "/* not a comment */"}'
        self.assertEqual(self.parse(text), {"url": "https://x.y/z", "odd": "x, ]", "c": "/* not a comment */"})

    def test_escaped_quote_in_string(self) -> None:
        self.assertEqual(self.parse('{"q": "say \\"hi\\" // still a string"}'), {"q": 'say "hi" // still a string'})

    def test_trailing_comma_before_comment_and_bracket(self) -> None:
        self.assertEqual(self.parse('[1, 2, // last\n]'), [1, 2])


class SettingsTests(RepoTestCase):
    def test_comment_in_settings_json_fails(self) -> None:
        self.write(".claude/settings.json", '{\n  // no\n  "a": 1\n}\n')
        found = ck.check_settings(self.root)
        self.assertEqual(len(found), 1)
        self.assertIn("not valid JSON", found[0].message)
        self.assertEqual(found[0].line, 2)

    def settings_with_hook(self, command: str) -> None:
        hook = {"type": "command", "command": command}
        self.write(".claude/settings.json", json.dumps({"hooks": {"PostToolUse": [{"matcher": "Edit", "hooks": [hook]}]}}))

    def test_hook_quoting_styles_are_recognised(self) -> None:
        self.write(".claude/hooks/h.sh", "#!/bin/sh\n", executable=True)
        for command in (
            '"$CLAUDE_PROJECT_DIR"/.claude/hooks/h.sh',
            '"$CLAUDE_PROJECT_DIR/.claude/hooks/h.sh"',
            "${CLAUDE_PROJECT_DIR}/.claude/hooks/h.sh",
            'bash "$CLAUDE_PROJECT_DIR"/.claude/hooks/h.sh',
        ):
            with self.subTest(command=command):
                self.settings_with_hook(command)
                self.assertEqual(ck.check_settings(self.root), [])

    def test_missing_hook_script_fails_in_every_style(self) -> None:
        for command in ('"$CLAUDE_PROJECT_DIR"/.claude/hooks/gone.sh', "bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/gone.sh"):
            with self.subTest(command=command):
                self.settings_with_hook(command)
                self.assertEqual(self.messages(ck.check_settings(self.root)), ["hook script not found: .claude/hooks/gone.sh"])

    def test_executable_bit_needed_only_when_run_directly(self) -> None:
        self.write(".claude/hooks/h.sh", "#!/bin/sh\n", executable=False)
        self.settings_with_hook('"$CLAUDE_PROJECT_DIR"/.claude/hooks/h.sh')
        self.assertEqual(self.messages(ck.check_settings(self.root)), ["hook script not executable: .claude/hooks/h.sh"])
        self.settings_with_hook('bash "$CLAUDE_PROJECT_DIR"/.claude/hooks/h.sh')
        self.assertEqual(ck.check_settings(self.root), [])

    def test_badly_shaped_hooks_report_instead_of_crashing(self) -> None:
        self.write(".claude/settings.json", json.dumps({"hooks": {"PostToolUse": {"matcher": "Edit"}}}))
        self.assertEqual(self.messages(ck.check_settings(self.root)), ["`hooks.PostToolUse` must be a list"])

    def test_example_jsonc_must_parse(self) -> None:
        self.write(".claude/settings.example.jsonc", '{\n  "a": 1 // ok\n}\n')
        self.assertEqual(ck.check_settings(self.root), [])
        self.write(".claude/settings.example.jsonc", '{\n  "a": 1\n  "b": 2\n}\n')
        self.assertIn("doesn't parse as JSONC", ck.check_settings(self.root)[0].message)


class FrontmatterTests(unittest.TestCase):
    def test_values(self) -> None:
        text = textwrap.dedent(
            """\
            ---
            name: foo # a comment
            description: >
              folded text
              over two lines
            quoted: "a: b"
            plain: first
              continued
            multi: "starts here
              and ends here"
            ---
            body
            ---
            """
        )
        fields = ck.frontmatter(text)
        self.assertEqual(fields["name"], "foo")
        self.assertEqual(fields["description"], "folded text over two lines")
        self.assertEqual(fields["quoted"], "a: b")
        self.assertEqual(fields["plain"], "first continued")
        self.assertEqual(fields["multi"], "starts here and ends here")

    def test_closing_marker_with_trailing_space_and_crlf(self) -> None:
        self.assertEqual(ck.frontmatter("---\r\nname: ws\r\n--- \r\nbody"), {"name": "ws"})

    def test_missing_frontmatter(self) -> None:
        self.assertIsNone(ck.frontmatter("# just a heading\n"))
        self.assertIsNone(ck.frontmatter("---\nname: never closed\n"))


class EntryTests(RepoTestCase):
    def test_skill_checks(self) -> None:
        self.write(".claude/skills/good/SKILL.md", "---\nname: good\ndescription: does things\n---\n")
        self.write(".claude/skills/wrong/SKILL.md", "---\nname: other\ndescription: x\n---\n")
        (self.root / ".claude/skills/empty").mkdir(parents=True)
        long = "x" * 1000
        self.write(".claude/skills/long/SKILL.md", f"---\nname: long\ndescription: {long}\nwhen_to_use: {long}\n---\n")
        found = {f.path: f.message for f in ck.check_frontmatter(self.root)}
        self.assertNotIn(".claude/skills/good/SKILL.md", found)
        self.assertIn("doesn't match", found[".claude/skills/wrong/SKILL.md"])
        self.assertIn("no SKILL.md", found[".claude/skills/empty"])
        self.assertIn("2000 characters", found[".claude/skills/long/SKILL.md"])

    def test_agent_needs_description_but_no_length_limit(self) -> None:
        self.write(".claude/agents/a.md", "---\nname: a\n---\n")
        self.write(".claude/agents/b.md", f"---\nname: b\ndescription: {'y' * 2000}\n---\n")
        self.assertEqual(self.messages(ck.check_frontmatter(self.root)), ["frontmatter has no `description`"])


class LinkTests(RepoTestCase):
    def broken(self, markdown: str) -> list[str]:
        self.write("exists.md", "x\n")
        self.write("my file.md", "x\n")
        self.write("foo_(bar).md", "x\n")
        self.write("img.png", "x\n")
        self.write("dir/page.md", "x\n")
        self.write("doc.md", markdown)
        return [f"{f.line}: {f.message}" for f in ck.check_links(self.root) if f.path == "doc.md"]

    def test_valid_link_forms_pass(self) -> None:
        doc = """\
            [a](exists.md) [b](<my file.md>) [c](my%20file.md) [d](exists.md?plain=1)
            [e](foo_(bar).md) [f](exists.md "title") [g](exists.md 'title') [h](exists.md (title))
            ![img](img.png) [![badge](img.png)](exists.md) [dir](dir/) [abs](/exists.md)
            [web](https://example.com) [mail](mailto:x@y.z) [proto](//example.com/x) [top](#top)
            [ref]: exists.md
            """
        self.assertEqual(self.broken(doc), [])

    def test_broken_forms_are_caught(self) -> None:
        doc = """\
            [a](nope.md)
            ![img](nope.png)
            [![badge](img.png)](nope2.md)
            [ref]: nope3.md
            [b](<no such.md>)
            [c](../../../outside.md)
            """
        self.assertEqual(
            self.broken(doc),
            [
                "1: broken link: nope.md",
                "2: broken link: nope.png",
                "3: broken link: nope2.md",
                "4: broken link: nope3.md",
                "5: broken link: no such.md",
                "6: link points outside the repo: ../../../outside.md",
            ],
        )

    def test_github_web_routes_outside_the_repo_are_allowed(self) -> None:
        self.write(".github/SECURITY.md", "[report](../../security/advisories/new)\n")
        self.assertEqual(ck.check_links(self.root), [])

    def test_code_and_comments_are_skipped(self) -> None:
        doc = """\
            `[a](nope1.md)` and ``[b](nope2.md)`` inline
            <!-- [c](nope3.md) --> after comment [ok](exists.md)
            <!--
            [d](nope4.md)
            -->
            ```
            [e](nope5.md)
            ```
            ~~~
            ```
            [f](nope6.md)
            ~~~
            ````
            ```
            [g](nope7.md)
            ```
            ````
            [after](nope8.md)
            """
        self.assertEqual(self.broken(doc), ["18: broken link: nope8.md"])

    def test_indented_backticks_do_not_open_a_fence(self) -> None:
        doc = "    ```\n[x](nope.md)\n"
        self.assertEqual(self.broken(doc), ["2: broken link: nope.md"])

    def test_inline_triple_backticks_do_not_open_a_fence(self) -> None:
        doc = "```code``` here\n[x](nope.md)\n"
        self.assertEqual(self.broken(doc), ["2: broken link: nope.md"])

    def test_skipped_directories(self) -> None:
        self.write("node_modules/pkg/README.md", "[x](nope.md)\n")
        self.write("build/out.md", "[x](nope.md)\n")
        self.write("docs/build/guide.md", "[x](nope.md)\n")
        self.write("notes.markdown", "[x](nope.md)\n")
        self.assertEqual(sorted(f.path for f in ck.check_links(self.root)), ["docs/build/guide.md", "notes.markdown"])


class RulesetTests(RepoTestCase):
    def ruleset(self, *checks: tuple[str, int | None]) -> None:
        required = [{"context": c, **({"integration_id": app} if app else {})} for c, app in checks]
        rules = [{"type": "deletion"}, {"type": "required_status_checks", "parameters": {"required_status_checks": required}}]
        self.write(".github/rulesets/main.json", json.dumps({"name": "main", "target": "branch", "enforcement": "active", "rules": rules}, indent=2))

    def missing(self, *contexts: str) -> list[str]:
        self.ruleset(*[(c, 15368) for c in contexts])
        return [m.split("`")[1] for m in self.messages(ck.check_rulesets(self.root))]

    def test_job_names(self) -> None:
        text = textwrap.dedent(
            """\
            on: [push]
            jobs:  # all of them
                lint:  # fast
                    runs-on: x
                test:
                    name: "C# tests"   # quoted, with a hash
                    strategy:
                        matrix: {os: [a, b]}
                quoted:
                    name: 'Bob''s build'
                folded:
                    name: >-
                      long
                      name
                    runs-on: x
                call:
                    uses: ./.github/workflows/b.yml
                expr:
                    name: build ${{ matrix.os }}
                nested:
                    steps:
                      - name: not a job name
            env:
              ignored: x
            """
        )
        J = ck.Job
        self.assertEqual(
            ck.jobs_in(text),
            {
                "lint": J("lint", False, False),
                "test": J("C# tests", True, False),
                "quoted": J("Bob's build", False, False),
                "folded": J("long name", False, False),
                "call": J("call", False, True),
                "expr": J("build ${{ matrix.os }}", False, False),
                "nested": J("nested", False, False),
            },
        )

    def test_matching(self) -> None:
        self.write(
            ".github/workflows/a.yml",
            "on: [push]\njobs:\n  lint:\n    runs-on: x\n  test:\n    name: unit tests\n    strategy:\n      matrix: {os: [a]}\n"
            "  call:\n    uses: ./.github/workflows/b.yml\n  build:\n    name: build ${{ inputs.os }}\n",
        )
        self.assertEqual(self.missing("lint", "unit tests", "unit tests (ubuntu)", "call / inner", "build ubuntu-26.04"), [])
        # Suffixes only for matrix and reusable jobs; renamed or partial names still fail.
        self.assertEqual(self.missing("lint (removed-os)", "lint / gone", "checks", "unit"), ["lint (removed-os)", "lint / gone", "checks", "unit"])

    def test_folded_name_does_not_hide_a_missing_check(self) -> None:
        self.write(".github/workflows/a.yml", "jobs:\n  docs:\n    name: >-\n      build docs\n    runs-on: x\n")
        self.assertEqual(self.missing("build docs", "toolkit-checks"), ["toolkit-checks"])

    def test_same_job_id_in_two_workflows(self) -> None:
        self.write(".github/workflows/a.yml", "jobs:\n  test:\n    runs-on: x\n")
        self.write(".github/workflows/b.yaml", "jobs:\n  test:\n    name: unit tests\n")
        self.assertEqual(self.missing("test", "unit tests"), [])

    def test_only_checks_bound_to_actions_are_verified(self) -> None:
        self.write(".github/workflows/a.yml", "jobs:\n  lint:\n    runs-on: x\n")
        self.ruleset(("ci/circleci: build", 18001), ("any-app", None), ("lint", 15368), ("gone", 15368))
        self.assertEqual([m.split("`")[1] for m in self.messages(ck.check_rulesets(self.root))], ["gone"])

    def test_finding_points_at_the_line(self) -> None:
        self.write(".github/workflows/a.yml", "jobs:\n  lint:\n    runs-on: x\n")
        self.ruleset(("gone", 15368))
        finding = ck.check_rulesets(self.root)[0]
        self.assertEqual(finding.line, read_line_number(self.root / ".github/rulesets/main.json", '"gone"'))

    def test_invalid_input(self) -> None:
        self.write(".github/rulesets/bad.json", "{ nope")
        self.write(".github/rulesets/shape.json", json.dumps({"name": "x"}))
        self.write(".github/rulesets/params.json", json.dumps({"name": "p", "target": "branch", "enforcement": "active", "rules": [{"type": "required_status_checks", "parameters": "oops"}]}))
        (self.root / ".github/workflows").mkdir(parents=True)
        (self.root / ".github/workflows/latin1.yml").write_bytes("name: caf\xe9\n".encode("latin-1"))
        messages = self.messages(ck.check_rulesets(self.root))
        self.assertTrue(any("not valid JSON" in m for m in messages))
        self.assertIn("a ruleset must be an object with a `rules` list", messages)
        self.assertTrue(any("needs `parameters.required_status_checks`" in m for m in messages))
        self.assertIn("not UTF-8, so its jobs couldn't be read", messages)


def read_line_number(path: Path, needle: str) -> int:
    return next(i for i, line in enumerate(path.read_text().splitlines(), 1) if needle in line)


class OutputTests(unittest.TestCase):
    def test_annotation_escapes_and_attaches_to_line(self) -> None:
        finding = ck.Finding("a,b:c.md", 7, "100% broken\nlink")
        self.assertEqual(ck.annotate(finding), "::error file=a%2Cb%3Ac.md,line=7::100%25 broken%0Alink")

    def test_plain_output(self) -> None:
        self.assertEqual(ck.plain(ck.Finding("x.md", None, "bad")), "error: x.md: bad")


class RealRepoTest(unittest.TestCase):
    def test_this_repo_passes(self) -> None:
        old = os.getcwd()
        try:
            os.chdir("/")  # the checker must not depend on the working directory
            findings = [f for check in ck.CHECKS.values() for f in check(ck.REPO_ROOT)]
        finally:
            os.chdir(old)
        self.assertEqual(findings, [], "\n".join(ck.plain(f) for f in findings))


if __name__ == "__main__":
    unittest.main()
