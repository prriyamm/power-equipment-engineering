"""Cable bus short-circuit and temperature-rise simulation.

Framing: IEEE Std C37.23 (metal-enclosed bus, includes cable bus) and CSA C22.2 No. 273 (cablebus) rate a
product by type tests: momentary (peak) withstand, short-time (rms, stated duration) withstand and a
temperature-rise test. Both texts are licensed and were not read; test durations, rise limits and pass
criteria are therefore NOT taken from them. The ratings and limits are user inputs from the product's own
test report (no defaults). This module computes the physics from public methods and compares it with those
inputs.

Short circuit (time domain)
- Phase currents: i_p(t) = sqrt(2) I [sin(wt + a - phi - 120 deg k) - sin(a - phi - 120 deg k) e^(-t/tau)],
  tau = (X/R)/w, a = closing (inception) angle. Each conductor carries its share of its phase from the
  impedance solve. Same model as forces.fault_forces.
- Force per metre on each conductor: vector sum of 2e-7 i_i i_j / d_ij (Ampere's force law; the basis of
  IEEE 605 and IEC 60865). Reuses the internals of forces.fault_forces, so the peaks match it exactly.
- Support block load over a span = force per metre x span (same static basis as the designer's screening).
- Conductor temperature: ICEA P-32-382 adiabatic relation (I/A)^2 t = K log10((T2+T0)/(T1+T0)) inverted for
  T2 with the let-through energy of the actual asymmetrical current, in closed form.
- Short-time rating: thermal equivalence on I^2 t (heating is proportional to I^2 t), so 63 kA for 2 s and
  89 kA for 1 s are the same energy (7938 vs 7921 kA^2 s).

Temperature rise
- Steady state per cable: the free-air thermal circuit of thermal.py (T1, T3, T4, shield loss factor lambda1,
  dielectric loss Wd) solved forward for the conductor temperature at a given current, iterating R(theta).
- Enclosure surface temperature: heat balance, losses inside the enclosure = natural convection (simplified
  laminar correlations) + grey-body radiation from the outer surface. An estimate, with no credit for
  ventilation.
- Warm-up: simplified one-node model, tau = C R with C the sum of conductor, insulation, shield and jacket
  thermal capacitances per metre and R the conductor-to-ambient thermal resistance at the operating point.

[UNVERIFIED: all physics constants are listed with status and citation in data/cablebus_sim.json.]
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, replace
from pathlib import Path

from . import conductors as cond
from . import validate
from .cablebus import (PHASES, CableBusInput, _groups, analyse, build_layout, construction)
from .cablebus_design import BLOCK_MATERIALS
from .forces import N_PER_M_TO_LBF_PER_FT, _forces_at, _geometry, _inst_currents, fault_forces, peak_factor
from .impedance import solve_sharing
from .thermal import (AIR_CONSTANTS, THERMAL_RESISTIVITY, CableConstruction, dielectric_loss, free_air_ampacity,
                      insulation_resistivity)

DATA = json.loads((Path(__file__).parent / "data" / "cablebus_sim.json").read_text())
NOT_SET = "NOT SET"
ENTER = "enter from test report"
N_PER_M_TO_LBF = 1 / 4.44822
CLAUSE_SC = "IEEE C37.23 / CSA C22.2 No. 273 short-circuit rating [clause text NOT read]"
CLAUSE_TR = "IEEE C37.23 / CSA C22.2 No. 273 temperature rise [clause text NOT read]"


@dataclass
class SimInput:
    bus: CableBusInput = field(default_factory=CableBusInput)
    # --- short circuit ---
    closing_angle_deg: float | None = None     # None: the worst angle found by fault_forces
    cycles: float = 5.0                        # waveform window
    steps_per_cycle: int = 96
    initial_temp_c: float | None = None        # conductor temperature at fault inception; None: insulation_temp_c
    # Tested ratings from the product's CSA C22.2 No. 273 / IEEE C37.23 test report. No defaults.
    tested_momentary_peak_ka: float | None = None
    tested_short_time_ka: float | None = None   # rms symmetrical
    tested_short_time_s: float | None = None
    tested_block_load_n: float | None = None    # tested load per support block, if the report gives one
    tested_force_n_per_m: float | None = None   # tested force per metre on a cable, if the report gives one
    block_material: str = "GPO-3"               # screening only (designer default); None skips
    block_thickness_mm: float = 25.4
    block_safety_factor: float = 2.0
    # --- temperature rise ---
    load_scale: float = 1.0                     # multiplies every cable current (design current = 1)
    enclosure_emissivity: float | None = None   # None: flagged default from the data file
    # Limits are rises above the ambient input (40 C is the usual test basis), from the test report.
    rise_limit_conductor_k: float | None = None
    rise_limit_enclosure_k: float | None = None
    rise_limit_termination_k: float | None = None
    termination_rise_k: float | None = None     # estimate or test result for the termination, if known


# --- context ------------------------------------------------------------------

def build_context(bus: CableBusInput) -> dict:
    """Solve the bus once: analyse (pattern, checks), then rebuild the layout and sharing for that pattern."""
    inp = replace(bus)
    result = analyse(inp, compare_bonding=False)   # may fill in derived fields on inp
    od = result.cable_od_mm
    cs = build_layout(inp, result.pattern, od)
    with_shields = inp.shield_bonding == "both_ends"
    res = solve_sharing(cs, _groups(inp, with_shields), inp.frequency_hz)
    phase_idx = [i for i, c in enumerate(cs) if c.group in PHASES]
    share = {i: res.currents[i] / res.groups[cs[i].group].current for i in phase_idx}
    return {"inp": inp, "result": result, "cs": cs, "res": res, "od": od, "phase_idx": phase_idx,
            "share": share}


# --- short circuit: waveforms ---------------------------------------------------

def _angle_grid(angle_steps: int) -> list[float]:
    return [math.pi * a / angle_steps for a in range(angle_steps)]


def worst_closing_angle(conductors, share, fault_ka_rms: float, x_over_r: float, freq: float = 60.0,
                        phases: tuple[str, ...] = PHASES, steps_per_cycle: int = 96,
                        angle_steps: int = 24) -> tuple[int, float]:
    """(grid index, radians) of the closing angle at which fault_forces finds its worst force.

    Same angle grid, first-cycle window and force model as forces.fault_forces; the first angle that reaches
    the overall maximum is returned.
    """
    validate.x_over_r("x_over_r", x_over_r)
    w = 2 * math.pi * freq
    tau = x_over_r / w
    phi = math.atan(x_over_r)
    amp = math.sqrt(2) * fault_ka_rms * 1000
    idx = [i for i, c in enumerate(conductors) if c.group in phases]
    geo = _geometry(conductors, idx)
    best, best_a = -1.0, 0
    for a_step, alpha in enumerate(_angle_grid(angle_steps)):
        m = 0.0
        for t_step in range(steps_per_cycle + 1):
            t = t_step / (steps_per_cycle * freq)
            inst = _inst_currents(conductors, share, idx, phases, amp, w, t, math.exp(-t / tau), alpha, phi)
            fxy = _forces_at(idx, geo, inst)
            for i in idx:
                m = max(m, math.hypot(*fxy[i]))
        if m > best:
            best, best_a = m, a_step
    return best_a, _angle_grid(angle_steps)[best_a]


def fault_force_waveforms(conductors, share, fault_ka_rms: float, x_over_r: float, freq: float = 60.0,
                          phases: tuple[str, ...] = PHASES, closing_angle_rad: float | None = None,
                          cycles: float = 5.0, steps_per_cycle: int = 96, angle_steps: int = 24) -> dict:
    """Time-domain currents and forces for one closing angle (default: the worst one fault_forces finds).

    Returns t (s), phase currents i_A/i_B/i_C (A, unit share), per-conductor current (A, with its share) and
    force magnitude per metre (N/m) keyed by conductor index, the force of the worst conductor (largest
    peak over the window) and the envelope max_i |F_i(t)|. peak_first_cycle_n_per_m is the largest force in
    the first cycle; at the worst angle it equals fault_forces(...).worst_n_per_m exactly.
    """
    validate.x_over_r("x_over_r", x_over_r)
    w = 2 * math.pi * freq
    tau = x_over_r / w
    phi = math.atan(x_over_r)
    amp = math.sqrt(2) * fault_ka_rms * 1000
    idx = [i for i, c in enumerate(conductors) if c.group in phases]
    geo = _geometry(conductors, idx)
    if closing_angle_rad is None:
        closing_angle_rad = worst_closing_angle(conductors, share, fault_ka_rms, x_over_r, freq, phases,
                                                steps_per_cycle, angle_steps)[1]
    alpha = closing_angle_rad
    n_t = int(cycles * steps_per_cycle) + 1
    n_first = steps_per_cycle + 1
    ts = []
    ph = {p: [] for p in phases}
    dc = {p: [] for p in phases}
    cur = {i: [] for i in idx}
    frc = {i: [] for i in idx}
    for t_step in range(n_t):
        t = t_step / (steps_per_cycle * freq)
        decay = math.exp(-t / tau)
        ts.append(t)
        for k, p in enumerate(phases):
            th = alpha - phi - 2 * math.pi * k / 3
            ph[p].append(amp * (math.sin(w * t + th) - math.sin(th) * decay))
            dc[p].append(-amp * math.sin(th) * decay)
        inst = _inst_currents(conductors, share, idx, phases, amp, w, t, decay, alpha, phi)
        fxy = _forces_at(idx, geo, inst)
        for i in idx:
            cur[i].append(inst[i])
            frc[i].append(math.hypot(*fxy[i]))
    peaks = {i: max(frc[i]) for i in idx}
    worst = first_max(idx, lambda i: peaks[i])
    envelope = [max(frc[i][k] for i in idx) for k in range(n_t)]
    return {"t_s": ts, "closing_angle_rad": alpha, "phase_current_a": ph, "dc_component_a": dc,
            "conductor_current_a": cur, "force_n_per_m": frc, "worst_index": worst,
            "force_worst_n_per_m": frc[worst], "force_envelope_n_per_m": envelope,
            "peak_n_per_m": max(envelope), "peak_first_cycle_n_per_m": max(envelope[:n_first]),
            "peak_per_conductor_n_per_m": peaks}


def first_peak_current(fault_ka_rms: float, x_over_r: float, freq: float = 60.0, steps_per_cycle: int = 480,
                       angle_step_deg: float = 1.0) -> dict:
    """Largest first-cycle instantaneous phase current over every closing angle (unit share).

    Phase k at closing angle a has the same waveform family as phase 0 at a - 120 deg k, so sweeping a over
    180 deg for all three phases covers every inception angle. Result in A.
    """
    validate.x_over_r("x_over_r", x_over_r)
    w = 2 * math.pi * freq
    tau = x_over_r / w
    phi = math.atan(x_over_r)
    amp = math.sqrt(2) * fault_ka_rms * 1000
    best, best_ang, best_ph, best_t = 0.0, 0.0, "A", 0.0
    n_ang = int(round(180.0 / angle_step_deg))
    for a in range(n_ang):
        alpha = math.radians(a * angle_step_deg)
        for k, p in enumerate(PHASES):
            th = alpha - phi - 2 * math.pi * k / 3
            for t_step in range(steps_per_cycle + 1):
                t = t_step / (steps_per_cycle * freq)
                v = abs(amp * (math.sin(w * t + th) - math.sin(th) * math.exp(-t / tau)))
                if v > best:
                    best, best_ang, best_ph, best_t = v, a * angle_step_deg, p, t
    return {"peak_a": best, "angle_deg": best_ang, "phase": best_ph, "time_s": best_t}


def i2t_closed_form(amp_a: float, th: float, t: float, freq: float, x_over_r: float) -> float:
    """Integral from 0 to t of i^2 dt, A^2 s, for i = amp [sin(wu + th) - sin(th) e^(-u/tau)] (exact)."""
    w = 2 * math.pi * freq
    p = w / x_over_r                      # 1 / tau
    s_t, c_t = math.sin(w * t + th), math.cos(w * t + th)
    i_sin2 = t / 2 - (math.sin(2 * (w * t + th)) - math.sin(2 * th)) / (4 * w)
    e1 = math.exp(-p * t)
    i_cross = (e1 * (-p * s_t - w * c_t) + (p * math.sin(th) + w * math.cos(th))) / (p * p + w * w)
    i_dc2 = (1 - math.exp(-2 * p * t)) / (2 * p)
    return amp_a ** 2 * (i_sin2 - 2 * math.sin(th) * i_cross + math.sin(th) ** 2 * i_dc2)


def i2t_ka2s(ka: float, seconds: float) -> float:
    return ka * ka * seconds


def equivalent_short_time_ka(rated_ka: float, rated_s: float, duration_s: float) -> float:
    """Short-time current with the same I^2 t at another duration (heating equivalence)."""
    if rated_ka <= 0 or rated_s <= 0 or duration_s <= 0:
        raise ValueError("rated_ka, rated_s and duration_s must be > 0")
    return math.sqrt(rated_ka ** 2 * rated_s / duration_s)


def first_max(items, key):
    """First item whose key is within 1e-9 (relative) of the maximum, so mirror-image ties (equal up to
    floating-point noise) resolve the same way in every port."""
    items = list(items)
    m = max(key(x) for x in items)
    return next(x for x in items if key(x) >= m * (1 - 1e-9))


# --- result helpers -------------------------------------------------------------

def _check(name, clause, value, limit, unit, passed, note="", status=None):
    st = status or (NOT_SET if passed is None else ("PASS" if passed else "FAIL"))
    return {"name": name, "clause": clause, "value": None if value is None else round(value, 3),
            "limit": None if limit is None else round(limit, 3), "unit": unit,
            "passed": None if passed is None else bool(passed), "status": st, "note": note}


def _verdict(checks: list[dict]) -> tuple[bool | None, bool]:
    set_ = [c for c in checks if c["passed"] is not None]
    complete = len(set_) == len(checks)
    if any(not c["passed"] for c in set_):
        return False, complete
    return (True if set_ else None), complete


def _status_row(name, value, status, source):
    return {"name": name, "value": value, "status": status, "source": source}


def _user_row(name, value, unit):
    return _status_row(name, NOT_SET if value is None else f"{value:g} {unit}",
                       NOT_SET if value is None else "USER (test report)", ENTER if value is None else "entered")


# --- short circuit --------------------------------------------------------------

def simulate_short_circuit(sim: SimInput, ctx: dict | None = None) -> dict:
    bus = sim.bus
    if not bus.fault_ka:
        raise ValueError("fault_ka is required for the short-circuit simulation")
    validate.x_over_r("x_over_r", bus.x_over_r)
    if sim.cycles <= 0 or sim.steps_per_cycle < 8:
        raise ValueError("cycles must be > 0 and steps_per_cycle >= 8")
    for nm in ("tested_momentary_peak_ka", "tested_short_time_ka", "tested_short_time_s", "tested_block_load_n",
               "tested_force_n_per_m"):
        v = getattr(sim, nm)
        if v is not None and v <= 0:
            raise ValueError(f"{nm} must be > 0")
    if bus.fault_clearing_s is not None:
        validate.clearing_time("fault_clearing_s", bus.fault_clearing_s)
    ctx = ctx or build_context(bus)
    inp, cs, res, share, phase_idx = ctx["inp"], ctx["cs"], ctx["res"], ctx["share"], ctx["phase_idx"]
    f, xr, ka = inp.frequency_hz, inp.x_over_r, inp.fault_ka
    span = inp.support_span_m

    fr = fault_forces(cs, share, ka, xr, f)
    a_idx, a_worst = worst_closing_angle(cs, share, ka, xr, f)
    alpha = a_worst if sim.closing_angle_deg is None else math.radians(sim.closing_angle_deg)
    wf = fault_force_waveforms(cs, share, ka, xr, f, closing_angle_rad=alpha, cycles=sim.cycles,
                               steps_per_cycle=sim.steps_per_cycle)
    t_s = wf["t_s"]
    envelope = wf["force_envelope_n_per_m"]
    block = [e * span for e in envelope]
    wi = wf["worst_index"]
    w_c = cs[wi]

    # Phase-current peak: worst first-cycle peak over all closing angles, and at the selected angle.
    pk = first_peak_current(ka, xr, f)
    sel_peak = max(max(abs(v) for v in wf["phase_current_a"][p][: sim.steps_per_cycle + 1]) for p in PHASES)
    sel_i = max(range(sim.steps_per_cycle + 1),
                key=lambda k: max(abs(wf["phase_current_a"][p][k]) for p in PHASES))
    # DC-offset envelope of the phase with the largest initial offset.
    phi = math.atan(xr)
    tau = xr / (2 * math.pi * f)
    amp = math.sqrt(2) * ka * 1000
    env_k = first_max(range(3), lambda k: abs(math.sin(alpha - phi - 2 * math.pi * k / 3)))
    env_ph = PHASES[env_k]
    upper = [d + amp for d in wf["dc_component_a"][env_ph]]
    lower = [d - amp for d in wf["dc_component_a"][env_ph]]

    # Conductor temperature (adiabatic, ICEA P-32-382) for the conductor with the largest share.
    t_clear = bus.fault_clearing_s
    t_end = t_clear if t_clear else sim.cycles / f
    t0 = sim.initial_temp_c if sim.initial_temp_c is not None else float(inp.insulation_temp_c)
    area = cond.AREA_CMIL[inp.size]
    hot = first_max(phase_idx, lambda i: abs(share[i]))
    s_hot = share[hot]
    k_hot = PHASES.index(cs[hot].group)

    def temp_at(alpha_, t_):
        th = alpha_ - phi - 2 * math.pi * k_hot / 3 + math.atan2(s_hot.imag, s_hot.real)
        e = i2t_closed_form(abs(s_hot) * amp, th, t_, f, xr)
        return cond.adiabatic_temperature_c(inp.material, area, t0, e), e

    n_th = 200
    th_t = [t_end * k / n_th for k in range(n_th + 1)]
    th_c = [temp_at(alpha, t)[0] for t in th_t]
    final_sel, e_sel = temp_at(alpha, t_end)
    worst_heat = max(((temp_at(a, t_end)[0], a) for a in _angle_grid(24)), key=lambda v: v[0])
    final_worst = max(worst_heat[0], final_sel)

    # Let-through energy of the symmetrical and the worst asymmetrical phase current (kA^2 s, whole phase).
    i2t_sym = i2t_ka2s(ka, t_end)
    i2t_asym = max(i2t_closed_form(amp, a - phi - 2 * math.pi * k / 3, t_end, f, xr)
                   for a in _angle_grid(24) for k in range(3)) / 1e6

    # --- ratings checks ---
    checks = []
    peak_ka = pk["peak_a"] / 1000
    t_peak = sim.tested_momentary_peak_ka
    checks.append(_check("Momentary: first-cycle asymmetrical peak current within the tested peak", CLAUSE_SC,
                         peak_ka, t_peak, "kA", None if t_peak is None else peak_ka <= t_peak,
                         ("worst closing angle " + f"{pk['angle_deg']:.0f} deg, X/R {xr:g}; ") +
                         (ENTER if t_peak is None else "tested peak from the test report")))
    t_st, t_ds = sim.tested_short_time_ka, sim.tested_short_time_s
    if t_st is not None and t_ds is not None and t_clear:
        eq = equivalent_short_time_ka(t_st, t_ds, t_clear)
        checks.append(_check("Short-time: fault current within the tested rating at the clearing time (I2t basis)",
                             CLAUSE_SC, ka, eq, "kA", ka <= eq,
                             f"tested {t_st:g} kA for {t_ds:g} s = {i2t_ka2s(t_st, t_ds):.0f} kA2s; required "
                             f"{i2t_ka2s(ka, t_clear):.0f} kA2s at {t_clear:g} s"))
    else:
        why = ("enter fault_clearing_s" if not t_clear else ENTER)
        checks.append(_check("Short-time: fault current within the tested rating at the clearing time (I2t basis)",
                             CLAUSE_SC, ka, None, "kA", None, why))
    if sim.tested_force_n_per_m is not None:
        v = fr.worst_n_per_m
        checks.append(_check("Peak force per metre within the tested force", CLAUSE_SC, v,
                             sim.tested_force_n_per_m, "N/m", v <= sim.tested_force_n_per_m,
                             "worst conductor, worst closing angle"))
    else:
        checks.append(_check("Peak force per metre within the tested force", CLAUSE_SC, fr.worst_n_per_m, None,
                             "N/m", None, "optional; " + ENTER))
    worst_block = fr.worst_n_per_m * span
    if sim.tested_block_load_n is not None:
        checks.append(_check("Support block load within the tested block rating", CLAUSE_SC, worst_block,
                             sim.tested_block_load_n, "N", worst_block <= sim.tested_block_load_n,
                             f"force x {span:g} m span, worst closing angle"))
    else:
        checks.append(_check("Support block load within the tested block rating", CLAUSE_SC, worst_block, None,
                             "N", None, f"force x {span:g} m span; " + ENTER))
    mat = BLOCK_MATERIALS.get(sim.block_material) if sim.block_material else None
    if mat:
        ligament = min(ctx["result"].pitch_mm - ctx["od"], ctx["od"])
        stress = worst_block / (sim.block_thickness_mm * ligament)
        allow = mat["tensile"] / sim.block_safety_factor
        checks.append(_check(f"Block web stress screening ({sim.block_material})", "cable bus designer screening",
                             stress, allow, "MPa", stress <= allow,
                             "load / (thickness x ligament); allowable = tensile / safety factor; material values "
                             "UNVERIFIED; the tested block rating governs"))
    if t_clear:
        lim = inp.insulation_sc_limit_c
        checks.append(_check("Conductor temperature at clearing within the insulation short-circuit limit",
                             "ICEA P-32-382 (adiabatic)", final_worst, lim, "C", final_worst <= lim,
                             f"worst conductor, worst closing angle, from {t0:g} C, own current share"))
    else:
        checks.append(_check("Conductor temperature at clearing within the insulation short-circuit limit",
                             "ICEA P-32-382 (adiabatic)", final_worst, None, "C", None, "enter fault_clearing_s"))
    passed, complete = _verdict(checks)

    notes = [
        "Ratings and limits are the product's own CSA C22.2 No. 273 / IEEE C37.23 test-report values; the "
        "standards' test durations and pass criteria were not available (licensed) and are not used.",
        "Short-time equivalence uses I2t = constant (conductor heating), so it does not capture duration-dependent "
        "mechanical effects; the standard test remains the basis of the rating.",
        f"Peak current {peak_ka:.2f} kA = {peak_ka / ka:.3f} x rms sym at X/R {xr:g} (IEC 60909 approximation "
        f"{peak_factor(xr, f):.3f}); the force model is the time-domain Ampere law with the solved current sharing.",
        "Block load is the static force x span on one block (same basis as the designer screening); it is not "
        "an IEEE 605 bending analysis.",
    ]
    data_status = [
        _user_row("Tested momentary peak", sim.tested_momentary_peak_ka, "kA"),
        _user_row("Tested short-time current (rms sym)", sim.tested_short_time_ka, "kA"),
        _user_row("Tested short-time duration", sim.tested_short_time_s, "s"),
        _user_row("Tested block load", sim.tested_block_load_n, "N"),
        _user_row("Tested force per metre", sim.tested_force_n_per_m, "N/m"),
        _status_row("ICEA P-32-382 constants K, T0", "Cu 0.0297 / 234, Al 0.0125 / 228", "UNVERIFIED",
                    "conductors.ADIABATIC, from memory"),
        _status_row("Block material strength", sim.block_material or "none", "UNVERIFIED",
                    "typical NEMA LI 1 / supplier values"),
        _status_row("Force model", "2e-7 i1 i2 / d, time domain", "UNVERIFIED",
                    "IEEE 605 / IEC 60865 physics; no standard text read"),
        _status_row("Peak-factor reference rows", "ANSI 2.7, IEC 2.6 (60 Hz), asym rms 1.6", "UNVERIFIED",
                    "secondary sources, LOW confidence, informational only"),
    ]
    return {
        "x_over_r": xr, "frequency_hz": f, "fault_ka": ka, "clearing_s": t_clear, "span_m": span,
        "closing_angle_deg": math.degrees(alpha), "worst_angle_deg": math.degrees(a_worst),
        "t_s": t_s, "phase_current_a": wf["phase_current_a"], "envelope_phase": env_ph,
        "envelope_upper_a": upper, "envelope_lower_a": lower,
        "peak_current_ka": peak_ka, "peak_current_angle_deg": pk["angle_deg"], "peak_current_phase": pk["phase"],
        "peak_at_selected_ka": sel_peak / 1000, "peak_at_selected_time_s": t_s[sel_i],
        "peak_factor_computed": peak_ka / ka, "peak_factor_iec60909": peak_factor(xr, f),
        "reference_peak_factors": {k: v["value"] for k, v in DATA["peak_factors"].items()},
        "worst_conductor": {"index": wi, "phase": w_c.group, "x_mm": round(w_c.x_mm, 1),
                            "y_mm": round(w_c.y_mm, 1)},
        "force_worst_n_per_m": wf["force_worst_n_per_m"], "force_envelope_n_per_m": envelope,
        "block_load_n": block,
        "peak_force_n_per_m": wf["peak_n_per_m"], "peak_force_first_cycle_n_per_m": wf["peak_first_cycle_n_per_m"],
        "worst_force_n_per_m": fr.worst_n_per_m, "worst_force_lbf_per_ft": fr.worst_n_per_m * N_PER_M_TO_LBF_PER_FT,
        "peak_block_load_n": max(block), "worst_block_load_n": worst_block,
        "worst_block_load_lbf": worst_block * N_PER_M_TO_LBF,
        "thermal": {"t_s": th_t, "temp_c": th_c, "initial_c": t0, "t_end_s": t_end, "final_c": final_sel,
                    "final_c_worst_angle": final_worst, "worst_heating_angle_deg": math.degrees(worst_heat[1]),
                    "conductor_index": hot, "share_abs": abs(s_hot), "i2t_a2s": e_sel},
        "i2t_sym_ka2s": i2t_sym, "i2t_asym_ka2s": i2t_asym,
        "equivalent_rating_ka": (equivalent_short_time_ka(t_st, t_ds, t_clear)
                                 if (t_st and t_ds and t_clear) else None),
        "checks": checks, "passed": passed, "complete": complete, "notes": notes, "data_status": data_status,
    }


# --- temperature rise -----------------------------------------------------------

def sim_construction(inp: CableBusInput, od: float) -> CableConstruction:
    """Cable construction for the thermal model; builds an LV cable from the OD when none is given."""
    cons = construction(inp)
    if cons is not None:
        return cons
    dc = cond.diameter_mm(inp.size)
    return CableConstruction(inp.size, inp.material, inp.insulation, max((od - dc) / 2, 0.1), inp.shield_mm,
                             inp.jacket_mm, inp.jacket, inp.voltage_v, inp.insulation_temp_c)


def installation_for(pitch_mm: float, od_mm: float) -> str:
    return "isolated" if pitch_mm - od_mm >= 0.75 * od_mm else "flat_touching"


def steady_state_cable(c: CableConstruction, current_a: float, ambient_c: float = 40.0,
                       installation: str = "isolated", lambda1: float = 0.0, freq: float = 60.0,
                       spacing_mm: float | None = None) -> dict:
    """Conductor and surface temperature of one cable in free air at a given current.

    Forward solution of the circuit used by thermal.free_air_ampacity (IEC 60287 / Neher-McGrath):

        dtheta_c = I^2 R [T1 + (1 + l1)(T3 + T4)] + Wd (0.5 T1 + T3 + T4)
        T4 = u / Ws,  u = surface rise = (Ws / (pi De h))^(1/(1+1/4)),  Ws = I^2 R (1 + l1) + Wd

    with R = R_ac(theta_c) iterated to convergence. At the ampacity current this returns the rated conductor
    temperature.
    """
    validate.voltage("voltage_v", c.voltage_v)
    rated_v = c.rated_voltage_v if c.rated_voltage_v is not None else c.voltage_v
    rho_i = insulation_resistivity(c.insulation, rated_v)
    t1 = rho_i / (2 * math.pi) * math.log(1 + 2 * c.insulation_mm / c.dc_mm)
    t3 = (THERMAL_RESISTIVITY[c.jacket] / (2 * math.pi) * math.log(1 + 2 * c.jacket_mm / c.da_mm)
          if c.jacket_mm else 0.0)
    wd = dielectric_loss(c, freq)
    z, e, g = AIR_CONSTANTS[installation]
    de_m = c.de_mm / 1000
    h = z / de_m ** g + e
    theta = ambient_c
    r = cond.rac_ohm_per_m(c.size, c.material, theta, freq, spacing_mm=spacing_mm)
    u = 0.0
    ws = 0.0
    for _ in range(500):
        r = cond.rac_ohm_per_m(c.size, c.material, theta, freq, spacing_mm=spacing_mm)
        x = current_a ** 2 * r
        ws = x * (1 + lambda1) + wd
        u = (ws / (math.pi * de_m * h)) ** 0.8
        nxt = ambient_c + x * t1 + 0.5 * wd * t1 + ws * t3 + u
        if abs(nxt - theta) < 1e-10:
            theta = nxt
            break
        theta = nxt
    x = current_a ** 2 * r
    ws = x * (1 + lambda1) + wd
    return {"theta_c": theta, "surface_c": ambient_c + u, "shield_c": ambient_c + u + ws * t3,
            "r_ohm_per_m": r, "conductor_loss_w_per_m": x, "heat_w_per_m": ws, "dielectric_w_per_m": wd,
            "t1": t1, "t3": t3, "t4": u / ws if ws > 0 else float("inf"), "lambda1": lambda1,
            "surface_rise_c": u}


def heat_capacity_j_per_m_k(c: CableConstruction) -> dict:
    """Thermal capacitance per metre of one cable (conductor, insulation, shield tape, jacket)."""
    hc = DATA["volumetric_heat_capacity_j_per_m3_k"]
    dc, di, da, de = c.dc_mm / 1000, c.di_mm / 1000, c.da_mm / 1000, c.de_mm / 1000
    a_cond = cond.area_mm2(c.size) * 1e-6
    q_cond = a_cond * hc[c.material]
    q_ins = math.pi / 4 * (di ** 2 - dc ** 2) * hc[c.insulation]
    q_shield = math.pi * (c.shield_mean_diameter_mm / 1000) * (c.shield_mm / 1000) * hc["Cu"] if c.shield_mm else 0.0
    q_jacket = math.pi / 4 * (de ** 2 - da ** 2) * hc[c.jacket] if c.jacket_mm else 0.0
    return {"conductor": q_cond, "insulation": q_ins, "shield": q_shield, "jacket": q_jacket,
            "total": q_cond + q_ins + q_shield + q_jacket}


def enclosure_surface_temperature(q_w_per_m: float, w_out_mm: float, h_out_mm: float, ambient_c: float,
                                  emissivity: float) -> dict:
    """Outer surface temperature of the enclosure that rejects q W per metre of run (an estimate).

    Faces per metre: two vertical sides (height H), top and bottom (width W). Free convection from the
    simplified laminar air correlations h = C (dT / L)^0.25 (C = 1.42 vertical, 1.32 top, 0.59 bottom), and
    grey-body radiation to the ambient. Uniform surface temperature, no ventilation or solar credit;
    solved by bisection on the surface rise.
    """
    cv = DATA["enclosure_convection"]
    sigma = cv["stefan_boltzmann"]
    w_m, h_m = w_out_mm / 1000, h_out_mm / 1000
    ta = ambient_c + 273.15

    def parts(rise):
        ts = ta + rise
        conv_v = cv["c_vertical"] * (rise / h_m) ** 0.25 * (2 * h_m) * rise
        conv_t = cv["c_top"] * (rise / w_m) ** 0.25 * w_m * rise
        conv_b = cv["c_bottom"] * (rise / w_m) ** 0.25 * w_m * rise
        rad = emissivity * sigma * (ts ** 4 - ta ** 4) * (2 * h_m + 2 * w_m)
        return conv_v + conv_t + conv_b, rad

    lo, hi = 0.0, 400.0
    for _ in range(200):
        mid = (lo + hi) / 2
        c_, r_ = parts(mid)
        if c_ + r_ < q_w_per_m:
            lo = mid
        else:
            hi = mid
    rise = (lo + hi) / 2
    c_, r_ = parts(rise)
    area = 2 * h_m + 2 * w_m
    return {"rise_k": rise, "surface_c": ambient_c + rise, "q_convection_w_per_m": c_, "q_radiation_w_per_m": r_,
            "h_rad_w_per_m2_k": r_ / area / rise if rise > 0 else 0.0,
            "h_conv_avg_w_per_m2_k": c_ / area / rise if rise > 0 else 0.0, "perimeter_m": area}


def simulate_temperature_rise(sim: SimInput, ctx: dict | None = None) -> dict:
    bus = sim.bus
    if sim.load_scale <= 0:
        raise ValueError("load_scale must be > 0")
    for nm in ("rise_limit_conductor_k", "rise_limit_enclosure_k", "rise_limit_termination_k"):
        v = getattr(sim, nm)
        if v is not None and v <= 0:
            raise ValueError(f"{nm} must be > 0")
    if sim.enclosure_emissivity is not None and not 0 < sim.enclosure_emissivity <= 1:
        raise ValueError("enclosure_emissivity must be in (0, 1]")
    ctx = ctx or build_context(bus)
    inp, cs, res, od, phase_idx = ctx["inp"], ctx["cs"], ctx["res"], ctx["od"], ctx["phase_idx"]
    cons = sim_construction(inp, od)
    pitch = ctx["result"].pitch_mm
    installation = installation_for(pitch, od)
    ambient = inp.ambient_c
    labels = {c.label: i for i, c in enumerate(cs)}

    def shield_lambda1(i):
        core_loss = res.losses_w_per_m[i]
        s = labels.get(f"S-{cs[i].label}")
        return round(res.losses_w_per_m[s] / core_loss, 4) if s is not None and core_loss else 0.0

    amp_cache: dict[float, float] = {}
    cables = []
    heat_cables = 0.0
    for i in phase_idx:
        lam = shield_lambda1(i)
        cur = abs(res.currents[i]) * sim.load_scale
        ss = steady_state_cable(cons, cur, ambient, installation, lam, inp.frequency_hz, pitch)
        if lam not in amp_cache:
            amp_cache[lam] = free_air_ampacity(cons, ambient, installation, lam, inp.frequency_hz, pitch).ampacity_a
        heat_cables += ss["heat_w_per_m"]
        cables.append({"index": i, "phase": cs[i].group, "x_mm": round(cs[i].x_mm, 1), "y_mm": round(cs[i].y_mm, 1),
                       "current_a": cur, "lambda1": lam, "ampacity_a": amp_cache[lam], "theta_c": ss["theta_c"],
                       "rise_k": ss["theta_c"] - ambient, "surface_c": ss["surface_c"], "shield_c": ss["shield_c"],
                       "r_ohm_per_m": ss["r_ohm_per_m"], "heat_w_per_m": ss["heat_w_per_m"],
                       "conductor_loss_w_per_m": ss["conductor_loss_w_per_m"], "t4": ss["t4"]})
    hot = first_max(range(len(cables)), lambda k: cables[k]["theta_c"])
    hc = cables[hot]

    # Enclosure estimate.
    encl = None
    q_encl_induced = ctx["result"].enclosure_loss_w / inp.length_m * sim.load_scale ** 2
    emis = sim.enclosure_emissivity if sim.enclosure_emissivity is not None else \
        DATA["enclosure_convection"]["default_emissivity"]
    notes = []
    if inp.enclosure_width_mm:
        ys = [cs[i].y_mm for i in phase_idx]
        h_in = inp.enclosure_height_mm or (max(ys) - min(ys) + 2 * od)
        w_out = inp.enclosure_width_mm + 2 * inp.side_thickness_mm
        h_out = h_in + 2 * inp.cover_thickness_mm
        q_total = heat_cables + q_encl_induced
        encl = enclosure_surface_temperature(q_total, w_out, h_out, ambient, emis)
        encl.update({"q_total_w_per_m": q_total, "q_induced_w_per_m": q_encl_induced, "emissivity": emis,
                     "width_out_mm": w_out, "height_out_mm": h_out})
    else:
        notes.append("Enclosure estimate skipped: give enclosure_width_mm (and height) to include it.")

    # Warm-up of the hottest cable: one-node first-order response to a step from ambient.
    caps = heat_capacity_j_per_m_k(cons)
    r_th = (hc["theta_c"] - ambient) / hc["heat_w_per_m"] if hc["heat_w_per_m"] > 0 else 0.0
    tau = caps["total"] * r_th
    rise_inf = hc["theta_c"] - ambient
    n_w = 100
    t_w = [5 * tau * k / n_w for k in range(n_w + 1)]
    th_w = [ambient + rise_inf * (1 - math.exp(-t / tau)) if tau > 0 else hc["theta_c"] for t in t_w]
    warm = {"t_s": t_w, "temp_c": th_w, "tau_s": tau, "r_th_k_m_per_w": r_th, "capacity_j_per_m_k": caps,
            "t95_s": -tau * math.log(0.05) if tau > 0 else 0.0, "rise_inf_k": rise_inf}

    # Checks.
    checks = [_check("Hottest conductor within the insulation temperature rating", "insulation rating",
                     hc["theta_c"], float(inp.insulation_temp_c), "C", hc["theta_c"] <= inp.insulation_temp_c,
                     f"at {sim.load_scale * 100:.0f} % of design current, ambient {ambient:g} C, free-air thermal "
                     "model [UNVERIFIED constants]")]
    lc = sim.rise_limit_conductor_k
    checks.append(_check("Hottest conductor rise within the test-report conductor rise limit", CLAUSE_TR,
                         hc["rise_k"], lc, "K", None if lc is None else hc["rise_k"] <= lc,
                         f"rise above {ambient:g} C ambient; " + (ENTER if lc is None else "limit from test report")))
    le = sim.rise_limit_enclosure_k
    if encl is None:
        checks.append(_check("Accessible enclosure surface rise within the test-report limit", CLAUSE_TR, None, le,
                             "K", None, "enclosure not modelled (give enclosure_width_mm)"))
    else:
        checks.append(_check("Accessible enclosure surface rise within the test-report limit", CLAUSE_TR,
                             encl["rise_k"], le, "K", None if le is None else encl["rise_k"] <= le,
                             "estimate (convection + radiation, no ventilation credit); " +
                             (ENTER if le is None else "limit from test report")))
    lt, rt = sim.rise_limit_termination_k, sim.termination_rise_k
    checks.append(_check("Termination rise within the test-report limit", CLAUSE_TR, rt, lt, "K",
                         None if (lt is None or rt is None) else rt <= lt,
                         "termination rise is not simulated; enter an estimate or the tested rise" +
                         ("" if lt is not None else " and the limit")))
    passed, complete = _verdict(checks)
    notes += [
        "Steady state: IEC 60287 / Neher-McGrath free-air circuit solved forward at each cable's own current "
        "(current sharing from the impedance solve); mutual heating between cables and tiers is not included.",
        "Enclosure surface temperature is an estimate from a lumped heat balance; the temperature-rise type test "
        "is the certification basis.",
        "Warm-up is a simplified one-node model: tau = C x R, C = conductor + insulation + shield + jacket "
        "thermal capacitance, R = conductor-to-ambient resistance at the operating point; the enclosure's own "
        "thermal mass is ignored, so real warm-up of the enclosure is slower.",
        "Rise limits are user inputs from the test report; C37.23 / CSA 273 limit values were not available.",
    ]
    data_status = [
        _user_row("Conductor rise limit", sim.rise_limit_conductor_k, "K"),
        _user_row("Enclosure (accessible surface) rise limit", sim.rise_limit_enclosure_k, "K"),
        _user_row("Termination rise limit", sim.rise_limit_termination_k, "K"),
        _user_row("Termination rise estimate", sim.termination_rise_k, "K"),
        _status_row("IEC 60287 thermal constants (T1, T4 air, dielectric)", "thermal.py tables", "UNVERIFIED",
                    "IEC 60287-1-1 / -2-1 from memory"),
        _status_row("Volumetric heat capacities", "Cu 3.45, Al 2.5, XLPE/EPR 2.4, PVC 1.7 MJ/m3K", "UNVERIFIED",
                    DATA["volumetric_heat_capacity_j_per_m3_k"]["_meta"]["url"]),
        _status_row("Enclosure convection correlations", "C = 1.42 / 1.32 / 0.59", "UNVERIFIED",
                    DATA["enclosure_convection"]["_meta"]["url"]),
        _status_row("Enclosure emissivity", f"{emis:g}",
                    "USER" if sim.enclosure_emissivity is not None else "FLAGGED DEFAULT",
                    "set the enclosure finish" if sim.enclosure_emissivity is None else "entered"),
    ]
    return {"ambient_c": ambient, "load_scale": sim.load_scale, "installation": installation, "cables": cables,
            "hottest_index": hot, "hottest": hc, "enclosure": encl, "warmup": warm, "checks": checks,
            "passed": passed, "complete": complete, "notes": notes, "data_status": data_status,
            "max_theta_c": hc["theta_c"], "min_theta_c": min(c["theta_c"] for c in cables)}


def simulate(sim: SimInput) -> dict:
    """Both simulations on one solve. The short circuit part needs bus.fault_ka."""
    ctx = build_context(sim.bus)
    out = {"temperature": simulate_temperature_rise(sim, ctx)}
    out["short_circuit"] = simulate_short_circuit(sim, ctx) if sim.bus.fault_ka else None
    return out
