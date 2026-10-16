"""Command line: python -m pecalc feeder|cablebus [options]   (add --json for machine output)."""

from __future__ import annotations

import argparse
import sys

from .ampacity import DataStatusError
from .cases import Case
from .cablebus_design import DesignRequest, design_options
from .cablebus import CableBusInput, analyse
from .lugs import LugInput, select_lugs
from .switchgear import BusInput, analyse_bus
from .transformer import TransformerInput, design, design_for_impedance, next_standard_kva
from .sizing import FeederInput, size_feeder

FT = 0.3048


def _length_m(value: float, unit: str) -> float:
    return value * FT if unit == "ft" else value


def _row(c) -> str:
    mark = "PASS" if c["passed"] else "FAIL"
    return f"  [{mark}] {c['name']}: {c['value']} vs {'not determined' if c['limit'] is None else c['limit']} {c['unit']}  ({c['clause']}){'  - ' + c['note'] if c.get('note') else ''}"


def feeder(a: argparse.Namespace) -> int:
    inp = FeederInput(code=a.code, voltage_v=a.voltage, phases=a.phases, continuous_a=a.continuous,
                      noncontinuous_a=a.noncontinuous, length_m=_length_m(a.length, a.length_unit),
                      material=a.material, insulation_temp_c=a.insulation_temp, terminal_temp_c=a.terminal_temp,
                      installation=a.installation, ambient_c=a.ambient,
                      current_carrying_per_raceway=a.ccc, conduit=a.conduit, power_factor=a.pf,
                      max_vd_pct=a.max_vd, hundred_percent_rated=a.hundred_percent, sets=a.sets,
                      fault_ka=a.fault_ka, fault_clearing_s=a.fault_time,
                      allow_placeholder_data=a.allow_placeholder_data)
    r = size_feeder(inp)
    if a.json:
        print(r.to_json())
        return 0 if r.recommended else 1
    print(f"Feeder sizing - {inp.code}, {inp.voltage_v:g} V {inp.phases}-phase, load {inp.load_a:g} A "
          f"({inp.continuous_a:g} continuous), {inp.length_m:.1f} m, {inp.material}, {inp.installation}")
    if not r.recommended:
        print("  No conductor passes all checks.")
    else:
        o = r.recommended
        print(f"\nRECOMMENDED: {o.sets} set(s) of {o.size_label} {inp.material} per phase")
        print(f"  allowable {o.ampacity_per_set_a} A per set, VD {o.vd_pct} % ({o.vd_v} V), loss {o.loss_w/1000:.2f} kW")
        print(f"  R {o.r_ohm_per_km} ohm/km, X {o.x_ohm_per_km} ohm/km per conductor")
        for c in o.checks:
            print(_row(c.__dict__))
        if r.lugs:
            print("\nLugs (one end):")
            for l in r.lugs.lines:
                print(f"  {l.quantity} x {l.conductor}: {l.style}, {l.stud_in} in stud"
                      f"{', ' + l.hole_spacing_in + ' in centres' if l.hole_spacing_in else ''}")
        if r.alternatives:
            print("\nAlternatives (all pass):")
            for alt in r.alternatives:
                print(f"  {alt.sets} x {alt.size_label}: VD {alt.vd_pct} %, loss {alt.loss_w/1000:.2f} kW, "
                      f"copper {alt.total_area_mm2} mm2/phase")
    print()
    for n in r.notes:
        print(f"Note: {n}")
    return 0 if r.recommended else 1


