"""Cable bus design check, any voltage (600 V to 35 kV class) and rating.

Builds the conductor layout (tiers, spacing, phase pattern), solves current
sharing among paralleled conductors and induced shield currents with the
multi-conductor impedance model, then checks each conductor against its
ampacity, and reports voltage drop, losses and short-circuit forces.

Ampacity per conductor comes from either:
- the code free-air table (LV conductors, <= 2000 V), or
- a per-cable rating the caller supplies (manufacturer datasheet free-air
  rating, or a calculated Neher-McGrath / IEC 60287 value), with its reference
  ambient and conductor temperature so it can be corrected to site ambient.
Calculated (thermal-model) ampacity is on the roadmap.
"""

from __future__ import annotations

import cmath
import itertools
import json
import math
from dataclasses import asdict, dataclass, field

from . import ampacity as amp
from . import conductors as cond
from .forces import N_PER_M_TO_LBF_PER_FT, fault_forces
from .impedance import Conductor, Group, balanced_three_phase, solve_sharing

PHASES = ("A", "B", "C")
CU_RHO20 = 1.7241e-8  # ohm m, annealed copper (shield tapes / wires)


@dataclass
class CableBusInput:
    code: str = "NEC"
    voltage_v: float = 600.0           # line-to-line
    current_a: float = 2000.0          # system rating per phase
    power_factor: float = 0.9
    frequency_hz: float = 60.0
    length_m: float = 60.0
    material: str = "Cu"
    size: str = "750"
    conductors_per_phase: int = 3
    tiers: int = 1
    cable_od_mm: float | None = None   # required above 2000 V; estimated for LV if omitted
    spacing_mm: float | None = None    # centre-to-centre in a tier; default 2 x OD (1 OD clearance)
    tier_spacing_mm: float | None = None  # centre-to-centre between tiers; default = spacing
    pattern: str = "auto"              # e.g. "ABCCBA" or "ABCCBA/CBAABC" for tiers, or "auto"
    insulation_temp_c: int = 90
    terminal_temp_c: int = 90          # equipment termination rating (NEC 110.14(C) / CEC 4-006)
    ambient_c: float = 40.0
    # Datasheet / calculated ampacity per cable (overrides the code table).
    cable_ampacity_a: float | None = None
    cable_ampacity_ambient_c: float = 40.0
    # MV shields: "none", "single_point" (no circulating current) or "both_ends".
    shield_bonding: str = "none"
    shield_area_mm2: float | None = None   # copper tape/wire cross-section per cable
    shield_mean_diameter_mm: float | None = None
    shield_temp_c: float = 80.0
    # Short circuit
    fault_ka: float | None = None
    x_over_r: float = 15.0
    support_span_m: float = 0.9144     # block / support spacing along the run (36 in)
    max_vd_pct: float = 3.0
    allow_placeholder_data: bool = False


@dataclass
class ConductorRow:
    index: int
    phase: str
    tier: int
    x_mm: float
    y_mm: float
    current_a: float
    share_pct: float
    ampacity_a: float
    loading_pct: float


@dataclass
class PatternScore:
    pattern: str
    max_share_pct: float
    loss_w_per_m: float


@dataclass
class CableBusResult:
    input: CableBusInput
    pattern: str
    patterns_compared: list[PatternScore]
    layout_width_mm: float
    layout_height_mm: float
    conductors: list[ConductorRow]
    ampacity_basis: str
    max_loading_pct: float
    vd_pct: float
    conductor_loss_w: float
    shield_loss_w: float
    shield_current_a: float
    fault_force_n_per_m: float | None
    fault_force_lbf_per_ft: float | None
    support_load_lbf: float | None
    checks: list[dict]
    notes: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c["passed"] for c in self.checks)

    def to_json(self) -> str:
        return json.dumps(asdict(self) | {"passed": self.passed}, indent=2, default=str)


# --- layout -----------------------------------------------------------------

def candidate_patterns(n_per_phase: int, tiers: int) -> list[str]:
    total = 3 * n_per_phase
    if total % tiers:
        raise ValueError(f"{total} conductors cannot be split evenly into {tiers} tiers")
    per_tier = total // tiers
    if per_tier % 3:
        raise ValueError(f"Each tier needs a multiple of 3 conductors (got {per_tier})")
    k = per_tier // 3
    seq = "ABC" * k
    mirrored = "".join("ABC" if i % 2 == 0 else "CBA" for i in range(k))
    rows = {
        "sequential": [seq] * tiers,
        "mirrored": [mirrored] * tiers,
        "mirrored, alternate tiers reversed": [mirrored if t % 2 == 0 else mirrored[::-1] for t in range(tiers)],
        "mirrored, alternate tiers rotated": [
            mirrored if t % 2 == 0 else mirrored.translate(str.maketrans("ABC", "CAB")) for t in range(tiers)],
    }
    out = []
    for r in rows.values():
        p = "/".join(r)
        if p not in out:
            out.append(p)
    return out


