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
from .field import LIMITS_UT, b_rms_ut
from .forces import N_PER_M_TO_LBF_PER_FT, fault_forces
from .impedance import Conductor, Group, balanced_three_phase, solve_sharing
from .thermal import CableConstruction, free_air_ampacity

PHASES = ("A", "B", "C")
CU_RHO20 = 1.7241e-8  # ohm m, annealed copper (shield tapes / wires)
# Aluminum alloy resistivity at 20 C, ohm m, and temperature coefficient.
# [UNVERIFIED: typical handbook values, 6063-T6 ~53 % IACS, 6061-T6 ~43 % IACS]
AL_ALLOYS = {"6063-T6": 3.25e-8, "6061-T6": 3.99e-8, "1350": 2.82e-8}
AL_ALPHA = 0.0040


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
    # Ampacity method: "auto" (datasheet if given, else code table for LV, else
    # calculated), "table", "datasheet" or "calculated" (IEC 60287 thermal model).
    ampacity_method: str = "auto"
    cable_ampacity_a: float | None = None      # datasheet free-air rating per cable
    cable_ampacity_ambient_c: float = 40.0
    # Cable construction (needed for "calculated"; also gives OD and shield geometry).
    insulation: str = "XLPE"
    insulation_mm: float | None = None         # incl. conductor/insulation screens for MV
    shield_mm: float = 0.0
    jacket_mm: float = 0.0
    jacket: str = "PVC"
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
    # Enclosure (optional): inside width/height around the conductor group.
    # Side rails are continuous along the run; covers/bottom are included only
    # when electrically continuous (covers_continuous=True).
    enclosure_width_mm: float | None = None
    enclosure_height_mm: float | None = None
    side_thickness_mm: float = 6.35
    cover_thickness_mm: float = 3.175
    covers_continuous: bool = False
    enclosure_alloy: str = "6063-T6"
    enclosure_temp_c: float = 50.0
    enclosure_filaments: int = 6           # filaments per side/cover for the induced-current model
    field_distances_m: tuple[float, ...] = (0.3, 1.0)
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
    enclosure_loss_w: float
    enclosure_current_a: float
    field_ut: dict
    fault_force_n_per_m: float | None
    fault_force_lbf_per_ft: float | None
    support_load_lbf: float | None
    checks: list[dict]
    notes: list[str] = field(default_factory=list)
    cable_od_mm: float = 0.0
    pitch_mm: float = 0.0
    tier_pitch_mm: float = 0.0

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
    if inp.enclosure_width_mm:
        out += enclosure_filaments(inp, out, od)
    return out


def enclosure_filaments(inp: CableBusInput, cores: list[Conductor], od: float) -> list[Conductor]:
    """Thin-plate enclosure walls as parallel strips (bonded at both ends).

    Captures longitudinal induced current in the housing; transverse eddy
    currents within a strip are neglected (skin depth in Al at 60 Hz ~ 11 mm,
    larger than typical wall thickness).
    """
    if inp.enclosure_alloy not in AL_ALLOYS:
        raise ValueError(f"enclosure_alloy must be one of {sorted(AL_ALLOYS)}")
    phases = [c for c in cores if c.group in PHASES]
    xs = [c.x_mm for c in phases]
    ys = [c.y_mm for c in phases]
    xc, yc = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    w, h = inp.enclosure_width_mm, inp.enclosure_height_mm or (max(ys) - min(ys) + 2 * od)
    if w < max(xs) - min(xs) + od or h < max(ys) - min(ys) + od:
        raise ValueError(f"Enclosure {w:.0f} x {h:.0f} mm is smaller than the conductor group "
                         f"({max(xs) - min(xs) + od:.0f} x {max(ys) - min(ys) + od:.0f} mm)")
    rho = AL_ALLOYS[inp.enclosure_alloy] * (1 + AL_ALPHA * (inp.enclosure_temp_c - 20))
    n = inp.enclosure_filaments
    out = []

    def strips(x0, y0, x1, y1, t, tag):
        length = math.hypot(x1 - x0, y1 - y0)
        seg = length / n
        for k in range(n):
            f = (k + 0.5) / n
            out.append(Conductor(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, "ENCLOSURE",
                                 rho / (seg * t * 1e-6), 0.2235 * (seg + t), f"{tag}{k}"))

    ts, tc = inp.side_thickness_mm, inp.cover_thickness_mm
    xl, xr = xc - w / 2 - ts / 2, xc + w / 2 + ts / 2
    strips(xl, yc - h / 2, xl, yc + h / 2, ts, "EL")
    strips(xr, yc - h / 2, xr, yc + h / 2, ts, "ER")
    if inp.covers_continuous:
        yb, yt = yc - h / 2 - tc / 2, yc + h / 2 + tc / 2
        strips(xc - w / 2, yt, xc + w / 2, yt, tc, "ET")
        strips(xc - w / 2, yb, xc + w / 2, yb, tc, "EB")
    return out