def cablebus(a: argparse.Namespace) -> int:
    inp = CableBusInput(code=a.code, voltage_v=a.voltage, current_a=a.current, power_factor=a.pf,
                        length_m=_length_m(a.length, a.length_unit), material=a.material, size=a.size,
                        conductors_per_phase=a.per_phase, tiers=a.tiers, cable_od_mm=a.od,
                        spacing_mm=a.spacing, tier_spacing_mm=a.tier_spacing, pattern=a.pattern,
                        insulation_temp_c=a.insulation_temp, terminal_temp_c=a.terminal_temp, ambient_c=a.ambient,
                        ampacity_method=a.ampacity_method,
                        cable_ampacity_a=a.cable_ampacity, cable_ampacity_ambient_c=a.cable_ampacity_ambient,
                        cable_ampacity_lambda1_ref=a.cable_ampacity_lambda1,
                        insulation=a.insulation, insulation_mm=a.insulation_mm, shield_mm=a.shield_mm,
                        jacket_mm=a.jacket_mm, jacket=a.jacket,
                        shield_bonding=a.shield_bonding, shield_area_mm2=a.shield_area,
                        shield_mean_diameter_mm=a.shield_diameter, fault_ka=a.fault_ka,
                        fault_clearing_s=a.fault_time, x_over_r=a.xr, support_span_m=a.support_span, max_vd_pct=a.max_vd,
                        enclosure_width_mm=a.enclosure_width, enclosure_height_mm=a.enclosure_height,
                        side_thickness_mm=a.side_mm, cover_thickness_mm=a.cover_mm,
                        covers_continuous=a.covers_continuous, enclosure_alloy=a.alloy,
                        allow_placeholder_data=a.allow_placeholder_data)
    r = analyse(inp)
    if a.json:
        print(r.to_json())
        return 0 if r.passed else 1
    print(f"Cable bus - {inp.code}, {inp.voltage_v:g} V, {inp.current_a:g} A, {inp.conductors_per_phase} x "
          f"{inp.size} {inp.material} per phase in {inp.tiers} tier(s), {inp.length_m:.1f} m")
    print(f"\nRESULT: {'PASS' if r.passed else 'FAIL'}")
    print(f"  Phase pattern: {r.pattern}   layout {r.layout_width_mm:.0f} x {r.layout_height_mm:.0f} mm (conductor envelope)")
    print(f"  Ampacity per cable: {r.ampacity_basis}")
    print(f"  Worst conductor loading {r.max_loading_pct} %, voltage drop {r.vd_pct} %, "
          f"conductor loss {r.conductor_loss_w/1000:.2f} kW, shield loss {r.shield_loss_w/1000:.2f} kW, "
          f"enclosure loss {r.enclosure_loss_w/1000:.2f} kW")
    for c in r.checks:
        print(_row(c))
    print("\nConductor currents (A, % of equal share):")
    for c in r.conductors:
        print(f"  {c.phase}  tier {c.tier}  x={c.x_mm:7.1f} mm  {c.current_a:8.1f} A  {c.share_pct:6.1f} %  "
              f"loading {c.loading_pct:5.1f} %")
    if len(r.patterns_compared) > 1:
        print("\nPatterns compared (worst share %, loss W/m):")
        for p in r.patterns_compared:
            print(f"  {p.pattern:<30} {p.max_share_pct:6.1f} %  {p.loss_w_per_m:8.1f}")
    print()
    for n in r.notes:
        print(f"Note: {n}")
    return 0 if r.passed else 1


def lugs(a: argparse.Namespace) -> int:
    inp = LugInput(code=a.code, size=a.size, material=a.material, sets_per_phase=a.sets, phases=a.phases,
                   neutral=a.neutral, neutral_size=a.neutral_size, ground_size=a.ground_size,
                   circuit_current_a=a.current, equipment_terminal_temp_c=a.terminal_temp,
                   termination=a.termination, pad_positions=a.pad_positions, pad_two_sided=not a.one_sided)
    r = select_lugs(inp)
    if a.json:
        print(r.to_json())
        return 0 if r.passed else 1
    print(f"Lug selection - {inp.code}, {inp.sets_per_phase} x {inp.size} {inp.material} per phase, "
          f"{inp.circuit_current_a:g} A, termination: {inp.termination}")
    print(f"  Termination temperature: {r.terminal_temp_c} C ({r.terminal_temp_basis})")
    for l in r.lines:
        extra = ", ".join(x for x in (l.part_no and f"part {l.part_no}", l.die and f"die {l.die}",
                                      l.torque and f"torque {l.torque}") if x)
        print(f"  {l.quantity:3d} x {l.terminal}: {l.conductor} - {l.style}; {l.lug_material}; stud {l.stud_in} in"
              f"{'; ' + l.hole_spacing_in + ' in centres' if l.hole_spacing_in else ''}{'; ' + extra if extra else ''}")
    print(f"  Total lugs per end: {r.total_lugs}")
    for c in r.checks:
        print(_row(c))
    for n in r.notes:
        print(f"Note: {n}")
    return 0 if r.passed else 1


