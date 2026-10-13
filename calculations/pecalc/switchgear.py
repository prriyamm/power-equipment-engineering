"""Switchgear / switchboard bus: current distribution, temperature rise, bracing.

Rectangular bars (one or more laminations per phase) are split into
filaments and solved with the multi-conductor impedance model, so skin and
proximity effects and the current split between laminations come out of the
same engine used for cable bus. Then:

- Temperature rise: steady heat balance per phase pack, natural convection
  (simplified air correlations, Holman / McAdams: vertical 1.42 (dT/L)^0.25,
  heated face up 1.32 (dT/L)^0.25, heated face down 0.59 (dT/L)^0.25 W/m2K)
  plus radiation from the outer envelope. Inner lamination faces are counted
  at 50 % for convection and 0 % for radiation [UNVERIFIED approximation].
- Short-circuit: time-domain forces on each phase pack (shared force solver),
  then beam bending of the bars between supports and the support reaction
  (3+ equal continuous spans: M = F L^2 / 10, R = 1.1 F L; single span
  pinned: F L^2 / 8, R = F L / 2; fixed-fixed: F L^2 / 12, R = F L / 2),
  the same structure as IEEE 605's span equation.

Temperature-rise limits (UL 891, ANSI C37.20.1/.2/.3) were not verified during
research, so the allowable rise is an input with a flagged default.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field

from . import validate
from .forces import N_PER_M_TO_LBF_PER_FT, fault_forces
from .impedance import Conductor, balanced_three_phase, solve_sharing

SIGMA = 5.670e-8
# Resistivity at 20 C (ohm m) and temperature coefficient. [UNVERIFIED: handbook
# values for C11000 (101 % IACS) and 6101-T61 (57 % IACS)]
BAR_MATERIALS = {"Cu": (1.7241e-8 / 1.01, 0.00393), "Al": (3.02e-8, 0.00403)}
# Typical yield strength, MPa [UNVERIFIED: supplier data varies by temper; give your own]
YIELD_MPA = {"Cu": 200.0, "Al": 165.0}
# Surface emissivity by finish [UNVERIFIED typical values]
EMISSIVITY = {"bare": 0.4, "tin": 0.3, "silver": 0.1, "painted": 0.9}
SPAN = {"continuous": (10.0, 1.1), "pinned": (8.0, 0.5), "fixed": (12.0, 0.5)}


@dataclass
class BusInput:
    current_a: float = 2000.0
    voltage_v: float = 600.0
    standard: str = "UL 891"
    material: str = "Cu"
    bar_thickness_mm: float = 6.35
    bar_width_mm: float = 101.6
    bars_per_phase: int = 2
    bar_gap_mm: float | None = None        # between laminations; default = thickness
    phase_spacing_mm: float = 150.0        # centre-to-centre between phase packs
    orientation: str = "face_to_face"      # bar faces toward the next phase (weak axis loaded)
                                           # or "edge_to_edge" (bar edges toward next phase)
    finish: str = "tin"
    ambient_c: float = 40.0
    internal_air_rise_c: float = 0.0       # enclosure air above room ambient
    max_rise_c: float = 65.0               # [UNVERIFIED default; confirm against UL 891 / C37.20.x]
    frequency_hz: float = 60.0
    filaments_thickness: int | None = None  # None: adapt to skin depth
    filaments_width: int | None = None
    fault_ka: float | None = None
    x_over_r: float = 15.0
    support_span_m: float = 0.6
    support_condition: str = "continuous"
    yield_mpa: float | None = None
    support_rating_n: float | None = None  # rated cantilever / working load of one support


@dataclass
class BusResult:
    input: BusInput
    rac_over_rdc: float
    lamination_share_pct: list[float]
    loss_w_per_m_per_phase: float
    rise_c: float
    rated_current_at_limit_a: float
    peak_force_n_per_m: float | None
    bending_stress_mpa: float | None
    support_load_n: float | None
    max_span_m: float | None
    checks: list[dict]
    notes: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c["passed"] for c in self.checks)

    def to_json(self) -> str:
        return json.dumps(asdict(self) | {"passed": self.passed}, indent=2, default=str)


def skin_depth_mm(material: str, temp_c: float, freq: float) -> float:
    rho20, alpha = BAR_MATERIALS[material]
    rho = rho20 * (1 + alpha * (temp_c - 20))
    return math.sqrt(rho / (math.pi * freq * 4e-7 * math.pi)) * 1000


def mesh(inp: BusInput, temp_c: float) -> tuple[int, int]:
    """Filaments per bar: about one skin depth across the width, >= 2 across thickness."""
    d = skin_depth_mm(inp.material, temp_c, inp.frequency_hz)
    nt = inp.filaments_thickness or min(4, max(2, math.ceil(inp.bar_thickness_mm / d) + 1))
    nw = inp.filaments_width or min(24, max(4, math.ceil(inp.bar_width_mm / d)))
    return nt, nw


def _layout(inp: BusInput, nt: int, nw: int, temp_c: float) -> tuple[list[Conductor], dict[int, str]]:
    rho20, alpha = BAR_MATERIALS[inp.material]
    rho = rho20 * (1 + alpha * (temp_c - 20))
    t, w = inp.bar_thickness_mm, inp.bar_width_mm
    gap = inp.bar_gap_mm if inp.bar_gap_mm is not None else t
    n = inp.bars_per_phase
    dt, dw = t / nt, w / nw
    r_fil = rho / (dt * dw * 1e-6)
    gmr = 0.2235 * (dt + dw)
    cs, bodies = [], {}
    for p, ph in enumerate("ABC"):
        xc = p * inp.phase_spacing_mm
        pack = n * t + (n - 1) * gap
        for b in range(n):
            off = -pack / 2 + t / 2 + b * (t + gap)
            for i in range(nt):
                for j in range(nw):
                    u = -t / 2 + (i + 0.5) * dt        # across thickness
                    v = -w / 2 + (j + 0.5) * dw        # across width
                    if inp.orientation == "face_to_face":   # thickness along x, width along y
                        x, y = xc + off + u, v
                    else:                                    # width along x, laminations stacked in y
                        x, y = xc + v, off + u
                    bodies[len(cs)] = ph
                    cs.append(Conductor(x, y, ph, r_fil, gmr, f"{ph}{b}.{i}.{j}"))
    return cs, bodies


def _dissipation_w_per_m(inp: BusInput, rise: float) -> float:
    """Heat a phase pack can shed at a given surface rise above local air."""
    t, w, n = inp.bar_thickness_mm / 1000, inp.bar_width_mm / 1000, inp.bars_per_phase
    gap = (inp.bar_gap_mm if inp.bar_gap_mm is not None else inp.bar_thickness_mm) / 1000
    pack = n * t + (n - 1) * gap
    if rise <= 0:
        return 0.0
    air = inp.ambient_c + inp.internal_air_rise_c + 273.15
    tb = air + rise
    if inp.orientation == "face_to_face":       # big faces vertical (height w), pack thickness horizontal
        h_v = 1.42 * (rise / w) ** 0.25
        conv = 2 * w * h_v * rise + pack * (1.32 + 0.59) * (rise / pack) ** 0.25 * rise
        inner = 2 * (n - 1) * w * h_v * rise * 0.5
        outer_perim = 2 * (w + pack)
    else:                                        # big faces horizontal (width w), pack height vertical
        conv = (w * 1.32 + w * 0.59) * (rise / w) ** 0.25 * rise + 2 * pack * 1.42 * (rise / pack) ** 0.25 * rise
        inner = 2 * (n - 1) * w * 0.59 * (rise / w) ** 0.25 * rise * 0.5
        outer_perim = 2 * (w + pack)
    rad = EMISSIVITY[inp.finish] * SIGMA * outer_perim * (tb ** 4 - air ** 4)
    return conv + inner + rad


def _rise_for_loss(inp: BusInput, loss_at: callable) -> float:
    """Solve loss(rise) = dissipation(rise) by bisection (loss depends on temperature)."""
    lo, hi = 0.0, 400.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if _dissipation_w_per_m(inp, mid) < loss_at(mid):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def analyse_bus(inp: BusInput) -> BusResult:
    if inp.material not in BAR_MATERIALS:
        raise ValueError("material must be Cu or Al")
    if inp.orientation not in ("face_to_face", "edge_to_edge"):
        raise ValueError("orientation must be face_to_face or edge_to_edge")
    if inp.finish not in EMISSIVITY:
        raise ValueError(f"finish must be one of {sorted(EMISSIVITY)}")
    validate.voltage("voltage_v", inp.voltage_v)
    validate.x_over_r("x_over_r", inp.x_over_r)
    if inp.fault_ka is not None and inp.fault_ka <= 0:
        raise ValueError(f"fault_ka must be greater than 0 kA, got {inp.fault_ka!r}")
    rho20, alpha = BAR_MATERIALS[inp.material]
    notes: list[str] = []

    # Current distribution at an assumed temperature, then refine once.
    temp = inp.ambient_c + inp.internal_air_rise_c + inp.max_rise_c
    for _ in range(2):
        nt, nw = mesh(inp, temp)
        cs, bodies = _layout(inp, nt, nw, temp)
        res = solve_sharing(cs, balanced_three_phase(1.0, 1.0), inp.frequency_hz)
        # Loss per phase pack per A^2, at this temperature (worst phase).
        k_loss = max(sum(p for p, c in zip(res.losses_w_per_m, cs) if c.group == ph) for ph in "ABC")
        t_solve = temp

        def loss_at(rise, I=inp.current_a):
            t_b = inp.ambient_c + inp.internal_air_rise_c + rise
            return k_loss * I ** 2 * (1 + alpha * (t_b - 20)) / (1 + alpha * (t_solve - 20))
        rise = _rise_for_loss(inp, loss_at)
        temp = inp.ambient_c + inp.internal_air_rise_c + rise

    area = inp.bars_per_phase * inp.bar_thickness_mm * inp.bar_width_mm * 1e-6
    rdc = rho20 * (1 + alpha * (t_solve - 20)) / area
    rac_rdc = k_loss / rdc
    loss_pp = loss_at(rise)

    # Rated current at the rise limit: loss(limit) = dissipation(limit).
    t_lim = inp.ambient_c + inp.internal_air_rise_c + inp.max_rise_c
    k_lim = k_loss * (1 + alpha * (t_lim - 20)) / (1 + alpha * (t_solve - 20))
    i_rated = math.sqrt(_dissipation_w_per_m(inp, inp.max_rise_c) / k_lim)

    # Lamination share (phase A).
    shares = []
    for b in range(inp.bars_per_phase):
        tot = sum(res.currents[i] for i, c in enumerate(cs) if c.label.startswith(f"A{b}."))
        shares.append(round(abs(tot) * inp.bars_per_phase * 100, 1))

    checks = [{"name": "Temperature rise at rated current", "clause": f"{inp.standard} [limit UNVERIFIED]",
               "value": round(rise, 1), "limit": inp.max_rise_c, "unit": "C", "passed": rise <= inp.max_rise_c,
               "note": f"ambient {inp.ambient_c} C + internal air {inp.internal_air_rise_c} C, finish {inp.finish}"}]

    force = stress = support = span_max = None
    if inp.fault_ka:
        fcs, fb = _layout(inp, 1, max(2, nw // 2), temp)
        fres = solve_sharing(fcs, balanced_three_phase(1.0, 1.0), inp.frequency_hz)
        share = {i: fres.currents[i] / fres.groups[c.group].current for i, c in enumerate(fcs)}
        fr = fault_forces(fcs, share, inp.fault_ka, inp.x_over_r, inp.frequency_hz,
                          steps_per_cycle=48, angle_steps=12, bodies=fb)
        force = max(fr.body_peak_n_per_m.values())
        fx = max(v[0] for v in fr.body_peak_xy.values())
        k_m, k_r = SPAN[inp.support_condition]
        L = inp.support_span_m
        t, w, n = inp.bar_thickness_mm / 1000, inp.bar_width_mm / 1000, inp.bars_per_phase
        # Force between phases acts along x. face_to_face loads the bar's weak axis.
        s_mod = n * (w * t ** 2 / 6 if inp.orientation == "face_to_face" else t * w ** 2 / 6)
        stress = fx * L ** 2 / k_m / s_mod / 1e6
        support = force * L * k_r
        allow = inp.yield_mpa or YIELD_MPA[inp.material]
        span_max = math.sqrt(k_m * s_mod * allow * 1e6 / fx)
        checks.append({"name": "Bar bending stress between supports", "clause": "beam theory / IEEE 605 span method",
                       "value": round(stress, 1), "limit": allow, "unit": "MPa", "passed": stress <= allow,
                       "note": f"{inp.support_condition} spans of {L} m; max span {span_max:.3f} m; "
                               f"yield {'given' if inp.yield_mpa else 'typical [UNVERIFIED]'}"})
        if inp.support_rating_n:
            checks.append({"name": "Support / insulator load", "clause": "manufacturer rating",
                           "value": round(support), "limit": inp.support_rating_n, "unit": "N",
                           "passed": support <= inp.support_rating_n})
        notes.append(f"Fault {inp.fault_ka} kA rms sym, X/R {inp.x_over_r}: first peak {fr.peak_current_ka:.1f} kA; "
                     f"peak force on a phase pack {force:.0f} N/m ({force * N_PER_M_TO_LBF_PER_FT:.0f} lbf/ft); "
                     f"support load {support:.0f} N ({support / 4.448:.0f} lbf). Static method (no dynamic "
                     "amplification); IEEE 605 / EPRI note static results are conservative for rigid bus.")

    notes.append(f"Rac/Rdc {rac_rdc:.3f} from the filament model ({nt} x {nw} filaments per bar, skin depth "
                 f"{skin_depth_mm(inp.material, temp, inp.frequency_hz):.1f} mm).")
    notes.append("Temperature rise uses still-air natural convection and radiation; enclosure air rise must be given "
                 "(internal_air_rise_c). Confirm by test per the product standard.")
    return BusResult(inp, round(rac_rdc, 4), shares, round(loss_pp, 2), round(rise, 1), round(i_rated),
                     None if force is None else round(force, 1), None if stress is None else round(stress, 1),
                     None if support is None else round(support, 1), None if span_max is None else round(span_max, 3),
                     checks, notes)
