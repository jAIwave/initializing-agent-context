from __future__ import annotations

import importlib.util
import json
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


smoke = load_script("smoke_commands")


def classify(command: str) -> str:
    category, _ = smoke.classify(
        {"command": command, "cwd": ".", "file": "test", "line": 1}
    )
    return category


class ClassificationTests(unittest.TestCase):
    def test_expected_categories(self) -> None:
        cases = [
            ("pytest --collect-only -q", "safe"),
            ("npx tsc --noEmit", "safe"),
            ("python -m pytest tests/ -q", "test"),
            ("python -m venv .venv", "setup"),
            ("choco install tesseract --version=5.3.3", "setup"),
            ("npm run build", "build"),
            ("git status", "info"),
            ("docker compose config", "info"),
            (
                '& "$pg\\postgres.exe" -D data -p 55432 -h 127.0.0.1',
                "unknown",
            ),
            ("docker compose --env-file .env up -d", "dangerous"),
            ("rm -rf build", "dangerous"),
            ("service nginx restart", "dangerous"),
            ("python -m compileall -q src/redis_service src/shared", "unknown"),
            ("down -v", "skip"),
        ]
        for command, expected in cases:
            with self.subTest(command=command):
                self.assertEqual(classify(command), expected)

    def test_compound_commands_are_skipped(self) -> None:
        self.assertEqual(classify("cd app && pytest"), "skip")


class JsonOutputTests(unittest.TestCase):
    def test_json_mode_is_pure_json(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "smoke_commands.py"),
                "--root",
                str(FIXTURES / "valid"),
                "--json",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIn("commands", data)
        self.assertIn("summary", data)


if __name__ == "__main__":
    unittest.main()
