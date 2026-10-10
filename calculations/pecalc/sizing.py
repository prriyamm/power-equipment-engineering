"""Feeder conductor sizing: ampacity, parallel sets, voltage drop, losses.

For each number of parallel sets the smallest conductor passing every check
is found; the option with the least total conductor area is recommended and
the alternatives are kept so the engineer can choose.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field

from . import ampacity as amp
from . import conductors as cond

FT_PER_M = 1 / cond.FT


@dataclass
class FeederInput:
    code: str = "NEC"                 # "NEC" or "CEC"
    voltage_v: float = 480.0          # line-to-line for 3-phase
    phases: int = 3
    continuous_a: float = 0.0         # continuous part of the load current
    noncontinuous_a: float = 0.0
    length_m: float = 30.0            # one-way length
    material: str = "Cu"
    insulation_temp_c: int = 90
    terminal_temp_c: int | None = None  # None: NEC 110.14(C)(1) / CEC 4-006 default by current
    installation: str = "raceway"     # "raceway" or "free_air"
    ambient_c: float = 30.0
    current_carrying_per_raceway: int = 3
    conduit: str = "pvc"              # "pvc", "aluminum" or "steel" (raceway reactance)
    power_factor: float = 0.85
    max_vd_pct: float = 3.0
    hundred_percent_rated: bool = False  # OCPD/equipment listed for 100 % continuous
    sets: int | None = None           # force a number of parallel sets
    max_sets: int = 8
    frequency_hz: float = 60.0
    conductor_temp_for_vd_c: float = 75.0
    fault_ka: float | None = None     # optional conductor short-circuit check
    fault_clearing_s: float | None = None
    insulation_sc_limit_c: float = 250.0  # XLPE/EPR; use 150 for thermoplastic
    allow_placeholder_data: bool = False

    @property
    def load_a(self) -> float:
        return self.continuous_a + self.noncontinuous_a


@dataclass
class Check:
    name: str
    clause: str
    value: float
    limit: float
    unit: str
    passed: bool
    note: str = ""


@dataclass
class Option:
    sets: int
    size: str
    size_label: str
    total_area_mm2: float
    ampacity_per_set_a: float
    vd_pct: float
    vd_v: float
    loss_w: float
    r_ohm_per_km: float
    x_ohm_per_km: float
    checks: list[Check] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)


@dataclass
class FeederResult:
    input: FeederInput
    data_status: str
    table: str
    recommended: Option | None
    alternatives: list[Option]
    notes: list[str]
    lugs: object | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, default=str)


def _reactance_ohm_per_m(inp: FeederInput, size: str) -> tuple[float, str]:
    if inp.installation == "raceway":
        data = json.loads((amp.DATA / "reactance_nec_table9.json").read_text())
        x_kft = data[inp.conduit].get(size)
        if x_kft is not None:
            return x_kft / 1000 / cond.FT, "NEC Ch. 9 Table 9"
    # Cables touching in trefoil (tray / free air) or sizes beyond Table 9.
    return cond.reactance_ohm_per_m(size, cond.cable_od_mm(size), inp.frequency_hz), "geometric (trefoil, touching)"


def _short_circuit_check(inp: FeederInput, size: str, sets: int) -> Check | None:
    """ICEA P-32-382 adiabatic withstand: (I/A)^2 t = K log10((T2+T0)/(T1+T0)).

    [UNVERIFIED: K = 0.0297 Cu / 0.0125 Al with A in cmil, I in A]
    """
    if not (inp.fault_ka and inp.fault_clearing_s):
        return None
    k, t0 = (0.0297, 234.0) if inp.material == "Cu" else (0.0125, 228.0)
    area = cond.AREA_CMIL[size] * sets
    withstand_a = area * math.sqrt(
        k * math.log10((inp.insulation_sc_limit_c + t0) / (inp.insulation_temp_c + t0)) / inp.fault_clearing_s
    )
    return Check("Short-circuit withstand (all sets)", "ICEA P-32-382", round(withstand_a / 1000, 1),
                 inp.fault_ka, "kA", withstand_a / 1000 >= inp.fault_ka,
                 f"{inp.fault_clearing_s} s clearing, {inp.insulation_temp_c}->{inp.insulation_sc_limit_c} C")


def evaluate(inp: FeederInput, size: str, sets: int) -> Option:
    code, mat = inp.code, inp.material
    clauses = amp.CLAUSES[code]
    checks: list[Check] = []

    if sets > 1:
        min_size = amp.PARALLEL_MIN[code][mat]
        checks.append(Check("Minimum size for parallel sets", clauses["parallel"],
                            cond.size_index(size), cond.size_index(min_size), "size index",
                            cond.size_index(size) >= cond.size_index(min_size), f"min {cond.size_label(min_size)}"))

    a_ins = amp.table_ampacity(code, inp.installation, mat, size, inp.insulation_temp_c)
    a_term = amp.table_ampacity(code, inp.installation, mat, size, inp.terminal_temp_c)
    if a_ins is None or a_term is None:
        raise ValueError(f"No {code} {inp.installation} ampacity for {mat} {size}")

    f_amb = amp.ambient_factor(inp.ambient_c, inp.insulation_temp_c)
    f_ccc = amp.ccc_factor(code, inp.current_carrying_per_raceway) if inp.installation == "raceway" else 1.0
    derated = a_ins * f_amb * f_ccc
    allowable = min(derated, a_term)
    per_set_load = inp.load_a / sets

    if code == "NEC":
        cont_mult = 1.0 if inp.hundred_percent_rated else 1.25
        required_term = (cont_mult * inp.continuous_a + inp.noncontinuous_a) / sets
        checks.append(Check("Terminal-column ampacity >= 125 % continuous + non-continuous",
                            f"{clauses['continuous']}(a), {clauses['terminal']}",
                            a_term, round(required_term, 1), "A", a_term >= required_term,
                            f"{inp.terminal_temp_c} C column, no derating"))
        checks.append(Check("Derated ampacity >= load", f"{clauses['continuous']}(b)",
                            round(derated, 1), round(per_set_load, 1), "A", derated >= per_set_load,
                            f"{a_ins:.0f} A x {f_amb:.3f} ambient x {f_ccc:.2f} grouping"))
    else:  # CEC: continuous load limited to 80 % (100 % rated: 100 %) of conductor ampacity
        cont_div = 1.0 if inp.hundred_percent_rated else 0.80
        required = (inp.continuous_a / cont_div + inp.noncontinuous_a) / sets
        checks.append(Check("Allowable ampacity >= continuous / 0.8 + non-continuous",
                            f"{clauses['continuous']}, {clauses['terminal']}",
                            round(allowable, 1), round(required, 1), "A", allowable >= required,
                            f"min({a_ins:.0f} A x {f_amb:.3f} x {f_ccc:.2f}, {inp.terminal_temp_c} C column {a_term:.0f} A)"))
    checks.append(Check("Allowable ampacity (lesser of derated and terminal column) >= load",
                        clauses["terminal"], round(allowable, 1), round(per_set_load, 1), "A",
                        allowable >= per_set_load))

    # Voltage drop and losses at the actual load current.
    od = cond.cable_od_mm(size)
    r = cond.rac_ohm_per_m(size, mat, inp.conductor_temp_for_vd_c, inp.frequency_hz, spacing_mm=od)
    x, x_basis = _reactance_ohm_per_m(inp, size)
    pf = inp.power_factor
    z_eff = r * pf + x * math.sqrt(1 - pf * pf)
    k = math.sqrt(3) if inp.phases == 3 else 2.0
    vd_v = k * inp.load_a * inp.length_m * z_eff / sets
    vd_pct = vd_v / inp.voltage_v * 100
    n_cond = 3 if inp.phases == 3 else 2
    loss_w = n_cond * inp.load_a ** 2 * r * inp.length_m / sets
    checks.append(Check("Voltage drop", clauses["vd"], round(vd_pct, 2), inp.max_vd_pct, "%",
                        vd_pct <= inp.max_vd_pct, f"R {r*1000:.4f} ohm/km at {inp.conductor_temp_for_vd_c:.0f} C, "
                        f"X {x*1000:.4f} ohm/km ({x_basis}), pf {pf}"))

    sc = _short_circuit_check(inp, size, sets)
    if sc:
        checks.append(sc)

    return Option(sets, size, cond.size_label(size), round(cond.area_mm2(size) * sets, 1),
                  round(allowable, 1), round(vd_pct, 2), round(vd_v, 2), round(loss_w, 1),
                  round(r * 1000, 4), round(x * 1000, 4), checks)


def size_feeder(inp: FeederInput) -> FeederResult:
    if inp.code not in amp.CODES:
        raise ValueError(f"code must be one of {amp.CODES}")
    if inp.material not in cond.MATERIALS:
        raise ValueError("material must be 'Cu' or 'Al'")
    if inp.load_a <= 0:
        raise ValueError("load current must be positive")
    if inp.voltage_v > 2000:
        raise ValueError("This module covers 0-2000 V conductors; medium-voltage tables are not loaded yet")
    if inp.terminal_temp_c is None:
        inp.terminal_temp_c = 60 if inp.load_a <= 100 else 75
    status = amp.check_status(inp.code, inp.allow_placeholder_data)
    info = amp.table_info(inp.code, inp.installation)

    table = json.loads((amp.DATA / f"ampacity_{inp.code.lower()}.json").read_text())
    sizes = [s for s in cond.SIZES if s in table[inp.installation][inp.material]]
    set_range = [inp.sets] if inp.sets else range(1, inp.max_sets + 1)

    options = []
    for n in set_range:
        for size in sizes:
            opt = evaluate(inp, size, n)
            if opt.passed:
                options.append(opt)
                break
    options.sort(key=lambda o: (o.total_area_mm2, o.sets))

    notes = [f"Ampacity table: {inp.code} {info.table_name} ({info.edition}) - data status {status}."]
    if status != "VERIFIED":
        notes.append(f"WARNING: {info.source}")
    notes.append("Overcurrent device selection and protection (NEC 240.4 / CEC 14-104) are not checked here.")
    if not options:
        notes.append("No conductor size passes every check within the allowed number of sets.")
    lugs = None
    if options:
        from .lugs import LugInput, select_lugs
        best = options[0]
        lugs = select_lugs(LugInput(code=inp.code, size=best.size, material=inp.material, sets_per_phase=best.sets,
                                    phases=inp.phases, circuit_current_a=inp.load_a,
                                    equipment_terminal_temp_c=inp.terminal_temp_c))
    return FeederResult(inp, status, info.table_name, options[0] if options else None, options[1:6], notes, lugs)
