"""Transformer preliminary design and application checks (3-phase, core type).

Preliminary electromagnetic design from the classic design equations
(Say, Sawhney, Kulkarni & Khaparde):

    E = 4.44 f N Bm Ai                (EMF equation)
    Et = K sqrt(kVA)                  (volts per turn, empirical start)
    kVA = 3.33 f Bm Kw J Aw Ai 1e-3   (3-phase output equation, SI units)
    %X = 2 pi f mu0 (N I / Et) Lmt (a + (b1 + b2) / 3) / (h / Kr) x 100   (Rogowski)
    Kr = 1 - (1 - exp(-pi h / W)) / (pi h / W),  W = a + b1 + b2

then losses, efficiency (including the DOE test load point), regulation,
secondary fault current, the 2 s short-circuit thermal withstand (IEC
60076-5 adiabatic formula) and the mean hoop stress in the outer winding.

Empirical constants are marked [UNVERIFIED] and every one is an input.
The design is a starting point for detailed design and FEA, not a final one.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field

MU0 = 4e-7 * math.pi
STEEL_DENSITY = 7650.0  # kg/m3, grain-oriented electrical steel

# Conductor resistivity at 20 C and inferred zero-resistance temperature.
WINDING = {"Cu": (1.7241e-8, 234.5), "Al": (2.8264e-8, 225.0)}
# Typical CRGO (M4, 0.27 mm) specific core loss at 60 Hz, W/kg vs B (T). [UNVERIFIED]
CORE_LOSS_60HZ = ((1.0, 0.35), (1.2, 0.50), (1.3, 0.58), (1.4, 0.68), (1.5, 0.80), (1.6, 0.95),
                  (1.7, 1.17), (1.8, 1.50))
# ANSI standard 3-phase kVA ratings (IEEE C57.12.00 / C57.12.01 practice). [UNVERIFIED list]
STANDARD_KVA = (15, 30, 45, 75, 112.5, 150, 225, 300, 500, 750, 1000, 1500, 2000, 2500, 3000, 3750,
                5000, 7500, 10000)


@dataclass
class TransformerInput:
    kva: float = 1500.0
    hv_v: float = 13800.0
    lv_v: float = 480.0
    hv_connection: str = "delta"
    lv_connection: str = "wye"
    frequency_hz: float = 60.0
    kind: str = "liquid"             # "liquid" or "dry"
    conductor: str = "Cu"           # winding material (both windings)
    b_max_t: float = 1.55
    k_et: float = 0.45               # Et = K sqrt(kVA) [UNVERIFIED: 0.45 Cu / ~0.37 Al, distribution]
    j_lv_a_mm2: float = 3.0
    j_hv_a_mm2: float = 3.0
    window_ratio: float = 3.0        # window height / width
    core_fill: float = 0.60          # net iron area / circumscribing-circle d^2 (stepped core) [UNVERIFIED]
    kw: float | None = None          # window space factor; default 10 / (30 + kV_HV) [UNVERIFIED]
    lv_fill: float = 0.70            # conductor fraction of LV winding cross-section (foil/strip)
    hv_fill: float = 0.45            # conductor fraction of HV winding cross-section (round/rect wire)
    core_to_lv_mm: float = 8.0
    lv_hv_duct_mm: float | None = None  # default 8 + 0.9 kV_HV [UNVERIFIED]
    end_clearance_mm: float | None = None  # winding to yoke; default 15 + 1.2 kV_HV
    phase_gap_mm: float | None = None   # between HV windings of adjacent limbs; default 10 + 0.8 kV_HV
    stray_loss_frac: float = 0.10    # stray + eddy as fraction of I2R
    building_factor: float = 1.25    # core loss building factor [UNVERIFIED typical]
    reference_temp_c: float | None = None  # load-loss reference; default 85 C liquid / 115 C dry (avg rise + 20)
    target_z_pct: float | None = None
    z_tolerance_pct: float = 7.5     # of the specified value [UNVERIFIED: C57.12.00 two-winding tolerance]
    power_factor: float = 0.9
    source_mva: float | None = None  # available fault MVA at HV terminals (None: infinite bus)
    fault_duration_s: float = 2.0    # through-fault thermal duration
    conductor_proof_mpa: float = 100.0  # 0.2 % proof stress of winding conductor [UNVERIFIED: annealed Cu]
    doe_min_efficiency_pct: float | None = None  # from 10 CFR 431.196 for this kVA/BIL (enter from the rule)


@dataclass
class TransformerResult:
    input: TransformerInput
    design: dict
    losses: dict
    impedance: dict
    performance: dict
    short_circuit: dict
    checks: list[dict]
    notes: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c["passed"] for c in self.checks)

    def to_json(self) -> str:
        return json.dumps(asdict(self) | {"passed": self.passed}, indent=2, default=str)


def next_standard_kva(load_kva: float, growth: float = 1.0) -> float:
    need = load_kva * growth
    for k in STANDARD_KVA:
        if k >= need:
            return k
    raise ValueError(f"{need:.0f} kVA exceeds the standard list")


def specific_core_loss(b: float) -> float:
    pts = CORE_LOSS_60HZ
    if b <= pts[0][0]:
        return pts[0][1] * (b / pts[0][0]) ** 2
    for (b0, w0), (b1, w1) in zip(pts, pts[1:]):
        if b <= b1:
            return w0 + (w1 - w0) * (b - b0) / (b1 - b0)
    (b0, w0), (b1, w1) = pts[-2], pts[-1]
    return w1 + (w1 - w0) * (b - b1) / (b1 - b0)


def rogowski_factor(h: float, w: float) -> float:
    x = math.pi * h / w
    return 1 - (1 - math.exp(-x)) / x


def _phase(v_ll: float, conn: str) -> float:
    return v_ll if conn == "delta" else v_ll / math.sqrt(3)


def design(inp: TransformerInput) -> TransformerResult:
    if inp.kind not in ("liquid", "dry"):
        raise ValueError("kind must be liquid or dry")
    if inp.conductor not in WINDING:
        raise ValueError("conductor must be Cu or Al")
    f, s = inp.frequency_hz, inp.kva * 1000
    kv_hv = inp.hv_v / 1000
    vph_lv, vph_hv = _phase(inp.lv_v, inp.lv_connection), _phase(inp.hv_v, inp.hv_connection)
    iph_lv, iph_hv = s / 3 / vph_lv, s / 3 / vph_hv
    i_line_lv = s / (math.sqrt(3) * inp.lv_v)

    # Turns and core.
    et0 = inp.k_et * math.sqrt(inp.kva)
    n_lv = max(1, round(vph_lv / et0))
    et = vph_lv / n_lv
    n_hv = round(n_lv * vph_hv / vph_lv)
    ai = et0 / (4.44 * f * inp.b_max_t)          # net iron area for the target flux density
    bm = et / (4.44 * f * ai)                      # actual flux density after rounding turns
    d = math.sqrt(ai / inp.core_fill)              # core circle diameter
    kw = inp.kw or 10 / (30 + kv_hv)
    j_avg = (inp.j_lv_a_mm2 + inp.j_hv_a_mm2) / 2 * 1e6
    aw = inp.kva / (3.33 * f * bm * kw * j_avg * ai * 1e-3)
    hw = math.sqrt(aw * inp.window_ratio)
    ww = aw / hw

    # Windings (LV inner, HV outer).
    a_lv, a_hv = iph_lv / inp.j_lv_a_mm2 * 1e-6, iph_hv / inp.j_hv_a_mm2 * 1e-6
    end = (inp.end_clearance_mm if inp.end_clearance_mm is not None else 15 + 1.2 * kv_hv) / 1000
    h = hw - 2 * end
    if h <= 0:
        raise ValueError("Window too short for the end clearances; reduce window_ratio or clearances")
    b_lv = n_lv * a_lv / (h * inp.lv_fill)
    b_hv = n_hv * a_hv / (h * inp.hv_fill)
    c1 = inp.core_to_lv_mm / 1000
    duct = (inp.lv_hv_duct_mm if inp.lv_hv_duct_mm is not None else 8 + 0.9 * kv_hv) / 1000
    gap_pp = (inp.phase_gap_mm if inp.phase_gap_mm is not None else 10 + 0.8 * kv_hv) / 1000
    lmt_lv = math.pi * (d + 2 * c1 + b_lv)
    lmt_hv = math.pi * (d + 2 * c1 + 2 * b_lv + 2 * duct + b_hv)
    lmt_duct = math.pi * (d + 2 * c1 + 2 * b_lv + duct)
    width_needed = 2 * (c1 + b_lv + duct + b_hv) + gap_pp

    # Losses.
    t_ref = inp.reference_temp_c or (85.0 if inp.kind == "liquid" else 115.0)
    rho20, t0 = WINDING[inp.conductor]
    rho = rho20 * (t0 + t_ref) / (t0 + 20)
    r_lv = rho * n_lv * lmt_lv / a_lv
    r_hv = rho * n_hv * lmt_hv / a_hv
    i2r = 3 * (iph_lv ** 2 * r_lv + iph_hv ** 2 * r_hv)
    load_loss = i2r * (1 + inp.stray_loss_frac)
    centre = ww + d
    core_vol = 3 * ai * hw + 2 * ai * (2 * centre + d)
    core_mass = core_vol * STEEL_DENSITY
    nll = core_mass * specific_core_loss(bm) * inp.building_factor

    # Impedance.
    w_rad = duct + b_lv + b_hv
    kr = rogowski_factor(h, w_rad)
    x_pct = 2 * math.pi * f * MU0 * (n_lv * iph_lv / et) * lmt_duct * (duct + (b_lv + b_hv) / 3) / (h / kr) * 100
    r_pct = load_loss / s * 100
    z_pct = math.hypot(x_pct, r_pct)
    x_over_r = x_pct / r_pct

    # Performance.
    def eff(load):
        out = s * load * inp.power_factor
        return out / (out + nll + load_loss * load ** 2) * 100
    doe_load = 0.5 if (inp.kind == "liquid" or inp.lv_v > 600) else 0.35
    doe_temp = 55.0 if inp.kind == "liquid" else 75.0
    ll_doe = load_loss * (t0 + doe_temp) / (t0 + t_ref)  # I2R-dominated correction [approximation]
    eff_doe = s * doe_load / (s * doe_load + nll + ll_doe * doe_load ** 2) * 100
    sin_phi = math.sqrt(1 - inp.power_factor ** 2)
    reg = r_pct * inp.power_factor + x_pct * sin_phi + (x_pct * inp.power_factor - r_pct * sin_phi) ** 2 / 200

    # Short circuit at LV terminals.
    z_pu = z_pct / 100 + (inp.kva / 1000 / inp.source_mva if inp.source_mva else 0)
    isc_lv = i_line_lv / z_pu
    kappa = 1.02 + 0.98 * math.exp(-3 / x_over_r)
    i_peak = math.sqrt(2) * kappa * isc_lv
    # Thermal: IEC 60076-5 adiabatic winding temperature after the fault.
    t1 = t_ref
    jsc = (iph_lv / z_pu) / (a_lv * 1e6)       # A/mm2 during fault (LV winding)
    k_mat, t_lim = (106000.0, 250.0) if inp.conductor == "Cu" else (45700.0, 200.0)
    denom = k_mat / (jsc ** 2 * inp.fault_duration_s) - 1
    t_fault = t1 + 2 * (t1 + t0) / denom if denom > 0 else float("inf")
    # Mechanical: mean hoop stress in the outer (HV) winding.
    b_peak = MU0 * n_hv * math.sqrt(2) * kappa * (iph_hv / z_pu) / (h / kr)
    pressure = b_peak ** 2 / (2 * MU0)
    r_hv_mean = lmt_hv / (2 * math.pi)
    hoop = pressure * r_hv_mean / (n_hv * a_hv / h) / 1e6

    checks = []

    def check(name, clause, value, limit, unit, passed, note=""):
        checks.append({"name": name, "clause": clause, "value": round(value, 3), "limit": round(limit, 3),
                       "unit": unit, "passed": bool(passed), "note": note})

    check("Peak flux density", "design practice (CRGO)", bm, 1.75, "T", bm <= 1.75, "keep margin for overexcitation")
    check("Windings fit the window width", "geometry", width_needed * 1000, ww * 1000, "mm",
          width_needed <= ww, "2 x (core-LV + LV + duct + HV) + phase gap")
    if inp.target_z_pct:
        tol = inp.target_z_pct * inp.z_tolerance_pct / 100
        check("Impedance within tolerance of target", "IEEE C57.12.00 [tolerance UNVERIFIED]", z_pct,
              inp.target_z_pct + tol, "%", abs(z_pct - inp.target_z_pct) <= tol,
              f"target {inp.target_z_pct} % +/- {inp.z_tolerance_pct} %")
    if inp.doe_min_efficiency_pct:
        check("Efficiency at DOE test point", "10 CFR 431.196 (value entered by user)", eff_doe,
              inp.doe_min_efficiency_pct, "%", eff_doe >= inp.doe_min_efficiency_pct,
              f"{doe_load:.0%} load, load loss at {doe_temp:.0f} C")
    check(f"Winding temperature after {inp.fault_duration_s:g} s through-fault", "IEC 60076-5 method; "
          "C57.12.00 limit [UNVERIFIED]", t_fault, t_lim, "C", t_fault <= t_lim,
          f"LV current density {jsc:.1f} A/mm2 during fault")
    check("Mean hoop stress in outer (HV) winding", "Kulkarni & Khaparde method [UNVERIFIED]", hoop,
          inp.conductor_proof_mpa, "MPa", hoop <= inp.conductor_proof_mpa, "compare with conductor 0.2 % proof stress")

    notes = [
        f"Preliminary design only (empirical K = {inp.k_et}, Kw = {kw:.3f}, core fill {inp.core_fill}); "
        "refine with detailed design and FEA, and confirm by test (IEEE C57.12.90 / C57.12.91).",
        f"DOE test point: {doe_load:.0%} load, load loss corrected to {doe_temp:.0f} C; enter the 10 CFR 431.196 "
        "minimum efficiency for this kVA and BIL (tables not loaded).",
        "Inner (LV) winding radial buckling and axial forces are not checked yet.",
    ]
    if not inp.source_mva:
        notes.append("Secondary fault current assumes an infinite source (no utility impedance).")

    r = lambda v, n=1: round(v, n)
    return TransformerResult(
        inp,
        design={"volts_per_turn": r(et, 3), "turns_lv": n_lv, "turns_hv": n_hv, "b_max_t": r(bm, 3),
                "core_area_net_cm2": r(ai * 1e4), "core_diameter_mm": r(d * 1000), "window_h_mm": r(hw * 1000),
                "window_w_mm": r(ww * 1000), "winding_height_mm": r(h * 1000),
                "lv_conductor_mm2": r(a_lv * 1e6), "hv_conductor_mm2": r(a_hv * 1e6, 2),
                "lv_radial_mm": r(b_lv * 1000), "hv_radial_mm": r(b_hv * 1000), "duct_mm": r(duct * 1000),
                "core_mass_kg": r(core_mass), "kw": r(kw, 3)},
        losses={"no_load_w": r(nll), "load_loss_w": r(load_loss), "reference_temp_c": t_ref,
                "r_lv_mohm": r(r_lv * 1000, 3), "r_hv_ohm": r(r_hv, 3)},
        impedance={"r_pct": r(r_pct, 2), "x_pct": r(x_pct, 2), "z_pct": r(z_pct, 2), "x_over_r": r(x_over_r, 2),
                   "rogowski_kr": r(kr, 3)},
        performance={"efficiency_pct": {f"{int(l * 100)}%": r(eff(l), 3) for l in (0.25, 0.5, 0.75, 1.0)},
                     "doe_point": {"load": doe_load, "efficiency_pct": r(eff_doe, 3)},
                     "regulation_pct": r(reg, 2),
                     "max_efficiency_load_pct": r(math.sqrt(nll / load_loss) * 100)},
        short_circuit={"lv_fault_ka_rms": r(isc_lv / 1000, 2), "lv_fault_peak_ka": r(i_peak / 1000, 2),
                       "winding_temp_after_fault_c": r(t_fault), "hv_hoop_stress_mpa": r(hoop, 1)},
        checks=checks, notes=notes)


def design_for_impedance(inp: TransformerInput, lo: float = 1.2, hi: float = 8.0) -> TransformerResult:
    """Tune the window height/width ratio so %Z meets target_z_pct.

    A taller window gives taller windings and lower leakage reactance, so %Z
    falls monotonically with window_ratio; solved by bisection.
    """
    if not inp.target_z_pct:
        raise ValueError("target_z_pct is required to tune impedance")
    from dataclasses import replace

    def z(ratio):
        return design(replace(inp, window_ratio=ratio)).impedance["z_pct"]
    z_lo, z_hi = z(lo), z(hi)
    if not (z_hi <= inp.target_z_pct <= z_lo):
        raise ValueError(f"Target {inp.target_z_pct} % Z is outside {z_hi:.2f}-{z_lo:.2f} % reachable by window "
                         "ratio alone; change the LV-HV duct, current density or volts per turn")
    for _ in range(40):
        mid = (lo + hi) / 2
        if z(mid) > inp.target_z_pct:
            lo = mid
        else:
            hi = mid
    result = design(replace(inp, window_ratio=(lo + hi) / 2))
    result.notes.insert(0, f"Window height/width ratio tuned to {(lo + hi) / 2:.2f} to meet {inp.target_z_pct} % Z.")
    return result
