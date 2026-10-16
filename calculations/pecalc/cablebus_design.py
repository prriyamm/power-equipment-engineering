"""Cable bus designer: generate, check and rank complete design options.

For a required voltage and current, every practical combination of conductor
size, conductors per phase and stacked tiers (1 to 4) is laid out with the
code spacing (one cable diameter clear between cables and between tiers,
NEC 370 / CSA C22.2 No. 273 free-air basis), fitted into the smallest standard
enclosure, and run through the full cable bus analysis (phase-pattern search,
current sharing, ampacity, enclosure induced current, voltage drop). The best
options are then checked for short-circuit forces on the support blocks.

Enclosure sizes and clearances are catalogue/design inputs, not code values.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field, replace

from . import conductors as cond
from .cablebus import CableBusInput, analyse, construction, per_cable_ampacity, resolve_method
from .thermal import free_air_ampacity

# Typical support-block laminate properties (MPa). [UNVERIFIED: typical NEMA LI 1 / supplier
# datasheet values; use the block supplier's tested rating when available]
BLOCK_MATERIALS = {
    "GPO-3": {"tensile": 69.0, "flexural": 165.0, "compressive": 240.0},
    "GPO-2": {"tensile": 69.0, "flexural": 150.0, "compressive": 240.0},
    "GPO-1": {"tensile": 55.0, "flexural": 125.0, "compressive": 205.0},
}
INCH = 25.4


@dataclass
class DesignRequest:
    code: str = "NEC"
    voltage_v: float = 600.0
    current_a: float = 2000.0
    power_factor: float = 0.9
    frequency_hz: float = 60.0
    length_m: float = 60.0
    ambient_c: float = 40.0
    material: str = "Cu"
    sizes: tuple[str, ...] | None = None          # default: 500-1000 kcmil
    max_per_phase: int = 12
    extra_per_phase: int = 2                       # also try this many more than the minimum
    tier_options: tuple[int, ...] = (1, 2, 3, 4)
    ampacity_method: str = "auto"
    insulation_temp_c: int = 90
    terminal_temp_c: int = 90
    # MV cable construction (needed above 2000 V; same for every size of a voltage class)
    insulation: str = "XLPE"
    insulation_mm: float | None = None
    shield_mm: float = 0.0
    jacket_mm: float = 0.0
    jacket: str = "PVC"
    shield_bonding: str | None = None              # default: single_point above 2000 V, none below
    # Enclosure catalogue (inside dimensions, inches) and clearances
    enclosure_widths_in: tuple[float, ...] = (12, 18, 24, 30, 36, 42, 48)
    enclosure_heights_in: tuple[float, ...] = (6, 8, 10, 12, 14, 16)
    edge_clearance_mm: float = 25.0                # outer cable to side rail (block end) [design default]
    vertical_clearance_mm: float = 25.0            # block to cover / bottom [design default]
    block_lip_mm: float = 10.0                     # block material above/below the cable
    enclosure_alloy: str = "6063-T6"
    side_thickness_mm: float = 6.35
    covers_continuous: bool = False
    # Short circuit and support blocks
    fault_ka: float | None = None
    x_over_r: float = 15.0
    support_span_m: float = 0.9144
    block_material: str = "GPO-3"
    block_thickness_mm: float = 25.4               # block thickness along the run
    block_safety_factor: float = 2.0
    block_rated_load_n: float | None = None        # tested load per cable position, if known
    max_loading_pct: float = 95.0                  # design margin on the most loaded cable
    max_vd_pct: float = 3.0
    top_n: int = 8
    allow_placeholder_data: bool = False


@dataclass
class DesignOption:
    rank: int
    size: str
    per_phase: int
    tiers: int
    pattern: str
    enclosure_in: str
    inside_w_mm: float
    inside_h_mm: float
    cable_od_mm: float
    max_loading_pct: float
    vd_pct: float
    loss_kw: float
    enclosure_loss_kw: float
    copper_mm2_per_phase: float
    passed: bool
    failed_checks: list[str]
    block_load_n: float | None = None
    block_stress_mpa: float | None = None
    block_allowable_mpa: float | None = None
    tags: list[str] = field(default_factory=list)
    case_inputs: dict = field(default_factory=dict)

    @property
    def label(self) -> str:
        return (f"{self.per_phase} x {cond.size_label(self.size)} per phase, {self.tiers} tier(s), "
                f"{self.enclosure_in} enclosure")


@dataclass
class DesignResult:
    request: DesignRequest
    options: list[DesignOption]
    considered: int
    notes: list[str]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, default=str)


def _base_input(req: DesignRequest, size: str) -> CableBusInput:
    bonding = req.shield_bonding or ("single_point" if req.voltage_v > 2000 else "none")
    return CableBusInput(
        code=req.code, voltage_v=req.voltage_v, current_a=req.current_a, power_factor=req.power_factor,
        frequency_hz=req.frequency_hz, length_m=req.length_m, material=req.material, size=size,
        insulation_temp_c=req.insulation_temp_c, terminal_temp_c=req.terminal_temp_c, ambient_c=req.ambient_c,
        ampacity_method=req.ampacity_method, insulation=req.insulation, insulation_mm=req.insulation_mm,
        shield_mm=req.shield_mm, jacket_mm=req.jacket_mm, jacket=req.jacket, shield_bonding=bonding,
        max_vd_pct=req.max_vd_pct, enclosure_alloy=req.enclosure_alloy, side_thickness_mm=req.side_thickness_mm,
        covers_continuous=req.covers_continuous, x_over_r=req.x_over_r, support_span_m=req.support_span_m,
        allow_placeholder_data=req.allow_placeholder_data, field_distances_m=(1.0,))


def _cable_od(req: DesignRequest, base: CableBusInput) -> float:
    cons = construction(base)
    if cons:
        return cons.de_mm
    if req.voltage_v > 2000:
        raise ValueError("Above 2000 V give the cable construction (insulation_mm, shield_mm, jacket_mm)")
    return cond.cable_od_mm(base.size)


def _estimate_ampacity(base: CableBusInput, od: float) -> float:
    """Per-cable ampacity ignoring sharing imbalance and shield loss (screening only)."""
    if resolve_method(base) == "calculated":
        cons = construction(base)
        if cons is None:
            raise ValueError("Calculated ampacity needs the cable construction")
        return free_air_ampacity(cons, base.ambient_c, "isolated", 0.0, base.frequency_hz, 2 * od).ampacity_a
    return per_cable_ampacity(base)[0]


def _fit_enclosure(req: DesignRequest, per_tier: int, tiers: int, od: float) -> tuple[float, float] | None:
    pitch = 2 * od
    need_w = (per_tier - 1) * pitch + od + 2 * req.edge_clearance_mm
    need_h = (tiers - 1) * pitch + od + 2 * req.block_lip_mm + 2 * req.vertical_clearance_mm
    best = None
    for w in req.enclosure_widths_in:
        for h in req.enclosure_heights_in:
            if w * INCH >= need_w and h * INCH >= need_h and (best is None or w * h < best[0] * best[1]):
                best = (w, h)
    return best


def design_options(req: DesignRequest) -> DesignResult:
    sizes = [cond.normalize_size(s) for s in (req.sizes or ("500", "600", "750", "1000"))]
    notes: list[str] = []
    candidates = []
    considered = 0
    for size in sizes:
        base = _base_input(req, size)
        od = _cable_od(req, base)
        a_est = _estimate_ampacity(base, od)
        n_min = max(1, math.ceil(req.current_a / a_est))
        if n_min > req.max_per_phase:
            notes.append(f"{cond.size_label(size)}: needs {n_min} per phase (> {req.max_per_phase}); skipped.")
            continue
        for n in range(n_min, min(req.max_per_phase, n_min + req.extra_per_phase) + 1):
            for tiers in req.tier_options:
                if (3 * n) % tiers or ((3 * n) // tiers) % 3:
                    continue
                per_tier = 3 * n // tiers
                fit = _fit_enclosure(req, per_tier, tiers, od)
                if fit is None:
                    continue
                considered += 1
                inp = replace(base, conductors_per_phase=n, tiers=tiers, cable_od_mm=od,
                              enclosure_width_mm=fit[0] * INCH,
                              enclosure_height_mm=fit[1] * INCH)
                r = analyse(inp, compare_bonding=False)
                failed = [c["name"] for c in r.checks if not c["passed"]]
                if r.max_loading_pct > req.max_loading_pct:
                    failed.append(f"Loading above {req.max_loading_pct:g} %")
                candidates.append(DesignOption(
                    0, size, n, tiers, r.pattern, f'{fit[0]:g} x {fit[1]:g} in', round(fit[0] * INCH, 1),
                    round(fit[1] * INCH, 1), round(od, 1), r.max_loading_pct, r.vd_pct,
                    round((r.conductor_loss_w + r.shield_loss_w + r.enclosure_loss_w) / 1000, 2),
                    round(r.enclosure_loss_w / 1000, 2), round(cond.area_mm2(size) * n, 0), not failed, failed,
                    case_inputs={k: v for k, v in asdict(inp).items()}))

    passing = [c for c in candidates if c.passed]
    failing = [c for c in candidates if not c.passed]
    passing.sort(key=lambda c: (c.copper_mm2_per_phase, c.inside_w_mm * c.inside_h_mm, c.max_loading_pct))
    failing.sort(key=lambda c: c.max_loading_pct)
    ranked = passing[: req.top_n] + (failing[: max(0, req.top_n - len(passing))] if len(passing) < 3 else [])
    for i, c in enumerate(ranked, 1):
        c.rank = i

    if passing:
        least_cu = min(passing, key=lambda c: (c.copper_mm2_per_phase, c.inside_w_mm * c.inside_h_mm))
        smallest = min(passing, key=lambda c: (c.inside_w_mm * c.inside_h_mm, c.copper_mm2_per_phase))
        margin = min(passing, key=lambda c: (c.max_loading_pct, c.copper_mm2_per_phase))
        for c, tag in ((least_cu, "least copper"), (smallest, "smallest enclosure"), (margin, "most margin")):
            c.tags.append(tag)
            if c not in ranked:
                ranked.append(c)
        for i, c in enumerate(ranked, 1):
            c.rank = i

    if req.fault_ka:
        mat = BLOCK_MATERIALS.get(req.block_material)
        allow = mat["tensile"] / req.block_safety_factor if mat else None
        for c in ranked:
            inp = CableBusInput(**{**c.case_inputs, "fault_ka": req.fault_ka})
            r = analyse(inp, compare_bonding=False)
            load = r.fault_force_n_per_m * req.support_span_m          # N on one block at the worst cable
            ligament = min(r.pitch_mm - r.cable_od_mm, r.cable_od_mm)
            stress = load / (req.block_thickness_mm * ligament)          # N/mm2 = MPa
            c.block_load_n, c.block_stress_mpa = round(load), round(stress, 1)
            c.block_allowable_mpa = None if allow is None else round(allow, 1)
            if allow is not None and stress > allow:
                c.passed = False
                c.failed_checks.append(f"{req.block_material} block web stress {stress:.1f} > {allow:.1f} MPa")
            if req.block_rated_load_n and load > req.block_rated_load_n:
                c.passed = False
                c.failed_checks.append(f"Block load {load:.0f} N > rated {req.block_rated_load_n:.0f} N")
        notes.append(f"Support blocks: {req.block_material}, {req.block_thickness_mm:g} mm thick along the run, "
                     f"supports every {req.support_span_m:g} m. Web stress = peak cable force x span / "
                     f"(block thickness x ligament between cables), allowable = tensile strength / "
                     f"{req.block_safety_factor:g} [screening; material values UNVERIFIED]. A tested block "
                     "rating (CSA C22.2 No. 273 / IEEE C37.23 short-circuit test) governs.")
    notes.append("Enclosure sizes are a configurable catalogue (inside width x height, inches); clearances "
                 f"{req.edge_clearance_mm:g} mm to the side rails and {req.vertical_clearance_mm:g} mm to the covers "
                 "are design defaults, not code values.")
    notes.append("Spacing basis: one cable diameter clear between cables and between tiers (free-air rating, "
                 "NEC 370 / CSA C22.2 No. 273) [clause text UNVERIFIED].")
    if req.code == "CEC" and req.voltage_v <= 2000 and req.ampacity_method in ("auto", "table"):
        notes.append("CEC low-voltage table method requires the CSA C22.1 tables to be entered first.")
    return DesignResult(req, ranked, considered, notes)
