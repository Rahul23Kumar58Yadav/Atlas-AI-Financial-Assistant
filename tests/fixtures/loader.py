"""Small helper for loading static fixture files by name from this directory."""
from __future__ import annotations

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent


def load_json(filename: str) -> dict:
    return json.loads((FIXTURES_DIR / filename).read_text())


def load_text(filename: str) -> str:
    return (FIXTURES_DIR / filename).read_text()
