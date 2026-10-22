"""Lug and termination selection.

Rules-based selection of lug style, material, stud size, hole pattern and
quantity for each termination, plus the termination temperature rule
(NEC 110.14(C) / CEC Rule 4-006). Part numbers, die codes and torque come
only from a catalogue file (data/lug_catalog.json) the user fills from the
manufacturer's current catalogue and installation sheets; without it the
result says "use the manufacturer's value" rather than inventing one.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from . import conductors as cond
from . import validate
from .ampacity import CODES, COLUMNS, DATA

# Typical stud size and 2-hole spacing by conductor size for NEMA-pattern
# compression lugs. [UNVERIFIED: industry practice from catalogue listings;
# 1/2 in stud on 1-3/4 in centres confirmed in product listings only]
_STUD_RULES = (
    (("14", "12", "10", "8"), "1/4", "5/8"),
    (("6", "4", "3", "2"), "3/8", "1"),
    (("1",) + cond.SIZES[cond.SIZES.index("1/0"):], "1/2", "1-3/4"),
)


@dataclass
class LugInput:
    code: str = "NEC"
    size: str = "500"
    material: str = "Cu"
    sets_per_phase: int = 1
    phases: int = 3
    neutral: bool = False
    neutral_size: str | None = None
    ground_size: str | None = None
    circuit_current_a: float = 400.0
    equipment_terminal_temp_c: int | None = None   # marked rating; None = code default
    termination: str = "bus"                         # "bus" (NEMA pad), "stud", "breaker" (mechanical lug)
    pad_positions: int | None = None                 # 2-hole positions available per phase on the pad
    pad_two_sided: bool = True                       # lugs may mount on both faces of the pad


@dataclass
class LugLine:
    terminal: str
    conductor: str
    quantity: int
    style: str
    lug_material: str
    stud_in: str
    hole_spacing_in: str | None
    part_no: str | None = None
    die: str | None = None
    torque: str | None = None


@dataclass
class LugResult:
    input: LugInput
    terminal_temp_c: int
    terminal_temp_basis: str
    lines: list[LugLine]
    total_lugs: int
    checks: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c["passed"] for c in self.checks)

    def to_json(self) -> str:
        return json.dumps(asdict(self) | {"passed": self.passed}, indent=2, default=str)


def default_terminal_temp(code: str, circuit_a: float, size: str) -> tuple[int, str]:
    """NEC 110.14(C)(1) / CEC 4-006(2): 60 C for <= 100 A or 14-1 AWG, else 75 C,
    unless the equipment is marked otherwise. [UNVERIFIED wording; CEC 2018 text checked]"""
    small = circuit_a <= 100 or cond.size_index(size) <= cond.size_index("1")
    clause = "NEC 110.14(C)(1)" if code == "NEC" else "CEC Rule 4-006"
    if small:
        return 60, f"{clause}: 100 A or less, or 14-1 AWG, defaults to 60 C unless marked"
    return 75, f"{clause}: over 100 A or larger than 1 AWG defaults to 75 C unless marked"


def stud_for(size: str) -> tuple[str, str]:
    size = cond.normalize_size(size)
    for sizes, stud, spacing in _STUD_RULES:
        if size in sizes:
            return stud, spacing
    raise AssertionError(size)


def _catalog() -> dict:
    p = DATA / "lug_catalog.json"
    return json.loads(p.read_text()) if p.exists() else {"_meta": {"status": "EMPTY"}, "lugs": []}


def _lookup(material: str, size: str, stud: str, holes: int) -> dict | None:
    for row in _catalog()["lugs"]:
        if (row["conductor_material"] == material and cond.normalize_size(row["size"]) == size
                and row["stud_in"] == stud and row["holes"] == holes):
            return row
    return None


def _line(terminal: str, size: str, material: str, qty: int, termination: str) -> LugLine:
    size = cond.normalize_size(size)
    stud, spacing = stud_for(size)
    if termination == "breaker":
        style, holes, spacing = "mechanical (set-screw) lug supplied/listed with the device", 0, None
        stud = "per device"
    elif termination == "bus" and cond.size_index(size) >= cond.size_index("1/0"):
        style, holes = "compression, 2-hole long barrel, NEMA spacing", 2
    else:
        style, holes, spacing = "compression, 1-hole long barrel", 1, None
    lug_mat = ("tin-plated copper" if material == "Cu"
               else "tin-plated aluminum, dual-rated AL9CU; apply oxide inhibitor")
    row = _lookup(material, size, stud, holes) if holes else None
    return LugLine(terminal, f"{cond.size_label(size)} {material}", qty, style, lug_mat, stud, spacing,
                   row.get("part_no") if row else None, row.get("die") if row else None,
                   row.get("torque") if row else None)


def select_lugs(inp: LugInput) -> LugResult:
    size = cond.normalize_size(inp.size)
    validate.one_of("code", inp.code, CODES)
    validate.one_of("material", inp.material, tuple(cond.MATERIALS))
    validate.integer_at_least("sets_per_phase", inp.sets_per_phase, 1)
    validate.one_of("phases", inp.phases, (1, 3))
    validate.positive("circuit_current_a", inp.circuit_current_a, "A")
    if inp.equipment_terminal_temp_c is not None:
        validate.one_of("equipment_terminal_temp_c", inp.equipment_terminal_temp_c, COLUMNS)
    if inp.equipment_terminal_temp_c is not None:
        t_term, basis = inp.equipment_terminal_temp_c, "equipment marking"
    else:
        t_term, basis = default_terminal_temp(inp.code, inp.circuit_current_a, size)

    lines = [_line(f"Phase ({inp.phases} x {inp.sets_per_phase} per phase)", size, inp.material,
                   inp.phases * inp.sets_per_phase, inp.termination)]
    if inp.neutral:
        lines.append(_line(f"Neutral ({inp.sets_per_phase})", inp.neutral_size or size, inp.material,
                           inp.sets_per_phase, inp.termination))
    if inp.ground_size:
        lines.append(_line("Equipment ground", inp.ground_size, inp.material, inp.sets_per_phase, "bus"))
    total = sum(l.quantity for l in lines)

    checks, notes = [], []
    if inp.pad_positions is not None and inp.termination == "bus":
        capacity = inp.pad_positions * (2 if inp.pad_two_sided else 1)
        checks.append({"name": "Lugs per phase fit the pad", "clause": "equipment pad drawing",
                       "value": inp.sets_per_phase, "limit": capacity, "unit": "lugs", "passed":
                       inp.sets_per_phase <= capacity,
                       "note": f"{inp.pad_positions} two-hole positions x {'2 faces' if inp.pad_two_sided else '1 face'}"})
    if inp.sets_per_phase > 1 and cond.size_index(size) < cond.size_index("1/0"):
        checks.append({"name": "Paralleled conductors 1/0 AWG or larger", "clause": "NEC 310.10(G) / CEC 12-108",
                       "value": cond.size_index(size), "limit": cond.size_index("1/0"), "unit": "size index",
                       "passed": False})
    cat = _catalog()["_meta"].get("status", "EMPTY")
    if any(l.torque is None for l in lines):
        notes.append("Torque: use the value marked on the equipment or in the lug manufacturer's installation "
                     "sheet (UL 486A-B tables apply only when none is marked). Add parts to "
                     "data/lug_catalog.json to have part numbers, dies and torques filled in.")
    notes.append(f"Lug catalogue status: {cat}. Stud/spacing defaults are typical practice [UNVERIFIED].")
    notes.append("Wire bending space (NEC 312.6 / CEC Table 37, UL 891 / UL 1558) is not checked yet.")
    if inp.material == "Al":
        notes.append("Aluminum: use lugs marked AL9CU (or AL7CU) for the conductor, Belleville washers on bolted "
                     "joints, and oxide-inhibiting compound.")
    return LugResult(inp, t_term, basis, lines, total, checks, notes)
