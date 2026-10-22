"""Fingerprint and status of the data tables in pecalc/data/.

The fingerprint is a short SHA-256 of every data file, parsed and re-serialised with
sorted keys, so line endings and key order do not change it. A report or case file
that shows a different fingerprint was made with different table data, even if the
engine version is the same.
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

from . import __version__

DATA_DIR = Path(__file__).resolve().parent / "data"


def _canonical(path: Path) -> str:
    return json.dumps(json.loads(path.read_text(encoding="utf-8")), sort_keys=True, separators=(",", ":"))


@lru_cache(maxsize=1)
def data_fingerprint() -> str:
    h = hashlib.sha256()
    for p in sorted(DATA_DIR.glob("*.json")):
        h.update(p.name.encode())
        h.update(b"\0")
        h.update(_canonical(p).encode())
        h.update(b"\0")
    return h.hexdigest()[:12]


def data_tables() -> list[dict]:
    """One row per data file: name, edition and status from its _meta (blank when not given)."""
    rows = []
    for p in sorted(DATA_DIR.glob("*.json")):
        meta = json.loads(p.read_text(encoding="utf-8")).get("_meta", {})
        rows.append({"file": p.name, "edition": meta.get("edition", ""), "status": meta.get("status", "")})
    return rows


def engine_stamp() -> dict:
    """What a saved case file records about the engine that wrote it."""
    return {"pecalc": __version__, "data": data_fingerprint()}
