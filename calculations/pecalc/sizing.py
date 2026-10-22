"""Feeder conductor sizing: ampacity, parallel sets, voltage drop, losses.

For each number of parallel sets the smallest conductor passing every check
is found; the option with the least total conductor area is recommended and
the alternatives are kept so the engineer can choose.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from functools import cache

from . import ampacity as amp
from . import conductors as cond
from . import reactance_derived as rxd
from . import validate
from .lugs import default_terminal_temp

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
    notes: list[str] = field(default_factory=list)

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
        found = rxd.reactance_per_1000ft(size, inp.conduit)
        if found is not None:
            x_kft, derived = found
            basis = f"DERIVED from NEC Ch. 9 Table 9 [{rxd.DERIVED_STATUS}]" if derived else "NEC Ch. 9 Table 9"
            return x_kft / 1000 / cond.FT, basis
    # Cables touching in trefoil (tray / free air).
    return cond.reactance_ohm_per_m(size, cond.cable_od_mm(size), inp.frequency_hz), "geometric (trefoil, touching)"


@cache
def _small_conductor_limits() -> dict:
    """NEC 240.4(D) maximum overcurrent device rating by size (data/nec_240_4d_small_conductors.json)."""
    return json.loads((amp.DATA / "nec_240_4d_small_conductors.json").read_text())


def small_conductor_limit_a(material: str, size: str) -> float | None:
    """NEC 240.4(D) limit in A, or None when 240.4(D) does not list the size. [UNVERIFIED data]"""
    v = _small_conductor_limits().get(material, {}).get(cond.normalize_size(size))
    return None if v is None else float(v)


def _short_circuit_check(inp: FeederInput, size: str, sets: int) -> Check | None:
    """ICEA P-32-382 adiabatic withstand (see conductors.adiabatic_withstand_a)."""
    if inp.fault_ka is None or inp.fault_clearing_s is None:
        return None
    withstand_a = cond.adiabatic_withstand_a(inp.material, cond.AREA_CMIL[size] * sets, inp.insulation_temp_c,
                                             inp.insulation_sc_limit_c, inp.fault_clearing_s)
    return Check("Short-circuit withstand (all sets)", "ICEA P-32-382", round(withstand_a / 1000, 1),
                 inp.fault_ka, "kA", withstand_a / 1000 >= inp.fault_ka,
                 f"{inp.fault_clearing_s} s clearing, {inp.insulation_temp_c}->{inp.insulation_sc_limit_c} C; "
                 "250 C is the thermoset (XLPE/EPR) limit, thermoplastic insulation has a lower limit "
                 "[UNVERIFIED, ICEA P-32-382]")


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
    # NEC 110.14(C): termination limits use the 60/75 C column of Table 310.16 whatever the
    # installation; free-air (Table 310.17) ampacity applies to the conductor only.
    # CEC Rule 4-006 is left on the installation's own table [UNVERIFIED which CEC table applies].
    term_install = "raceway" if code == "NEC" else inp.installation
    # NEC 110.14(C)(1) / CEC 4-006: when no terminal rating is given, the default depends on the
    # candidate conductor size (60 C for 14-1 AWG or circuits of 100 A or less, else 75 C).
    notes: list[str] = []
    if inp.terminal_temp_c is None:
        t_term, t_basis = default_terminal_temp(code, inp.load_a, size)
        notes.append(f"Terminal temperature {t_term} C by default: {t_basis}")
    else:
        t_term = inp.terminal_temp_c
        notes.append(f"Terminal temperature {t_term} C as given (equipment marking)")
    a_term = amp.table_ampacity(code, term_install, mat, size, t_term)
    if a_ins is None or a_term is None:
        raise ValueError(f"No {code} {inp.installation} ampacity for {mat} {size}")

    f_amb = amp.ambient_factor(inp.ambient_c, inp.insulation_temp_c)
    f_ccc = amp.ccc_factor(code, inp.current_carrying_per_raceway) if inp.installation == "raceway" else 1.0
    derated = a_ins * f_amb * f_ccc
    allowable = min(derated, a_term)
    # NEC 110.14(C): the conductor cannot use a column above the lowest temperature rating of any
    # connected termination or conductor, so the termination check uses the lesser of the conductor's
    # own (undeflated) insulation-column ampacity and the terminal column.
    a_cond = min(a_ins, a_term)
    if inp.installation == "raceway" and sets * inp.phases > inp.current_carrying_per_raceway:
        notes.append(f"{sets} sets x {inp.phases} phase conductors exceed current_carrying_per_raceway="
                     f"{inp.current_carrying_per_raceway}: the grouping adjustment assumes separate raceways per set")
    per_set_load = inp.load_a / sets

    if code == "NEC":
        cont_mult = 1.0 if inp.hundred_percent_rated else 1.25
        required_term = (cont_mult * inp.continuous_a + inp.noncontinuous_a) / sets
        term_table = amp.table_info(code, term_install).table_name
        checks.append(Check("Terminal-column ampacity >= 125 % continuous + non-continuous",
                            f"{clauses['continuous']}(a), {clauses['terminal']}",
                            a_cond, round(required_term, 1), "A", a_cond >= required_term,
                            f"lesser of {term_table} {inp.insulation_temp_c} C insulation column ({a_ins:.0f} A) and "
                            f"{t_term} C terminal column ({a_term:.0f} A), no derating; the conductor cannot "
                            f"use a column above its terminations' rating (NEC 110.14(C))"))
        # NEC 240.4(D): the overcurrent device for 18-10 AWG may not exceed the listed rating.
        # The device must be at least 125 % continuous + non-continuous (215.3; 100 % if listed),
        # so that minimum rating is checked against the limit. Small sizes cannot be paralleled.
        limit = small_conductor_limit_a(mat, size)
        if limit is not None:
            ocpd_min = cont_mult * inp.continuous_a + inp.noncontinuous_a
            checks.append(Check("Minimum OCPD rating <= small-conductor limit", "NEC 240.4(D) [data UNVERIFIED]",
                                round(ocpd_min, 1), limit, "A", ocpd_min <= limit,
                                f"{cond.size_label(size)} {mat}: max overcurrent device {limit:g} A"))
        checks.append(Check("Derated ampacity >= load", f"{clauses['continuous']}(b)",
                            round(derated, 1), round(per_set_load, 1), "A", derated >= per_set_load,
                            f"{a_ins:.0f} A x {f_amb:.3f} ambient x {f_ccc:.2f} grouping"))
    else:  # CEC: continuous load limited to 80 % (100 % rated: 100 %) of conductor ampacity
        cont_div = 1.0 if inp.hundred_percent_rated else 0.80
        required = (inp.continuous_a / cont_div + inp.noncontinuous_a) / sets
        checks.append(Check("Allowable ampacity >= continuous / 0.8 + non-continuous",
                            f"{clauses['continuous']}, {clauses['terminal']}",
                            round(allowable, 1), round(required, 1), "A", allowable >= required,
                            f"min({a_ins:.0f} A x {f_amb:.3f} x {f_ccc:.2f}, {t_term} C column {a_term:.0f} A)"))
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
                  round(r * 1000, 4), round(x * 1000, 4), checks, notes)


def _validate_input(inp: FeederInput) -> None:
    if inp.code not in amp.CODES:
        raise ValueError(f"code must be one of {amp.CODES}")
    if inp.material not in cond.MATERIALS:
        raise ValueError("material must be 'Cu' or 'Al'")
    validate.non_negative("continuous_a", inp.continuous_a, "A")
    validate.non_negative("noncontinuous_a", inp.noncontinuous_a, "A")
    if inp.load_a <= 0:
        raise ValueError("load current must be positive (continuous_a + noncontinuous_a must be greater than 0 A)")
    validate.voltage("voltage_v", inp.voltage_v)
    validate.one_of("phases", inp.phases, (1, 3))
    validate.positive("length_m", inp.length_m, "m")
    validate.power_factor("power_factor", inp.power_factor)
    validate.positive("max_vd_pct", inp.max_vd_pct, "%")
    validate.positive("frequency_hz", inp.frequency_hz, "Hz")
    validate.integer_at_least("current_carrying_per_raceway", inp.current_carrying_per_raceway, 1)
    validate.in_range("ambient_c", inp.ambient_c, -50, 100, "C")
    validate.in_range("conductor_temp_for_vd_c", inp.conductor_temp_for_vd_c, -50, 250, "C")
    validate.one_of("insulation_temp_c", inp.insulation_temp_c, amp.COLUMNS)
    if inp.terminal_temp_c is not None:
        validate.one_of("terminal_temp_c", inp.terminal_temp_c, amp.COLUMNS)
    if inp.sets is not None:
        validate.integer_at_least("sets", inp.sets, 1)
    validate.integer_at_least("max_sets", inp.max_sets, 1)
    validate.positive("insulation_sc_limit_c", inp.insulation_sc_limit_c, "C")
    if (inp.fault_ka is None) != (inp.fault_clearing_s is None):
        raise ValueError("fault_ka and fault_clearing_s must be given together for the short-circuit check; "
                         "only one was given")
    if inp.fault_clearing_s is not None:
        validate.clearing_time("fault_clearing_s", inp.fault_clearing_s)
    if inp.fault_ka is not None:
        validate.positive("fault_ka", inp.fault_ka, "kA")
    if inp.installation not in amp.INSTALLATIONS:
        raise ValueError(f"installation must be one of {amp.INSTALLATIONS}")
    if inp.installation == "raceway" and inp.conduit not in rxd.RACEWAYS:
        raise ValueError(f"conduit must be one of {rxd.RACEWAYS}")
    if inp.code == "NEC" and inp.voltage_v > 1000:
        raise ValueError("voltage_v above 1000 V is outside NEC Article 215 (feeders not over 1000 V ac, "
                         "NFPA 70-2023 215.1); Part III of Article 235 applies above 1000 V and is not implemented")
    if inp.voltage_v > 2000:
        raise ValueError("This module covers 0-2000 V conductors; medium-voltage tables are not loaded yet")


def size_feeder(inp: FeederInput) -> FeederResult:
    _validate_input(inp)
    status = amp.check_status(inp.code, inp.allow_placeholder_data)
    info = amp.table_info(inp.code, inp.installation)

    table = json.loads((amp.DATA / f"ampacity_{inp.code.lower()}.json").read_text())
    sizes = [s for s in cond.SIZES if s in table[inp.installation][inp.material]]
    set_range = [inp.sets] if inp.sets is not None else range(1, inp.max_sets + 1)

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
    if inp.code == "NEC":
        notes.append("NEC 240.4(D) small-conductor limits are checked against the minimum overcurrent device "
                     "rating (data UNVERIFIED); the rest of 240.4 and device selection are not checked here.")
        if inp.installation == "free_air":
            notes.append("Terminations checked against Table 310.16 at the terminal temperature (NEC 110.14(C)); "
                         "conductor ampacity from Table 310.17.")
    else:
        notes.append("Overcurrent device selection and protection (CEC 14-104) are not checked here.")
    if inp.installation == "raceway":
        notes.append(f"Grouping adjustment uses current_carrying_per_raceway={inp.current_carrying_per_raceway} "
                     "current-carrying conductors per raceway (default 3: each parallel set in its own raceway).")
    if not options:
        notes.append("No conductor size passes every check within the allowed number of sets.")
    best = options[0] if options else None
    if best and inp.installation == "raceway" and best.size in rxd.DERIVED_SIZES:
        notes.append(f"WARNING: reactance for {best.size_label} in {inp.conduit} conduit is not in NEC Table 9; "
                     f"value used is {rxd.DERIVED_STATUS}. Method: {rxd.DERIVED_METHOD}")
    lugs = None
    if options:
        from .lugs import LugInput, select_lugs
        best = options[0]
        lugs = select_lugs(LugInput(code=inp.code, size=best.size, material=inp.material, sets_per_phase=best.sets,
                                    phases=inp.phases, circuit_current_a=inp.load_a,
                                    equipment_terminal_temp_c=inp.terminal_temp_c))  # None: lugs derives its own default
    return FeederResult(inp, status, info.table_name, options[0] if options else None, options[1:6], notes, lugs)
