from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures"


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = load_script("check_agent_docs")


def run_checker(fixture: str, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "check_agent_docs.py"),
            "--root",
            str(FIXTURES / fixture),
            *extra,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


class GithubSlugTests(unittest.TestCase):
    def test_matches_github_slug_rules(self) -> None:
        cases = {
            "Setup & Commands": "setup--commands",
            "Pilot (17.10.2026)": "pilot-17102026",
            "Use `code` now": "use-code-now",
            "See [Docs](https://example.com)": "see-docs",
        }
        for heading, expected in cases.items():
            with self.subTest(heading=heading):
                self.assertEqual(checker.github_slug(heading), expected)


class MojibakeTests(unittest.TestCase):
    def test_warns_on_encoded_text(self) -> None:
        self.assertTrue(checker.has_mojibake("Ãœbersicht"))

    def test_skips_lines_that_explain_mojibake(self) -> None:
        self.assertFalse(checker.has_mojibake("Mojibake example: Ã¤"))


class FixtureTests(unittest.TestCase):
    def test_valid_fixture_passes_strict(self) -> None:
        result = run_checker("valid", "--strict")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_broken_fixture_fails(self) -> None:
        result = run_checker("broken", "--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing link target", result.stdout)

    def test_site_absolute_links_are_ignored(self) -> None:
        result = run_checker("site-links", "--strict")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_mojibake_warns(self) -> None:
        result = run_checker("mojibake", "--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mojibake", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
