from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures"


class ScanTests(unittest.TestCase):
    def test_scan_fixture_returns_json(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "scan_repo.py"),
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
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["state"]["state"], "S3")
        self.assertIsInstance(data["units"], list)


if __name__ == "__main__":
    unittest.main()
