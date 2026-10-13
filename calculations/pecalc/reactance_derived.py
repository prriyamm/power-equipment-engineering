"""Cable reactance in conduit: NEC Chapter 9 Table 9 plus DERIVED rows.

Table 9 has no rows for 700, 800 or 900 kcmil and stops at 1000 kcmil, while
the conductor model and ampacity tables run to 2000 kcmil. Before this module
those sizes silently fell back to the touching-trefoil geometric reactance,
35-48 % below the Table 9 trend. data/reactance_nec_table9.json is NOT
changed; the values below are computed from it.

Every value produced here for a size missing from Table 9 is DERIVED, not a
published value, and callers must surface that to the user.

Method (per conduit column: pvc, aluminum, steel), identical to the web port
(prriyamm/power-studio-web, src/engine/reactanceDerived.js) so both agree:

    XL per conductor ~ ln(GMD / GMR), and both GMD (cable OD) and GMR scale
    roughly with conductor diameter ~ sqrt(kcmil), so XL is close to linear
    in ln(kcmil).
    - 700 kcmil: linear in ln(kcmil) between the 600 and 750 rows.
    - 800, 900 kcmil: linear in ln(kcmil) between the 750 and 1000 rows.
    - 1250-2000 kcmil: linear in ln(kcmil) extrapolated from the 750 and
      1000 rows, floored at the touching-trefoil reactance (GMD = cable OD,
      GMR = 0.7788 r) from the conductor geometry at 60 Hz. Three cables in a
      conduit cannot be closer than touching, so that is a physical lower
      bound; steel conduit only adds to it.
    Values are rounded to 4 decimals (ohm per 1000 ft).
"""

from __future__ import annotations

import json
import math
from functools import cache

from . import conductors as cond
from .ampacity import DATA

DERIVED_STATUS = "DERIVED — UNVERIFIED (interpolated/extrapolated from NEC Table 9, not a published value)"
DERIVED_METHOD = ("Linear in ln(kcmil): interpolated between neighbouring Table 9 rows (700, 800, 900 kcmil); "
                  "extrapolated from the 750 and 1000 kcmil rows (1250-2000 kcmil), floored at the touching-cable "
                  "reactance from the conductor geometry.")
RACEWAYS = ("pvc", "aluminum", "steel")
_INTERP = {"700": ("600", "750"), "800": ("750", "1000"), "900": ("750", "1000")}
_EXTRAP = ("1250", "1500", "1750", "2000")
DERIVED_SIZES = tuple(_INTERP) + _EXTRAP


@cache
def table9() -> dict:
    return json.loads((DATA / "reactance_nec_table9.json").read_text())


def floor_per_1000ft(size: str) -> float:
    """Touching-trefoil reactance, ohm / 1000 ft at 60 Hz (lower bound)."""
    return cond.reactance_ohm_per_m(size, cond.cable_od_mm(size), 60.0) * 1000 * cond.FT


def _ln_lerp(s: str, a: str, b: str, xa: float, xb: float) -> float:
    return xa + (math.log(int(s)) - math.log(int(a))) / (math.log(int(b)) - math.log(int(a))) * (xb - xa)


@cache
def derived_table() -> dict[str, dict[str, float]]:
    """Derived XL per raceway and size, ohm / 1000 ft. Never Table 9 values."""
    out = {}
    for rw in RACEWAYS:
        col = table9()[rw]
        row = {s: round(_ln_lerp(s, a, b, col[a], col[b]), 4) for s, (a, b) in _INTERP.items()}
        for s in _EXTRAP:
            row[s] = round(max(_ln_lerp(s, "750", "1000", col["750"], col["1000"]), floor_per_1000ft(s)), 4)
        out[rw] = row
    return out


def reactance_per_1000ft(size: str, raceway: str) -> tuple[float, bool] | None:
    """(XL ohm / 1000 ft, derived) for cable in conduit; None if neither table nor derivation covers it."""
    if raceway not in RACEWAYS:
        raise ValueError(f"conduit must be one of {RACEWAYS}")
    size = cond.normalize_size(size)
    x = table9()[raceway].get(size)
    if x is not None:
        return float(x), False
    x = derived_table()[raceway].get(size)
    return (x, True) if x is not None else None
