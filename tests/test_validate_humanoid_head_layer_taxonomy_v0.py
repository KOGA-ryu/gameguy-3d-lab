"""Tests for humanoid head layer taxonomy source validation."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/validate_humanoid_head_layer_taxonomy_v0.py"


class HumanoidHeadLayerTaxonomyValidationTests(unittest.TestCase):
    def test_humanoid_head_layer_taxonomy_validates(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS humanoid head layer taxonomy validation", result.stdout)


if __name__ == "__main__":
    unittest.main()
