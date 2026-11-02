"""The refactor must reproduce outputs captured from the original code."""
from __future__ import annotations

import json
import os
from pathlib import Path

from golden_capture import capture

GOLDEN = Path(__file__).parent / "golden" / "baseline.json"


def test_matches_original_baseline(tmp_path):
    cwd = os.getcwd()
    try:
        result = capture(tmp_path)
    finally:
        os.chdir(cwd)
    expected = json.loads(GOLDEN.read_text())
    assert result.keys() == expected.keys()
    for key in expected:
        assert result[key] == expected[key], key
