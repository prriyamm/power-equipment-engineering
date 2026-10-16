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

import datetime as _dt
import json
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import validate

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
    source_x_over_r: float = 10.0    # utility source X/R at the HV terminals [UNVERIFIED typical; enter the utility's value]
    fault_duration_s: float = 2.0    # through-fault thermal duration
    conductor_proof_mpa: float = 100.0  # 0.2 % proof stress of winding conductor [UNVERIFIED: annealed Cu]
    doe_min_efficiency_pct: float | None = None  # optional extra user minimum (the 431.196 tables are built in)
    bil_kv: float | None = None      # HV winding BIL, kV; needed for the medium-voltage dry-type DOE minimum (no default)
    doe_date: str | None = None      # manufacture date YYYY-MM-DD selecting the 431.196 window; None = today
    doe_submersible: bool = False    # liquid-immersed submersible unit (431.196(b)(4) table from 2029-04-23)


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
    doe: dict = field(default_factory=dict)   # doe_efficiency_check() result plus the losses at the DOE conditions

    @property
    def passed(self) -> bool:
        return all(c["passed"] for c in self.checks)

    def to_json(self) -> str:
        return json.dumps(asdict(self) | {"passed": self.passed}, indent=2, default=str)


# DOE test load point by equipment class. Efficiency standards: 10 CFR 431.196 (a) low-voltage dry-type,
# (b) liquid-immersed, (c) medium-voltage dry-type; class definitions in 10 CFR 431.192 (low-voltage
# dry-type: input voltage <= 600 V; medium-voltage dry-type: primary 601 V to 34.5 kV). The per-unit test
# load (35 % LVDT, 50 % liquid and MVDT) is Table 2.1 and the reference temperatures (no-load 20 C; load
# loss 55 C liquid, 75 C dry) Table 2.2 of Appendix A to Subpart K (read from the eCFR, see
# data/doe_10cfr431_efficiency.json).
DOE_TEST_POINT_CITATION = "10 CFR 431.192; Part 431 Subpart K App. A Tables 2.1 and 2.2"
DOE_DATA = json.loads((Path(__file__).resolve().parent / "data" / "doe_10cfr431_efficiency.json")
                      .read_text(encoding="utf-8"))
DOE_CATEGORIES = ("liquid", "lv_dry", "mv_dry")
DOE_CHECK_NAME = "DOE 10 CFR 431.196 minimum efficiency"
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def doe_test_point(kind: str, primary_v: float) -> tuple[str, float]:
    """(DOE equipment class, per-unit test load). Classified by the primary (input) voltage."""
    if kind == "liquid":
        return "liquid-immersed", 0.50
    if primary_v <= 600:
        return "low-voltage dry-type", 0.35
    return "medium-voltage dry-type", 0.50


def doe_category(kind: str, primary_v: float) -> str:
    """DOE category key ('liquid', 'lv_dry', 'mv_dry') from the cooling type and primary (input) voltage.

    10 CFR 431.192: low-voltage dry-type has an input voltage of 600 V or less; medium-voltage dry-type a
    rated primary voltage between 601 V and 34.5 kV. A primary above 600 V is treated as medium voltage.
    """
    if kind == "liquid":
        return "liquid"
    return "lv_dry" if primary_v <= DOE_DATA["scope"]["lv_dry_max_input_v"] else "mv_dry"


def _doe_rows(window: dict, phases: int, band: int | None) -> list:
    rows = window["single_phase" if phases == 1 else "three_phase"]
    return [[k, v if band is None else v[band]] for k, v in rows]


def _doe_lookup(rows: list, kva: float) -> dict:
    """Minimum efficiency for `kva` from tabulated [kVA, eff|None] rows, by the 431.196 rule: the table value,
    or linear interpolation between the rows immediately below and above. No extrapolation; a blank (None)
    neighbour also leaves the minimum undetermined."""
    valued = [r for r in rows if r[1] is not None]
    below = [r for r in valued if r[0] < kva]
    above = [r for r in valued if r[0] > kva]
    nearest = ([below[-1]] if below else []) + ([above[0]] if above else [])
    for k, v in rows:
        if k == kva:
            if v is None:
                return {"required": None, "interpolated": False, "rows": [], "nearest": nearest,
                        "reason": "the table gives no minimum at this kVA for this BIL"}
            return {"required": v, "interpolated": False, "rows": [[k, v]], "nearest": [[k, v]], "reason": ""}
    lo = [r for r in rows if r[0] < kva]
    hi = [r for r in rows if r[0] > kva]
    if not lo or not hi:
        return {"required": None, "interpolated": False, "rows": [], "nearest": nearest,
                "reason": "rating outside the tabulated kVA range (the rule gives no extrapolation)"}
    (k0, e0), (k1, e1) = lo[-1], hi[0]
    if e0 is None or e1 is None:
        return {"required": None, "interpolated": False, "rows": [], "nearest": nearest,
                "reason": "an adjacent table row has no minimum for this BIL"}
    return {"required": e0 + (e1 - e0) * (kva - k0) / (k1 - k0), "interpolated": True,
            "rows": [[k0, e0], [k1, e1]], "nearest": [[k0, e0], [k1, e1]], "reason": ""}