def bus(a: argparse.Namespace) -> int:
    inp = BusInput(current_a=a.current, voltage_v=a.voltage, standard=a.standard, material=a.material,
                   bar_thickness_mm=a.thickness, bar_width_mm=a.width, bars_per_phase=a.bars,
                   bar_gap_mm=a.gap, phase_spacing_mm=a.phase_spacing, orientation=a.orientation,
                   finish=a.finish, ambient_c=a.ambient, internal_air_rise_c=a.air_rise, max_rise_c=a.max_rise,
                   fault_ka=a.fault_ka, x_over_r=a.xr, support_span_m=a.span, support_condition=a.support,
                   yield_mpa=a.yield_mpa, support_rating_n=a.support_rating)
    r = analyse_bus(inp)
    if a.json:
        print(r.to_json())
        return 0 if r.passed else 1
    print(f"Switchgear bus - {inp.standard}, {inp.current_a:g} A, {inp.bars_per_phase} x "
          f"{inp.bar_thickness_mm} x {inp.bar_width_mm} mm {inp.material} per phase, {inp.orientation}, "
          f"phase spacing {inp.phase_spacing_mm} mm")
    print(f"\nRESULT: {'PASS' if r.passed else 'FAIL'}")
    print(f"  Temperature rise {r.rise_c} C at {inp.current_a:g} A; rating at {inp.max_rise_c} C rise: "
          f"{r.rated_current_at_limit_a} A")
    print(f"  Rac/Rdc {r.rac_over_rdc}, loss {r.loss_w_per_m_per_phase} W/m per phase, "
          f"lamination currents {r.lamination_share_pct} % of equal share")
    if r.peak_force_n_per_m is not None:
        print(f"  Fault: {r.peak_force_n_per_m:.0f} N/m on a phase, bending stress {r.bending_stress_mpa} MPa, "
              f"support load {r.support_load_n:.0f} N, max span {r.max_span_m} m")
    for c in r.checks:
        print(_row(c))
    for n in r.notes:
        print(f"Note: {n}")
    return 0 if r.passed else 1


def transformer(a: argparse.Namespace) -> int:
    kva = a.kva or next_standard_kva(a.load_kva, a.growth)
    inp = TransformerInput(kva=kva, hv_v=a.hv, lv_v=a.lv, hv_connection=a.hv_conn, lv_connection=a.lv_conn,
                           kind=a.kind, conductor=a.conductor, b_max_t=a.bmax, k_et=a.k, j_lv_a_mm2=a.j_lv,
                           j_hv_a_mm2=a.j_hv, target_z_pct=a.target_z, power_factor=a.pf,
                           source_mva=a.source_mva, source_x_over_r=a.source_xr,
                           doe_min_efficiency_pct=a.doe_eff, bil_kv=a.bil, doe_date=a.doe_date,
                           doe_submersible=a.submersible)
    r = design_for_impedance(inp) if (a.target_z and a.tune) else design(inp)
    if a.json:
        print(r.to_json())
        return 0 if r.passed else 1
    print(f"Transformer preliminary design - {kva:g} kVA, {a.hv:g} V {a.hv_conn} / {a.lv:g} V {a.lv_conn}, "
          f"{a.kind}, {a.conductor} windings")
    print(f"\nRESULT: {'PASS' if r.passed else 'FAIL'}")
    for title, d in (("Design", r.design), ("Losses", r.losses), ("Impedance", r.impedance),
                     ("Performance", r.performance), ("Short circuit", r.short_circuit)):
        print(f"  {title}: " + ", ".join(f"{k} {v}" for k, v in d.items()))
    for c in r.checks:
        print(_row(c))
    for n in r.notes:
        print(f"Note: {n}")
    return 0 if r.passed else 1


