"""Command line: python -m pecalc feeder|cablebus [options]   (add --json for machine output)."""

from __future__ import annotations

import argparse
import sys

from .ampacity import DataStatusError
from .cablebus import CableBusInput, analyse
from .lugs import LugInput, select_lugs
from .sizing import FeederInput, size_feeder

FT = 0.3048


def _length_m(value: float, unit: str) -> float:
    return value * FT if unit == "ft" else value


def _row(c) -> str:
    mark = "PASS" if c["passed"] else "FAIL"
    return f"  [{mark}] {c['name']}: {c['value']} vs {c['limit']} {c['unit']}  ({c['clause']}){'  - ' + c['note'] if c.get('note') else ''}"


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
                        insulation=a.insulation, insulation_mm=a.insulation_mm, shield_mm=a.shield_mm,
                        jacket_mm=a.jacket_mm, jacket=a.jacket,
                        shield_bonding=a.shield_bonding, shield_area_mm2=a.shield_area,
                        shield_mean_diameter_mm=a.shield_diameter, fault_ka=a.fault_ka, x_over_r=a.xr,
                        support_span_m=a.support_span, max_vd_pct=a.max_vd,
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
          f"conductor loss {r.conductor_loss_w/1000:.2f} kW, shield loss {r.shield_loss_w/1000:.2f} kW")
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
    c.add_argument("--shield-bonding", choices=["none", "single_point", "both_ends"], default="none")
    c.add_argument("--shield-area", type=float, help="shield copper area per cable, mm2")
    c.add_argument("--shield-diameter", type=float, help="shield mean diameter, mm")
    c.add_argument("--xr", type=float, default=15.0, help="X/R ratio at the fault point")
    c.add_argument("--support-span", type=float, default=0.9144, help="support/block spacing, m")
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

    a = p.parse_args(argv)
    if a.ambient is None:
        a.ambient = 40.0 if a.cmd == "cablebus" else 30.0
    try:
        return a.func(a)
    except (ValueError, DataStatusError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