def _groups(inp: CableBusInput, with_shields: bool) -> dict[str, Group]:
    g = balanced_three_phase(inp.current_a, inp.power_factor)
    if with_shields:
        g["SHIELD"] = Group("SHIELD", "bonded")
    if inp.enclosure_width_mm:
        g["ENCLOSURE"] = Group("ENCLOSURE", "bonded")
    return g


# --- ampacity ---------------------------------------------------------------

def construction(inp: CableBusInput) -> CableConstruction | None:
    if inp.insulation_mm is None:
        return None
    return CableConstruction(inp.size, inp.material, inp.insulation, inp.insulation_mm, inp.shield_mm,
                             inp.jacket_mm, inp.jacket, inp.voltage_v, inp.insulation_temp_c)


def resolve_method(inp: CableBusInput) -> str:
    m = inp.ampacity_method
    if m == "auto":
        if inp.cable_ampacity_a:
            return "datasheet"
        if inp.voltage_v <= 2000:
            return "table"
        return "calculated"
    if m not in ("table", "datasheet", "calculated"):
        raise ValueError("ampacity_method must be auto, table, datasheet or calculated")
    return m


def per_cable_ampacity(inp: CableBusInput) -> tuple[float, str]:
    if resolve_method(inp) == "datasheet":
        if not inp.cable_ampacity_a:
            raise ValueError("ampacity_method 'datasheet' needs cable_ampacity_a")
        f = amp.ambient_factor(inp.ambient_c, inp.insulation_temp_c, inp.cable_ampacity_ambient_c)
        return (inp.cable_ampacity_a * f,
                f"Supplied rating {inp.cable_ampacity_a:.0f} A at {inp.cable_ampacity_ambient_c:.0f} C "
                f"x ambient factor {f:.3f} ({inp.ambient_c:.0f} C)")
    if inp.voltage_v > 2000:
        raise ValueError("Code tables are loaded for <= 2000 V only; above that use the 'calculated' "
                         "method (give the cable construction) or 'datasheet' (give cable_ampacity_a)")
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
    cons = construction(inp)
    od = inp.cable_od_mm or (cons.de_mm if cons else None) or (cond.cable_od_mm(size) if inp.voltage_v <= 2000 else None)
    if od is None:
        raise ValueError("Above 2000 V give cable_od_mm or the cable construction (insulation_mm, shield_mm, jacket_mm)")
    with_shields = inp.shield_bonding == "both_ends"
    if with_shields and cons and cons.shield_mm:
        inp.shield_mean_diameter_mm = inp.shield_mean_diameter_mm or cons.shield_mean_diameter_mm
        inp.shield_area_mm2 = inp.shield_area_mm2 or math.pi * cons.shield_mean_diameter_mm * cons.shield_mm
    method = resolve_method(inp)
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

    pitch = inp.spacing_mm or 2 * od
    labels = {c.label: i for i, c in enumerate(cs)}
    a_term = None
    if method == "calculated":
        if cons is None:
            raise ValueError("The calculated ampacity method needs the cable construction (insulation_mm etc.)")
        installation = "isolated" if pitch - od >= 0.75 * od else "flat_touching"
        cache: dict[float, object] = {}

        def ampacity_for(i: int):
            core_loss = res.losses_w_per_m[i]
            s = labels.get(f"S-{cs[i].label}")
            lam = round(res.losses_w_per_m[s] / core_loss, 4) if s is not None and core_loss else 0.0
            if lam not in cache:
                cache[lam] = free_air_ampacity(cons, inp.ambient_c, installation, lam, inp.frequency_hz, pitch)
            return cache[lam]
        notes.append("Calculated ampacity (IEC 60287 / Neher-McGrath thermal model) is permitted by NEC 310.14(B) / "
                     "315.60(B) under engineering supervision; model constants are UNVERIFIED pending check against "
                     "IEC 60287. Each cable's own shield loss factor (lambda1) from the sharing solve is included.")
    else:
        a_cable, basis_fixed = per_cable_ampacity(inp)
        if method == "table":
            a_term = amp.table_ampacity(inp.code, "free_air", inp.material, size, inp.terminal_temp_c)

    rows = []
    worst = None
    for i, c in enumerate(cs):
        if c.group not in PHASES:
            continue
        cur = abs(res.currents[i])
        if method == "calculated":
            ar = ampacity_for(i)
            a_i, basis_i = ar.ampacity_a, ar.summary()
        else:
            a_i, basis_i = a_cable, basis_fixed
        row = ConductorRow(i, c.group, round(c.y_mm / (inp.tier_spacing_mm or pitch)),
                           round(c.x_mm, 1), round(c.y_mm, 1), round(cur, 1),
                           round(res.share_pct(i), 1), round(a_i, 1), round(cur / a_i * 100, 1))
        rows.append(row)
        if worst is None or row.loading_pct > worst[0].loading_pct:
            worst = (row, basis_i)
    max_cur = max(r.current_a for r in rows)
    max_loading = worst[0].loading_pct
    basis = worst[1]

    # Voltage drop: worst phase, sending-end phase voltage as reference.
    v_ph = inp.voltage_v / math.sqrt(3)
    vd_pct = max((v_ph - abs(v_ph - d * inp.length_m)) / v_ph * 100
                 for d in res.group_drop_v_per_m.values())
    cond_loss = res.group_loss_w_per_m("phase") * inp.length_m
    shield_loss = sum(p for p, c in zip(res.losses_w_per_m, cs) if c.group == "SHIELD") * inp.length_m
    encl_loss = sum(p for p, c in zip(res.losses_w_per_m, cs) if c.group == "ENCLOSURE") * inp.length_m
    shield_i = max((abs(res.currents[i]) for i, c in enumerate(cs) if c.group == "SHIELD"), default=0.0)
    encl_i = max((abs(sum(res.currents[i] for i, c in enumerate(cs) if c.label.startswith(side)))
                  for side in ("EL", "ER", "ET", "EB")), default=0.0) if inp.enclosure_width_mm else 0.0

    # Magnetic field beside and above the group, measured from the outer surface.
    xs = [c.x_mm for c in cs]
    ys = [c.y_mm for c in cs]
    right, top = max(xs) + od / 2, max(ys) + od / 2
    xmid, ymid = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    field_ut = {}
    for d in inp.field_distances_m:
        field_ut[f"side {d:g} m"] = round(b_rms_ut(cs, res.currents, right + d * 1000, ymid), 2)
        field_ut[f"top {d:g} m"] = round(b_rms_ut(cs, res.currents, xmid, top + d * 1000), 2)

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
    if method == "table":
        check("Spacing for free-air ampacity basis (>= 1 cable diameter clearance)",
              "NEC 370.80 / CEC 12-2252 [UNVERIFIED]", pitch - od, od, "mm", pitch - od >= od - 1e-6)
    w = worst[0]
    check("Most heavily loaded conductor within its ampacity", basis, w.current_a, w.ampacity_a, "A",
          w.current_a <= w.ampacity_a, f"{w.phase} at x={w.x_mm} mm; current sharing solved for pattern {pattern}")
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
    if method == "table":
        notes.append(f"{inp.code} table data status: {amp.table_info(inp.code, 'free_air').status}.")
    if inp.enclosure_width_mm:
        notes.append(f"Enclosure ({inp.enclosure_alloy}, sides{' + covers' if inp.covers_continuous else ' only'}): "
                     f"induced current up to {encl_i:.0f} A per wall, loss {encl_loss/1000:.2f} kW "
                     f"({encl_loss / max(cond_loss, 1e-9) * 100:.1f} % of conductor loss). Longitudinal circulating "
                     "current only; transverse eddy and hysteresis (none in Al) not included.")
    else:
        notes.append("Enclosure not modelled (give enclosure_width_mm to include induced housing currents).")
    if field_ut:
        worst_b = max(field_ut.values())
        notes.append("Magnetic field (RMS resultant) " + ", ".join(f"{k}: {v} uT" for k, v in field_ut.items()) +
                     f". Reference levels at 60 Hz: ICNIRP 1998 public {LIMITS_UT['ICNIRP 1998 public']} uT, "
                     f"occupational {LIMITS_UT['ICNIRP 1998 occupational']} uT"
                     f"{' - EXCEEDS public level' if worst_b > LIMITS_UT['ICNIRP 1998 public'] else ''}.")

    width = max(r.x_mm for r in rows) + od
    height = max(r.y_mm for r in rows) + od
    return CableBusResult(inp, pattern, compared, round(width, 1), round(height, 1), rows, basis,
                          round(max_loading, 1), round(vd_pct, 3), round(cond_loss, 1), round(shield_loss, 1),
                          round(shield_i, 1), round(encl_loss, 1), round(encl_i, 1), field_ut,
                          None if f_nm is None else round(f_nm, 1),
                          None if f_lbf is None else round(f_lbf, 1), None if support is None else round(support, 1),
                          checks, notes, round(od, 2), round(pitch, 2), round(inp.tier_spacing_mm or pitch, 2))