def run_case(a: argparse.Namespace) -> int:
    case = Case.load(a.case)
    result = case.run()
    passed = bool(getattr(result, "passed", True)) and not (case.module == "feeder" and not result.recommended)
    if a.report:
        from .report import write_report
        print(f"Report written to {write_report(case, result, a.report)}")
    if a.json:
        print(result.to_json())
    elif not a.report:
        print(f"{case.title or case.module}: {'PASS' if passed else 'FAIL'} (input hash {case.input_hash()})")
    return 0 if passed else 1


def cablebus_design(a: argparse.Namespace) -> int:
    req = DesignRequest(code=a.code, voltage_v=a.voltage, current_a=a.current, length_m=_length_m(a.length, a.length_unit),
                        material=a.material, ambient_c=a.ambient, sizes=tuple(a.sizes.split(",")) if a.sizes else None,
                        insulation=a.insulation, insulation_mm=a.insulation_mm, shield_mm=a.shield_mm,
                        jacket_mm=a.jacket_mm, fault_ka=a.fault_ka, x_over_r=a.xr, support_span_m=a.support_span,
                        block_material=a.block, block_rated_load_n=a.block_rating, max_loading_pct=a.max_loading,
                        allow_placeholder_data=a.allow_placeholder_data)
    r = design_options(req)
    if a.json:
        print(r.to_json())
        return 0 if any(o.passed for o in r.options) else 1
    print(f"Cable bus designs - {req.code}, {req.voltage_v:g} V, {req.current_a:g} A ({r.considered} checked)\n")
    print(f"{'#':>2}  {'Result':6} {'Design':58} {'Pattern':22} {'Load%':>6} {'VD%':>5} {'kW':>6} {'Block MPa':>11}")
    for o in r.options:
        blk = "" if o.block_stress_mpa is None else f"{o.block_stress_mpa}/{o.block_allowable_mpa}"
        print(f"{o.rank:>2}  {'PASS' if o.passed else 'FAIL':6} {o.label:58} {o.pattern:22} {o.max_loading_pct:6.1f} "
              f"{o.vd_pct:5.2f} {o.loss_kw:6.1f} {blk:>11}  {', '.join(o.tags) or '; '.join(o.failed_checks)}")
    if a.choose:
        o = next((x for x in r.options if x.rank == a.choose), None)
        if o is None:
            raise ValueError(f"No option #{a.choose}")
        case = Case(module="cablebus", inputs={k: (list(v) if isinstance(v, tuple) else v)
                                                for k, v in o.case_inputs.items()},
                    title=f"Cable bus: {o.label}")
        if a.save_case:
            case.save(a.save_case)
            print(f"\nCase saved to {a.save_case}")
        if a.report:
            from .report import write_report
            print(f"Report written to {write_report(case, case.run(), a.report)}")
    print()
    for n in r.notes:
        print(f"Note: {n}")
    return 0 if any(o.passed for o in r.options) else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="pecalc", description="Power equipment engineering calculations")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(s):
        s.add_argument("--code", choices=["NEC", "CEC"], default="NEC")
        s.add_argument("--voltage", type=float, required=True, help="line-to-line volts")
        s.add_argument("--length", type=float, required=True)
        s.add_argument("--length-unit", choices=["m", "ft"], default="ft")
        s.add_argument("--material", choices=["Cu", "Al"], default="Cu")
        s.add_argument("--pf", type=float, default=0.85)
        s.add_argument("--insulation-temp", type=int, choices=[60, 75, 90], default=90)
        s.add_argument("--ambient", type=float)
        s.add_argument("--max-vd", type=float, default=3.0)
        s.add_argument("--fault-ka", type=float)
        s.add_argument("--allow-placeholder-data", action="store_true",
                       help="run with PLACEHOLDER code tables (testing only)")
        s.add_argument("--json", action="store_true")

    f = sub.add_parser("feeder", help="size feeder conductors")
    common(f)
    f.add_argument("--phases", type=int, choices=[1, 3], default=3)
    f.add_argument("--continuous", type=float, default=0.0, help="continuous load, A")
    f.add_argument("--noncontinuous", type=float, default=0.0, help="non-continuous load, A")
    f.add_argument("--terminal-temp", type=int, choices=[60, 75, 90],
                   help="equipment termination rating; default per NEC 110.14(C) / CEC 4-006")
    f.add_argument("--installation", choices=["raceway", "free_air"], default="raceway")
    f.add_argument("--ccc", type=int, default=3, help="current-carrying conductors per raceway")
    f.add_argument("--conduit", choices=["pvc", "aluminum", "steel"], default="pvc")
    f.add_argument("--hundred-percent", action="store_true", help="equipment rated for 100 %% continuous")
    f.add_argument("--sets", type=int, help="force number of parallel sets")
    f.add_argument("--fault-time", type=float, help="fault clearing time, s")
    f.set_defaults(func=feeder, ambient=None)

    c = sub.add_parser("cablebus", help="check a cable bus design")
    common(c)
    c.add_argument("--current", type=float, required=True, help="rated current per phase, A")
    c.add_argument("--size", required=True, help="conductor size, e.g. 750 or 4/0")
    c.add_argument("--per-phase", type=int, required=True, help="conductors per phase")
    c.add_argument("--tiers", type=int, default=1)
    c.add_argument("--od", type=float, help="cable outside diameter, mm (required above 2000 V)")
    c.add_argument("--spacing", type=float, help="centre spacing in a tier, mm (default 2 x OD)")
    c.add_argument("--tier-spacing", type=float, help="centre spacing between tiers, mm")
    c.add_argument("--pattern", default="auto", help="e.g. ABCCBA or ABCCBA/CBAABC, default: try several")
    c.add_argument("--terminal-temp", type=int, choices=[60, 75, 90], default=90)
    c.add_argument("--ampacity-method", choices=["auto", "table", "datasheet", "calculated"], default="auto",
                   help="auto: datasheet if given, else code table (<=2000 V), else IEC 60287 calculation")
    c.add_argument("--insulation", choices=["XLPE", "EPR", "PVC", "XHHW", "RW90"], default="XLPE")
    c.add_argument("--insulation-mm", type=float, help="insulation wall incl. screens, mm (enables calculation)")
    c.add_argument("--shield-mm", type=float, default=0.0, help="metallic shield thickness, mm")
    c.add_argument("--jacket-mm", type=float, default=0.0, help="jacket thickness, mm")
    c.add_argument("--jacket", choices=["PVC", "PE"], default="PVC")
    c.add_argument("--cable-ampacity", type=float, help="datasheet free-air rating per cable, A")
    c.add_argument("--cable-ampacity-ambient", type=float, default=40.0)
    c.add_argument("--cable-ampacity-lambda1", type=float, default=0.0,
                   help="shield loss factor lambda1 the datasheet rating assumes (0 = single-point / cross-bonded)")
    c.add_argument("--fault-time", type=float, help="fault clearing time, s (enables conductor withstand check)")
    c.add_argument("--shield-bonding", choices=["none", "single_point", "both_ends"], default="none")
    c.add_argument("--shield-area", type=float, help="shield copper area per cable, mm2")
    c.add_argument("--shield-diameter", type=float, help="shield mean diameter, mm")
    c.add_argument("--xr", type=float, default=15.0, help="X/R ratio at the fault point")
    c.add_argument("--support-span", type=float, default=0.9144, help="support/block spacing, m")
    c.add_argument("--enclosure-width", type=float, help="enclosure inside width, mm (enables housing model)")
    c.add_argument("--enclosure-height", type=float, help="enclosure inside height, mm")
    c.add_argument("--side-mm", type=float, default=6.35, help="side rail thickness, mm")
    c.add_argument("--cover-mm", type=float, default=3.175, help="cover thickness, mm")
    c.add_argument("--covers-continuous", action="store_true", help="covers/bottom electrically continuous")
    c.add_argument("--alloy", choices=["6063-T6", "6061-T6", "1350"], default="6063-T6")
    c.set_defaults(func=cablebus)

    g = sub.add_parser("lugs", help="select lugs for a termination")
    g.add_argument("--code", choices=["NEC", "CEC"], default="NEC")
    g.add_argument("--size", required=True)
    g.add_argument("--material", choices=["Cu", "Al"], default="Cu")
    g.add_argument("--sets", type=int, default=1, help="parallel sets per phase")
    g.add_argument("--phases", type=int, choices=[1, 3], default=3)
    g.add_argument("--current", type=float, required=True, help="circuit rating, A")
    g.add_argument("--neutral", action="store_true")
    g.add_argument("--neutral-size")
    g.add_argument("--ground-size")
    g.add_argument("--terminal-temp", type=int, choices=[60, 75, 90])
    g.add_argument("--termination", choices=["bus", "stud", "breaker"], default="bus")
    g.add_argument("--pad-positions", type=int, help="2-hole positions per phase on the pad")
    g.add_argument("--one-sided", action="store_true", help="lugs on one face of the pad only")
    g.add_argument("--json", action="store_true")
    g.set_defaults(func=lugs, ambient=0)

    b = sub.add_parser("bus", help="check switchgear / switchboard bus bars")
    b.add_argument("--current", type=float, required=True)
    b.add_argument("--voltage", type=float, default=600.0)
    b.add_argument("--standard", default="UL 891")
    b.add_argument("--material", choices=["Cu", "Al"], default="Cu")
    b.add_argument("--thickness", type=float, required=True, help="bar thickness, mm")
    b.add_argument("--width", type=float, required=True, help="bar width, mm")
    b.add_argument("--bars", type=int, default=1, help="laminations per phase")
    b.add_argument("--gap", type=float, help="gap between laminations, mm (default = thickness)")
    b.add_argument("--phase-spacing", type=float, required=True, help="centre-to-centre, mm")
    b.add_argument("--orientation", choices=["face_to_face", "edge_to_edge"], default="face_to_face")
    b.add_argument("--finish", choices=["bare", "tin", "silver", "painted"], default="tin")
    b.add_argument("--ambient", type=float, default=40.0)
    b.add_argument("--air-rise", type=float, default=0.0, help="enclosure internal air rise, C")
    b.add_argument("--max-rise", type=float, default=65.0, help="allowable rise per product standard, C")
    b.add_argument("--fault-ka", type=float)
    b.add_argument("--xr", type=float, default=15.0)
    b.add_argument("--span", type=float, default=0.6, help="support spacing, m")
    b.add_argument("--support", choices=["continuous", "pinned", "fixed"], default="continuous")
    b.add_argument("--yield-mpa", type=float)
    b.add_argument("--support-rating", type=float, help="support/insulator rated load, N")
    b.add_argument("--json", action="store_true")
    b.set_defaults(func=bus)

    t = sub.add_parser("transformer", help="preliminary transformer design and checks")
    t.add_argument("--kva", type=float, help="rating; or give --load-kva to pick the next standard size")
    t.add_argument("--load-kva", type=float)
    t.add_argument("--growth", type=float, default=1.0, help="growth factor applied to --load-kva")
    t.add_argument("--hv", type=float, required=True, help="HV line voltage")
    t.add_argument("--lv", type=float, required=True, help="LV line voltage")
    t.add_argument("--hv-conn", choices=["delta", "wye"], default="delta")
    t.add_argument("--lv-conn", choices=["delta", "wye"], default="wye")
    t.add_argument("--kind", choices=["liquid", "dry"], default="liquid")
    t.add_argument("--conductor", choices=["Cu", "Al"], default="Cu")
    t.add_argument("--bmax", type=float, default=1.55, help="design flux density, T")
    t.add_argument("--k", type=float, default=0.45, help="Et = K sqrt(kVA) constant")
    t.add_argument("--j-lv", type=float, default=3.0, help="LV current density, A/mm2")
    t.add_argument("--j-hv", type=float, default=3.0, help="HV current density, A/mm2")
    t.add_argument("--target-z", type=float, help="specified impedance, %%")
    t.add_argument("--tune", action="store_true", help="tune window proportions to meet --target-z")
    t.add_argument("--pf", type=float, default=0.9)
    t.add_argument("--source-mva", type=float, help="utility fault MVA at HV terminals")
    t.add_argument("--source-xr", type=float, default=10.0,
                   help="utility source X/R at HV terminals (default 10, UNVERIFIED typical)")
    t.add_argument("--doe-eff", type=float, help="extra user minimum efficiency at the DOE point, %% (the 10 CFR "
                   "431.196 tables are built in)")
    t.add_argument("--bil", type=float, help="HV winding BIL, kV (needed for the medium-voltage dry-type DOE minimum)")
    t.add_argument("--doe-date", help="manufacture date YYYY-MM-DD selecting the 10 CFR 431.196 window (default today)")
    t.add_argument("--submersible", action="store_true", help="liquid-immersed submersible unit (DOE)")
    t.add_argument("--json", action="store_true")
    t.set_defaults(func=transformer, ambient=0)

    d = sub.add_parser("cablebus-design", help="recommend cable bus designs (sizes, tiers, layout, enclosure)")
    common(d)
    d.add_argument("--current", type=float, required=True)
    d.add_argument("--sizes", help="comma-separated sizes to try, e.g. 500,750,1000")
    d.add_argument("--insulation", choices=["XLPE", "EPR", "PVC", "XHHW", "RW90"], default="XLPE")
    d.add_argument("--insulation-mm", type=float, help="MV insulation wall incl. screens, mm")
    d.add_argument("--shield-mm", type=float, default=0.0)
    d.add_argument("--jacket-mm", type=float, default=0.0)
    d.add_argument("--xr", type=float, default=15.0)
    d.add_argument("--support-span", type=float, default=0.9144)
    d.add_argument("--block", choices=["GPO-3", "GPO-2", "GPO-1"], default="GPO-3")
    d.add_argument("--block-rating", type=float, help="tested block load per cable position, N")
    d.add_argument("--max-loading", type=float, default=95.0)
    d.add_argument("--choose", type=int, help="option number to save / report")
    d.add_argument("--save-case", help="save the chosen option as a case file")
    d.add_argument("--report", help="write the chosen option's calculation package (HTML)")
    d.set_defaults(func=cablebus_design)

    r = sub.add_parser("run", help="run a saved design case file")
    r.add_argument("case", help="case JSON file")
    r.add_argument("--report", help="write a printable HTML calculation package to this path")
    r.add_argument("--json", action="store_true")
    r.set_defaults(func=run_case, ambient=0)

    a = p.parse_args(argv)
    if a.cmd == "transformer" and not (a.kva or a.load_kva):
        p.error("transformer needs --kva or --load-kva")
    if a.ambient is None:
        a.ambient = 40.0 if a.cmd in ("cablebus", "cablebus-design") else 30.0
    try:
        return a.func(a)
    except (ValueError, DataStatusError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