def _doe_windows(category: str, submersible: bool) -> list:
    applies = ("all", "submersible" if submersible else "non_submersible")
    return [w for w in DOE_DATA["categories"][category]["windows"] if w["applies_to"] in applies]


def _doe_band(bil_kv: float | None) -> tuple[int | None, str | None]:
    for i, b in enumerate(DOE_DATA["categories"]["mv_dry"]["bil_bands_kv"]):
        if bil_kv is not None and b["min"] <= bil_kv and (b["max"] is None or bil_kv <= b["max"]):
            return i, b["id"]
    return None, None


def doe_efficiency_check(kind: str, phases: int, kva: float, bil_kv: float | None = None,
                         efficiency_pct: float | None = None, date: str | None = None, *,
                         submersible: bool = False, primary_v: float | None = None,
                         secondary_v: float | None = None, frequency_hz: float | None = None,
                         today: str | None = None) -> dict:
    """DOE 10 CFR 431.196 minimum-efficiency check.

    kind: 'liquid', 'lv_dry' or 'mv_dry' (see doe_category); phases 1 or 3; kva nameplate; bil_kv the
    winding BIL (medium-voltage dry-type only); efficiency_pct the efficiency at the DOE test load (Appendix
    A per-unit load, unity power factor output basis, load loss at the reference temperature); date the
    manufacture date 'YYYY-MM-DD' that selects the compliance window (default: today). Optional scope inputs
    (primary_v, secondary_v, frequency_hz) test the 431.192 distribution-transformer definition.

    status: 'pass' / 'fail'; 'not_in_table' (no minimum determinable from the table: outside the tabulated
    kVA range, a blank cell, or BIL outside the bands); 'needs_input' (medium-voltage dry-type without BIL);
    'not_covered' (outside the 431.192 definition or before the first compliance window).
    """
    if kind not in DOE_CATEGORIES:
        raise ValueError(f"kind must be one of {', '.join(DOE_CATEGORIES)}, got {kind!r}")
    if phases not in (1, 3):
        raise ValueError(f"phases must be 1 or 3, got {phases!r}")
    if not kva or kva <= 0:
        raise ValueError(f"kva must be greater than 0, got {kva!r}")
    if date is None:
        date = today or _dt.date.today().isoformat()
    if not isinstance(date, str) or not _ISO_DATE.match(date):
        raise ValueError(f"date must be an ISO date YYYY-MM-DD, got {date!r}")
    cat = DOE_DATA["categories"][kind]
    tp, scope = DOE_DATA["test_procedure"], DOE_DATA["scope"]
    band, band_id = _doe_band(bil_kv) if kind == "mv_dry" else (None, None)
    windows = _doe_windows(kind, submersible and kind == "liquid")
    out = {"category": kind, "category_label": cat["label"], "phases": phases, "kva": kva, "bil_kv": bil_kv,
           "bil_band": band_id, "date": date, "submersible": bool(submersible and kind == "liquid"),
           "test_load_pu": tp["per_unit_load"][kind], "reference_temp_c": dict(tp["reference_temp_c"][kind]),
           "window": None, "required_pct": None, "interpolated": False, "rows": [], "nearest_rows": [],
           "efficiency_pct": efficiency_pct, "margin_pct": None, "status": "", "passed": None, "message": "",
           "citation": "", "data_status": DOE_DATA["_meta"]["status"],
           "snapshot": DOE_DATA["_meta"]["ecfr_snapshot_date"], "by_window": []}

    def lookup(w):
        if kind == "mv_dry" and band is None:
            return None
        return _doe_lookup(_doe_rows(w, phases, band), kva)

    for w in windows:
        lk = lookup(w)
        out["by_window"].append({"id": w["id"], "paragraph": w["paragraph"], "table": w["table"], "from": w["from"],
                                 "to": w["to"], "required_pct": lk["required"] if lk else None})

    # Scope: 10 CFR 431.192 definition of distribution transformer.
    lo_kva, hi_kva = scope["kva_range"]["liquid" if kind == "liquid" else "dry"]
    why = ""
    if primary_v is not None and primary_v > scope["max_input_v"]:
        why = f"input voltage above {scope['max_input_v'] / 1000:g} kV"
    elif secondary_v is not None and secondary_v > scope["max_output_v"]:
        why = f"output voltage above {scope['max_output_v']} V"
    elif frequency_hz is not None and frequency_hz != scope["frequency_hz"]:
        why = f"not rated {scope['frequency_hz']} Hz"
    elif not lo_kva <= kva <= hi_kva:
        why = f"rating outside {lo_kva:g}-{hi_kva:g} kVA"
    if why:
        out.update(status="not_covered", citation="10 CFR 431.192",
                   message=f"Not a DOE distribution transformer (10 CFR 431.192): {why}. No 431.196 minimum applies.")
        return out

    window = next((w for w in windows if w["from"] <= date and (w["to"] is None or date < w["to"])), None)
    if window is None:
        out.update(status="not_covered", citation=cat["paragraph"],
                   message=f"No {cat['label'].lower()} standard for units manufactured before {windows[0]['from']} "
                           f"({cat['paragraph']}).")
        return out
    out["window"] = {"id": window["id"], "paragraph": window["paragraph"], "table": window["table"],
                     "from": window["from"], "to": window["to"]}
    load_txt = f"{tp['per_unit_load'][kind] * 100:g} % of nameplate load"
    out["citation"] = f"{window['paragraph']}, {window['table']}; App. A Table 2.1 ({load_txt})"
    if kind == "mv_dry" and bil_kv is None:
        out.update(status="needs_input", message="Medium-voltage dry-type minimums depend on the BIL: enter the "
                                                 "HV winding BIL (kV) to select the 431.196(c) column.")
        return out
    if kind == "mv_dry" and band is None:
        out.update(status="not_in_table", message=f"BIL {bil_kv:g} kV is outside the 431.196(c) BIL columns "
                                                  "(20-45, 46-95, 96 kV and above); rating not in table.")
        return out
    lk = lookup(window)
    out.update(rows=lk["rows"], nearest_rows=lk["nearest"], interpolated=lk["interpolated"])
    if lk["required"] is None:
        near = ", ".join(f"{k:g} kVA {v:.2f} %" for k, v in lk["nearest"]) or "none"
        out.update(status="not_in_table", message=f"Rating not in table: {lk['reason']}. Nearest rows: {near}.")
        return out
    req = lk["required"]
    out["required_pct"] = req
    how = (f"interpolated between {lk['rows'][0][0]:g} and {lk['rows'][1][0]:g} kVA" if lk["interpolated"]
           else "table value")
    if efficiency_pct is None:
        out.update(status="needs_input", message=f"Minimum {req:.2f} % ({how}); no efficiency given.")
        return out
    passed = efficiency_pct >= req
    out.update(margin_pct=efficiency_pct - req, passed=passed, status="pass" if passed else "fail",
               message=f"Minimum {req:.2f} % at {load_txt} ({how}).")
    return out