def _check_pattern(pattern: str, n_per_phase: int, tiers: int) -> list[str]:
    rows = pattern.upper().split("/")
    if len(rows) != tiers:
        raise ValueError(f"Pattern {pattern!r} has {len(rows)} tiers, expected {tiers}")
    flat = "".join(rows)
    for p in PHASES:
        if flat.count(p) != n_per_phase:
            raise ValueError(f"Pattern {pattern!r} must contain {n_per_phase} x {p}")
    if set(flat) - set(PHASES):
        raise ValueError("Pattern may contain only A, B, C and '/'")
    return rows


def build_layout(inp: CableBusInput, pattern: str, od: float) -> list[Conductor]:
    rows = _check_pattern(pattern, inp.conductors_per_phase, inp.tiers)
    pitch = inp.spacing_mm or 2 * od
    tier_pitch = inp.tier_spacing_mm or pitch
    r_core = cond.rac_ohm_per_m(inp.size, inp.material, inp.insulation_temp_c, inp.frequency_hz,
                                spacing_mm=pitch)
    gmr = cond.gmr_mm(inp.size)
    out = []
    for t, row in enumerate(rows):
        for i, ph in enumerate(row):
            out.append(Conductor(i * pitch, t * tier_pitch, ph, r_core, gmr, f"{ph}{t}{i}"))
    if inp.shield_bonding == "both_ends":
        if not (inp.shield_area_mm2 and inp.shield_mean_diameter_mm):
            raise ValueError("shield_area_mm2 and shield_mean_diameter_mm are required for both-ends bonding")
        rs = CU_RHO20 * (1 + 0.00393 * (inp.shield_temp_c - 20)) / (inp.shield_area_mm2 * 1e-6)
        rad = inp.shield_mean_diameter_mm / 2
        for c in list(out):
            out.append(Conductor(c.x_mm, c.y_mm, "SHIELD", rs, rad, f"S-{c.label}", tube_radius_mm=rad))
    return out


def _groups(inp: CableBusInput, with_shields: bool) -> dict[str, Group]:
    g = balanced_three_phase(inp.current_a, inp.power_factor)
    if with_shields:
        g["SHIELD"] = Group("SHIELD", "bonded")
    return g


# --- ampacity ---------------------------------------------------------------

def per_cable_ampacity(inp: CableBusInput) -> tuple[float, str]:
    if inp.cable_ampacity_a:
        f = amp.ambient_factor(inp.ambient_c, inp.insulation_temp_c, inp.cable_ampacity_ambient_c)
        return (inp.cable_ampacity_a * f,
                f"Supplied rating {inp.cable_ampacity_a:.0f} A at {inp.cable_ampacity_ambient_c:.0f} C "
                f"x ambient factor {f:.3f} ({inp.ambient_c:.0f} C)")
    if inp.voltage_v > 2000:
        raise ValueError("Above 2000 V supply cable_ampacity_a (datasheet free-air rating); "
                         "MV code tables and the calculated-ampacity model are not loaded yet")
    amp.check_status(inp.code, inp.allow_placeholder_data)
    base = amp.table_ampacity(inp.code, "free_air", inp.material, inp.size, inp.insulation_temp_c)
    if base is None:
        raise ValueError(f"No free-air ampacity for {inp.material} {inp.size}")
    info = amp.table_info(inp.code, "free_air")
    rated = _load_rated_ambient(inp.code)
    f = amp.ambient_factor(inp.ambient_c, inp.insulation_temp_c, rated)
    return base * f, (f"{inp.code} {info.table_name} {base:.0f} A ({inp.insulation_temp_c} C column, "
                      f"data {info.status}) x ambient factor {f:.3f} ({inp.ambient_c:.0f} C)")


def _load_rated_ambient(code: str) -> float:
    return float(json.loads((amp.DATA / f"ampacity_{code.lower()}.json").read_text())["_meta"]["rated_ambient_c"])


# --- main -------------------------------------------------------------------

