"""Code ampacity tables and correction factors (NEC and CEC).

Table values live in data/*.json, each with a status: VERIFIED (checked
against the licensed code book), UNVERIFIED (entered from memory, likely
right) or PLACEHOLDER (known not to be the right table). Calculations refuse
PLACEHOLDER data unless the caller explicitly allows it.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from .conductors import normalize_size

DATA = Path(__file__).parent / "data"
COLUMNS = (60, 75, 90)
CODES = ("NEC", "CEC")
INSTALLATIONS = ("raceway", "free_air")

# Clause references printed in reports. NEC: NFPA 70-2023. CEC: CSA C22.1.
# [UNVERIFIED: clause numbering to be confirmed against current editions]
CLAUSES = {
    "NEC": {
        "ambient": "NEC 310.15(B)(1) equation",
        "ccc": "NEC Table 310.15(C)(1)",
        "parallel": "NEC 310.10(G)",
        "terminal": "NEC 110.14(C)",
        "continuous": "NEC 215.2(A)(1)",
        "vd": "NEC 215.2(A)(2) Informational Note (3 % feeder / 5 % total)",
    },
    "CEC": {
        "ambient": "CEC Table 5A (equation basis)",
        "ccc": "CEC Table 5C",
        "parallel": "CEC Rule 12-108",
        "terminal": "CEC Rule 4-006",
        "continuous": "CEC Rule 8-104",
        "vd": "CEC Rule 8-102 (3 % feeder or branch / 5 % total)",
    },
}

# Number of current-carrying conductors in one raceway -> adjustment factor.
# [UNVERIFIED: values from memory; confirm against the tables cited above]
_CCC = {
    "NEC": ((3, 1.00), (6, 0.80), (9, 0.70), (20, 0.50), (30, 0.45), (40, 0.40), (10**9, 0.35)),
    "CEC": ((3, 1.00), (6, 0.80), (24, 0.70), (42, 0.60), (10**9, 0.50)),
}

# Minimum size for paralleled conductors.
# NEC 310.10(G): 1/0 AWG. CEC 12-108: 1/0 AWG Cu, 2/0 AWG Al. [UNVERIFIED]
PARALLEL_MIN = {"NEC": {"Cu": "1/0", "Al": "1/0"}, "CEC": {"Cu": "1/0", "Al": "2/0"}}


class DataStatusError(RuntimeError):
    pass


@dataclass(frozen=True)
class TableInfo:
    code: str
    edition: str
    status: str
    source: str
    table_name: str


@cache
def _load(code: str) -> dict:
    if code not in CODES:
        raise ValueError(f"code must be one of {CODES}")
    return json.loads((DATA / f"ampacity_{code.lower()}.json").read_text())


def table_info(code: str, installation: str) -> TableInfo:
    meta = _load(code)["_meta"]
    return TableInfo(code, meta["edition"], meta["status"], meta["source"], meta["tables"][installation])


def check_status(code: str, allow_placeholder_data: bool) -> str:
    status = _load(code)["_meta"]["status"]
    if status == "PLACEHOLDER" and not allow_placeholder_data:
        raise DataStatusError(
            f"{code} ampacity tables are PLACEHOLDER data (see pecalc/data/ampacity_{code.lower()}.json). "
            "Enter the real table values first, or pass allow_placeholder_data=True / --allow-placeholder-data "
            "to run anyway for testing."
        )
    return status


def table_ampacity(code: str, installation: str, material: str, size: str, temp_col: int) -> float | None:
    if installation not in INSTALLATIONS:
        raise ValueError(f"installation must be one of {INSTALLATIONS}")
    if temp_col not in COLUMNS:
        raise ValueError(f"temperature column must be one of {COLUMNS}")
    row = _load(code)[installation][material].get(normalize_size(size))
    return None if row is None else float(row[COLUMNS.index(temp_col)])


def ambient_factor(ambient_c: float, conductor_temp_c: int, rated_ambient_c: float = 30.0) -> float:
    """sqrt((Tc - Ta) / (Tc - Tr)); 0 if the ambient reaches the rating."""
    if ambient_c >= conductor_temp_c:
        return 0.0
    return math.sqrt((conductor_temp_c - ambient_c) / (conductor_temp_c - rated_ambient_c))


def ccc_factor(code: str, current_carrying: int) -> float:
    for limit, factor in _CCC[code]:
        if current_carrying <= limit:
            return factor
    raise AssertionError
