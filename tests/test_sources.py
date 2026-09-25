"""data/SOURCES.md is generated. Fail if the committed copy has gone stale."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_sources import TARGET, build  # noqa: E402


def test_sources_file_is_up_to_date():
    assert TARGET.exists(), "data/SOURCES.md is missing; run scripts/build_sources.py"
    assert TARGET.read_text() == build(), (
        "data/SOURCES.md is out of date with the data. "
        "Run: python scripts/build_sources.py"
    )