def source_impedance_pu(kva: float, source_mva: float | None, x_over_r: float) -> complex:
    """Utility source impedance on the transformer base: |Z| = kVA/1000 / MVA_sc at angle atan(X/R)."""
    if not source_mva:
        return 0j
    mag = kva / 1000 / source_mva
    r = mag / math.hypot(1.0, x_over_r)
    return complex(r, r * x_over_r)


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
    validate.voltage("hv_v", inp.hv_v)
    validate.voltage("lv_v", inp.lv_v)
    validate.power_factor("power_factor", inp.power_factor)
    validate.clearing_time("fault_duration_s", inp.fault_duration_s)
    validate.x_over_r("source_x_over_r", inp.source_x_over_r)
    if inp.source_mva is not None and inp.source_mva <= 0:
        raise ValueError(f"source_mva must be greater than 0 MVA (or None for an infinite bus), got {inp.source_mva!r}")
    if inp.kva <= 0:
        raise ValueError(f"kva must be greater than 0, got {inp.kva!r}")
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
    doe_class, doe_load = doe_test_point(inp.kind, inp.hv_v)
    doe_temp = 55.0 if inp.kind == "liquid" else 75.0
    ll_doe = load_loss * (t0 + doe_temp) / (t0 + t_ref)  # I2R-dominated correction [approximation]
    eff_doe = s * doe_load / (s * doe_load + nll + ll_doe * doe_load ** 2) * 100
    sin_phi = math.sqrt(1 - inp.power_factor ** 2)
    reg = r_pct * inp.power_factor + x_pct * sin_phi + (x_pct * inp.power_factor - r_pct * sin_phi) ** 2 / 200

    # Short circuit at LV terminals: source and transformer impedances added as phasors
    # (each with its own X/R), on the transformer kVA base.
    z_tx = complex(r_pct, x_pct) / 100
    z_src = source_impedance_pu(inp.kva, inp.source_mva, inp.source_x_over_r)
    z_tot = z_tx + z_src
    z_pu = abs(z_tot)
    xr_tot = z_tot.imag / z_tot.real
    isc_lv = i_line_lv / z_pu
    kappa = 1.02 + 0.98 * math.exp(-3 / xr_tot)
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
    doe = doe_efficiency_check(doe_category(inp.kind, inp.hv_v), 3, inp.kva, inp.bil_kv, eff_doe, inp.doe_date,
                               submersible=inp.doe_submersible, primary_v=inp.hv_v, secondary_v=inp.lv_v,
                               frequency_hz=inp.frequency_hz)
    doe["losses"] = {"no_load_w": nll, "load_loss_w": ll_doe, "load_loss_temp_c": doe_temp}
    if doe["status"] in ("pass", "fail"):
        check(DOE_CHECK_NAME, doe["citation"], eff_doe, doe["required_pct"], "%", doe["passed"],
              f"{doe['category_label']}, {doe['window']['paragraph']} window, {doe_load:.0%} load, unity pf, "
              f"load loss at {doe_temp:.0f} C; " + doe["message"])
    elif doe["status"] == "needs_input":
        checks.append({"name": DOE_CHECK_NAME, "clause": doe["citation"], "value": round(eff_doe, 3), "limit": None,
                       "unit": "%", "passed": False, "note": "Not determined: " + doe["message"]})
    if inp.doe_min_efficiency_pct:
        check("Efficiency at DOE test point", f"10 CFR 431.196 (value entered by user); {DOE_TEST_POINT_CITATION}",
              eff_doe, inp.doe_min_efficiency_pct, "%", eff_doe >= inp.doe_min_efficiency_pct,
              f"{doe_class}, {doe_load:.0%} load, load loss at {doe_temp:.0f} C")
    check(f"Winding temperature after {inp.fault_duration_s:g} s through-fault", "IEC 60076-5 method; "
          "C57.12.00 limit [UNVERIFIED]", t_fault, t_lim, "C", t_fault <= t_lim,
          f"LV current density {jsc:.1f} A/mm2 during fault")
    check("Mean hoop stress in outer (HV) winding", "Kulkarni & Khaparde method [UNVERIFIED]", hoop,
          inp.conductor_proof_mpa, "MPa", hoop <= inp.conductor_proof_mpa, "compare with conductor 0.2 % proof stress")

    notes = [
        f"Preliminary design only (empirical K = {inp.k_et}, Kw = {kw:.3f}, core fill {inp.core_fill}); "
        "refine with detailed design and FEA, and confirm by test (IEEE C57.12.90 / C57.12.91).",
        f"DOE test point: {doe_class} (HV winding taken as the primary), {doe_load:.0%} load, load loss corrected to {doe_temp:.0f} C "
        "(I2R ratio, approximation). 10 CFR 431.196 check: " + doe["message"],
        "Inner (LV) winding radial buckling and axial forces are not checked yet.",
    ]
    if not inp.source_mva:
        notes.append("Secondary fault current assumes an infinite source (no utility impedance).")
    else:
        notes.append(f"Secondary fault current: source {inp.source_mva:g} MVA at X/R {inp.source_x_over_r:g} added to "
                     f"the transformer impedance as phasors; combined X/R {xr_tot:.2f}.")

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
                       "total_z_pu": r(z_pu, 5), "total_x_over_r": r(xr_tot, 2),
                       "winding_temp_after_fault_c": r(t_fault), "hv_hoop_stress_mpa": r(hoop, 1)},
        checks=checks, notes=notes, doe=doe)


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
