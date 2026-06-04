"""Tests for craft fabrication method source validation."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/validate_craft_fabrication_methods_v0.py"


class CraftFabricationMethodValidationTests(unittest.TestCase):
    def test_craft_methods_validate(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS craft fabrication method validation", result.stdout)


if __name__ == "__main__":
    unittest.main()