def analyse(inp: CableBusInput) -> CableBusResult:
    size = cond.normalize_size(inp.size)
    inp.size = size
    od = inp.cable_od_mm or (cond.cable_od_mm(size) if inp.voltage_v <= 2000 else None)
    if od is None:
        raise ValueError("cable_od_mm is required above 2000 V (take it from the cable datasheet)")
    with_shields = inp.shield_bonding == "both_ends"
    notes: list[str] = []

    patterns = (candidate_patterns(inp.conductors_per_phase, inp.tiers) if inp.pattern == "auto"
                else [inp.pattern.upper()])
    scored = []
    for p in patterns:
        cs = build_layout(inp, p, od)
        res = solve_sharing(cs, _groups(inp, with_shields), inp.frequency_hz)
        phase_idx = [i for i, c in enumerate(cs) if c.group in PHASES]
        scored.append((p, cs, res, max(res.share_pct(i) for i in phase_idx), sum(res.losses_w_per_m)))
    scored.sort(key=lambda s: (round(s[3], 1), s[4]))
    pattern, cs, res, _, _ = scored[0]
    compared = [PatternScore(p, round(m, 1), round(l, 2)) for p, _, _, m, l in scored]

    a_cable, basis = per_cable_ampacity(inp)
    a_term = None
    if not inp.cable_ampacity_a and inp.voltage_v <= 2000:
        a_term = amp.table_ampacity(inp.code, "free_air", inp.material, size, inp.terminal_temp_c)

    rows = []
    for i, c in enumerate(cs):
        if c.group not in PHASES:
            continue
        cur = abs(res.currents[i])
        rows.append(ConductorRow(i, c.group, round(c.y_mm / (inp.tier_spacing_mm or inp.spacing_mm or 2 * od)),
                                 round(c.x_mm, 1), round(c.y_mm, 1), round(cur, 1),
                                 round(res.share_pct(i), 1), round(a_cable, 1), round(cur / a_cable * 100, 1)))
    max_cur = max(r.current_a for r in rows)
    max_loading = max(r.loading_pct for r in rows)

    # Voltage drop: worst phase, sending-end phase voltage as reference.
    v_ph = inp.voltage_v / math.sqrt(3)
    vd_pct = max((v_ph - abs(v_ph - d * inp.length_m)) / v_ph * 100
                 for d in res.group_drop_v_per_m.values())
    cond_loss = res.group_loss_w_per_m("phase") * inp.length_m
    shield_loss = res.group_loss_w_per_m("bonded") * inp.length_m
    shield_i = max((abs(res.currents[i]) for i, c in enumerate(cs) if c.group == "SHIELD"), default=0.0)

    clauses = amp.CLAUSES[inp.code]
    checks = []

    def check(name, clause, value, limit, unit, passed, note=""):
        checks.append({"name": name, "clause": clause, "value": round(value, 2), "limit": round(limit, 2),
                       "unit": unit, "passed": bool(passed), "note": note})

    min_size = amp.PARALLEL_MIN[inp.code][inp.material]
    if inp.conductors_per_phase > 1:
        check("Minimum size for paralleled conductors", clauses["parallel"], cond.size_index(size),
              cond.size_index(min_size), "size index", cond.size_index(size) >= cond.size_index(min_size),
              f"min {cond.size_label(min_size)}")
    pitch = inp.spacing_mm or 2 * od
    if not inp.cable_ampacity_a:
        check("Spacing for free-air ampacity basis (>= 1 cable diameter clearance)",
              "NEC 370.80 / CEC 12-2252 [UNVERIFIED]", pitch - od, od, "mm", pitch - od >= od - 1e-6)
    check("Most heavily loaded conductor within ampacity", basis, max_cur, a_cable, "A", max_cur <= a_cable,
          f"current sharing solved for pattern {pattern}")
    if a_term is not None:
        check("Most heavily loaded conductor within termination rating", clauses["terminal"], max_cur, a_term,
              "A", max_cur <= a_term, f"{inp.terminal_temp_c} C column, no ambient correction")
    check("Voltage drop (worst phase)", clauses["vd"], vd_pct, inp.max_vd_pct, "%", vd_pct <= inp.max_vd_pct)

    f_nm = f_lbf = support = None
    if inp.fault_ka:
        phase_idx = [i for i, c in enumerate(cs) if c.group in PHASES]
        share = {}
        for i in phase_idx:
            share[i] = res.currents[i] / res.groups[cs[i].group].current
        fr = fault_forces(cs, share, inp.fault_ka, inp.x_over_r, inp.frequency_hz)
        f_nm, f_lbf = fr.worst_n_per_m, fr.worst_lbf_per_ft
        support = fr.worst_n_per_m * inp.support_span_m / 4.44822
        notes.append(f"Fault: {inp.fault_ka} kA rms sym, X/R {inp.x_over_r}, first peak {fr.peak_current_ka:.1f} kA; "
                     f"worst conductor force {f_nm:.0f} N/m ({f_lbf:.0f} lbf/ft); load on one support over a "
                     f"{inp.support_span_m:.3f} m span ~ {support:.0f} lbf (static; compare with tested block strength).")

    if with_shields:
        notes.append(f"Shields bonded both ends: max circulating current {shield_i:.0f} A, "
                     f"shield loss {shield_loss/1000:.2f} kW ({shield_loss / max(cond_loss, 1e-9) * 100:.1f} % of "
                     f"conductor loss). Single-point or cross bonding removes most of this.")
    if inp.voltage_v > 2000 and inp.shield_bonding == "none":
        notes.append("MV cable selected with shield_bonding 'none': set 'single_point' or 'both_ends' to state the design.")
    if not inp.cable_ampacity_a:
        notes.append(f"{inp.code} table data status: {amp.table_info(inp.code, 'free_air').status}.")
    notes.append("Enclosure losses (eddy currents in the aluminum housing) are not yet included.")

    width = max(r.x_mm for r in rows) + od
    height = max(r.y_mm for r in rows) + od
    return CableBusResult(inp, pattern, compared, round(width, 1), round(height, 1), rows, basis,
                          round(max_loading, 1), round(vd_pct, 3), round(cond_loss, 1), round(shield_loss, 1),
                          round(shield_i, 1), None if f_nm is None else round(f_nm, 1),
                          None if f_lbf is None else round(f_lbf, 1), None if support is None else round(support, 1),
                          checks, notes)
