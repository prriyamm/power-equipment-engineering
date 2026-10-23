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
import functools
import itertools
import json
import math
from dataclasses import asdict, dataclass, field, replace

from . import ampacity as amp
from . import conductors as cond
from . import validate
from .field import LIMITS_UT, b_rms_ut
from .forces import N_PER_M_TO_LBF_PER_FT, fault_forces
from .impedance import Conductor, Group, balanced_three_phase, open_circuit_voltages, solve_sharing
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
    # Cable library: "standard" (NEC sizes; default), "mv_construction" (same path, MV construction inputs) or
    # "dlo_2000v" (manufacturer row from data/dlo_cables.json, selected by cable_id such as
    # "southwire_dlo_2000v:444.4"). Library cables take area, OD, DC resistance and ampacity from the data file.
    cable_type: str = "standard"
    cable_id: str | None = None
    conductors_per_phase: int = 3
    tiers: int = 1
    cable_od_mm: float | None = None   # required above 2000 V; estimated for LV if omitted
    spacing_mm: float | None = None    # centre-to-centre in a tier; default 2 x OD (1 OD clearance)
    tier_spacing_mm: float | None = None  # centre-to-centre between tiers; default = spacing
    pattern: str = "auto"              # e.g. "ABCCBA" or "ABCCBA/CBAABC" for tiers, or "auto"
    insulation_temp_c: int = 90
    # Equipment termination rating (NEC 110.14(C) / CEC 4-006). None = derive from the voltage: 75 C up to
    # 2000 V (NEC 110.14(C)(1)(b)), 90 C above 2000 V (NEC 110.40). An explicit value always wins.
    terminal_temp_c: int | None = None
    ambient_c: float = 40.0
    # Ampacity method: "auto" (datasheet if given, else code table for LV, else
    # calculated), "table", "datasheet" or "calculated" (IEC 60287 thermal model).
    ampacity_method: str = "auto"
    cable_ampacity_a: float | None = None      # datasheet free-air rating per cable
    cable_ampacity_ambient_c: float = 40.0
    # Shield loss factor lambda1 already included in the datasheet rating. Datasheet ratings for
    # single-point or cross-bonded shields carry no circulating loss, so the default is 0.
    # Used to derate the datasheet rating when shields are bonded at both ends.
    cable_ampacity_lambda1_ref: float = 0.0
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
    # Shield short-circuit withstand (optional): ground-fault current returning through the shields of the
    # faulted phase's cables, shared equally, and the copper shield temperature limit [UNVERIFIED: 250 C is a
    # typical figure; use the cable maker's value]. Needs fault_clearing_s and a shield area.
    ground_fault_ka: float | None = None
    shield_sc_limit_c: float = 250.0
    # Single-point bonding: length of one bonded (minor) section; the shield is grounded at one end of
    # each section and the standing voltage builds up to the open end. None = the whole run.
    shield_section_length_m: float | None = None
    # Owner / utility limit for the open-end standing voltage at normal load. No verified public value
    # exists (IEEE 575 practice ~25 V is a LOW-confidence secondary figure), so there is no default.
    shield_voltage_limit_v: float | None = None
    # Short circuit
    fault_ka: float | None = None
    fault_clearing_s: float | None = None  # optional; enables the conductor short-circuit withstand check
    insulation_sc_limit_c: float = 250.0   # XLPE/EPR; use 150 for thermoplastic
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
    sheath: dict | None = None   # shield standing voltage and bonding comparison (shielded cable only)
    cable_data: dict | None = None   # library cable used (data, status, source), None for standard cable

    @property
    def passed(self) -> bool:
        return all(c["passed"] for c in self.checks)

    def to_json(self) -> str:
        return json.dumps(asdict(self) | {"passed": self.passed}, indent=2, default=str)


def default_terminal_temp_c(voltage_v: float) -> tuple[int, str]:
    """Default equipment termination temperature and its basis (used when terminal_temp_c is None)."""
    if voltage_v <= 2000:
        return 75, ("Termination temperature defaulted to 75 C: NEC 110.14(C)(1)(b) (circuits over 100 A or "
                    "conductors larger than 1 AWG; cable bus conductors are 1/0 minimum per NEC 370.20(A)(2)) "
                    "(NFPA 70-2023 pp. 70-65, 70-253). Set terminal_temp_c to 90 if the equipment is listed and "
                    "identified for 90 C conductors (110.14(C)(1)(b)(2)), or to the listed rating of separately "
                    "installed pressure connectors (110.14(C)(2)).")
    return 90, ("Termination temperature defaulted to 90 C above 2000 V: NEC 110.40, unless otherwise identified "
                "(NFPA 70-2023 p. 70-73).")


def termination_ampacity(inp: CableBusInput, size: str, terminal_temp_c: int) -> tuple[float | None, str, str]:
    """Termination ampacity per conductor and the table used: (ampacity or None, table key, reason if None).

    NEC 110.14(C): the termination provisions are based on Table 310.16 (raceway) whatever the installation
    (same rule as sizing.py); CEC 4-006 keeps the installation's table [UNVERIFIED which CEC table applies].
    Only <= 2000 V tables are loaded.
    """
    table = "raceway" if inp.code == "NEC" else "free_air"
    if inp.voltage_v > 2000:
        return None, table, ("code ampacity tables are loaded for <= 2000 V only (above that, check the "
                             "equipment termination rating, NEC 110.40)")
    try:
        amp.check_status(inp.code, inp.allow_placeholder_data)
        a = amp.table_ampacity(inp.code, table, inp.material, size, terminal_temp_c)
    except (ValueError, amp.DataStatusError) as e:
        return None, table, str(e)
    if a is None:
        return None, table, f"no {inp.code} {table} table row for {inp.material} {size}"
    return a, table, ""


def require_ambient_below(ambient_c: float, conductor_temp_c: float) -> None:
    """A site ambient at or above the conductor rating gives zero ampacity (and later a zero-division)."""
    if ambient_c >= conductor_temp_c:
        raise ValueError(f"ambient_c ({ambient_c:g} C) must be below the conductor temperature rating "
                         f"({conductor_temp_c:g} C)")


def ambient_factor_checked(ambient_c: float, conductor_temp_c: int, rated_ambient_c: float = 30.0) -> float:
    """amp.ambient_factor for the cable bus paths: raises instead of returning 0."""
    require_ambient_below(ambient_c, conductor_temp_c)
    return amp.ambient_factor(ambient_c, conductor_temp_c, rated_ambient_c)


def validate_input(inp: CableBusInput) -> None:
    """Range checks on the numeric inputs, with messages that name the input."""
    validate.voltage("voltage_v", inp.voltage_v)
    validate.positive("current_a", inp.current_a, "A")
    validate.positive("length_m", inp.length_m, "m")
    validate.positive("frequency_hz", inp.frequency_hz, "Hz")
    validate.count_at_least("tiers", inp.tiers)
    validate.count_at_least("conductors_per_phase", inp.conductors_per_phase)
    if inp.fault_ka is not None:
        validate.non_negative("fault_ka", inp.fault_ka, "kA")


# --- cable library (manufacturer rows) --------------------------------------
# Library cables are only reachable through cable_type "dlo_2000v", so the non-standard DLO sizes
# (262.6 ... 1111 kcmil) stay out of the NEC size list used by the code tables.

LIBRARY_FILE = amp.DATA / "dlo_cables.json"
DLO_STRANDING_FACTOR = cond.STRANDING_FACTOR   # 1.02, same as the standard path; not verified for Class I stranding
# Conductor diameter / sqrt(area) for Class I stranding: 0.782 in / (sqrt(444 400 cmil) / 1000 in) = 1.173.
# Single-point ratio from the Southwire 444.4 kcmil product page. [UNVERIFIED proxy, used only when not printed]
DLO_DIAMETER_RATIO = 0.782 / (math.sqrt(444400) / 1000)
CABLE_TYPES = ("standard", "mv_construction", "dlo_2000v")


@dataclass(frozen=True)
class CableSpec:
    cable_id: str
    manufacturer: str
    series: str
    size: str                       # size key as printed, e.g. "444.4" or "4/0"
    size_label: str
    area_cmil: float
    od_mm: float                    # printed nominal OD
    insulation_mm: float            # printed insulation wall
    diameter_mm: float              # conductor diameter used (printed, or proxy below)
    diameter_source: str            # "printed" or "proxy"
    rdc_ref: tuple[float, float] | None   # printed DC resistance (ohm per 1000 ft, reference C), or None
    rated_voltage_v: float
    temp_c: int
    ampacity_free_air_a: float      # printed free-air ampacity, 90 C conductor
    ampacity_ref_ambient_c: float
    ampacity_basis: str
    basis_stated: bool
    standard_nec_size: bool
    listed_rhh: bool
    status: str
    source_name: str
    source_url: str
    source_date: str
    flags: tuple[str, ...]

    def as_dict(self) -> dict:
        return asdict(self)


@functools.cache
def _library() -> dict:
    return json.loads(LIBRARY_FILE.read_text(encoding="utf-8"))


def _library_size_label(size: str) -> str:
    if "/" in size or float(size) < 250:
        return f"{size} AWG"
    return f"{size} kcmil"


def cable_spec(cable_id: str) -> CableSpec:
    key, sep, size = str(cable_id).partition(":")
    series = _library()["series"].get(key) if sep else None
    if series is None:
        raise ValueError(f"Unknown cable_id {cable_id!r}; use '<series>:<size>', e.g. 'southwire_dlo_2000v:444.4'")
    row = next((r for r in series["rows"] if r["id"] == size), None)
    if row is None:
        raise ValueError(f"cable_id {cable_id!r}: size {size!r} is not in series {key!r}")
    meta = _library()["_meta"]["sources"][row["source"]]
    area = float(row["area_cmil"])
    if row.get("conductor_diameter_in"):
        d_mm, d_src = float(row["conductor_diameter_in"]) * 25.4, "printed"
    else:
        d_mm, d_src = math.sqrt(area) / 1000 * DLO_DIAMETER_RATIO * 25.4, "proxy"
    rdc = row.get("dc_resistance_ohm_per_kft")
    basis = row.get("ampacity_basis") or meta.get("ampacity_basis", {}).get("free_air", "NOT STATED")
    flags = tuple(row.get("flags", [])) + (() if d_src == "printed" else ("DIAMETER_PROXY",))
    return CableSpec(
        cable_id=f"{key}:{row['id']}", manufacturer=series["manufacturer"], series=series["series"],
        size=row["size"], size_label=_library_size_label(row["size"]),
        area_cmil=area, od_mm=float(row["nominal_od_mm"]), insulation_mm=float(row["insulation_mm"]),
        diameter_mm=d_mm, diameter_source=d_src,
        rdc_ref=None if rdc is None else (float(rdc["value"]), float(rdc["temp_c"])),
        rated_voltage_v=float(series["voltage_v"]), temp_c=int(series["temp_c"]),
        ampacity_free_air_a=float(row["ampacity_free_air_90c_30c_a"]),
        ampacity_ref_ambient_c=float(row["ampacity_ref_ambient_c"]), ampacity_basis=basis,
        basis_stated="NOT STATED" not in basis, standard_nec_size=bool(row["standard_nec_size"]),
        listed_rhh=bool(row.get("listing_rhh_rhw")), status=row["status"],
        source_name=meta["title"], source_url=meta["url"], source_date=meta["date"], flags=flags)


def library_entries() -> list[dict]:
    """Every library row as a dict (for the UI select and the calc package)."""
    out = []
    for key, series in _library()["series"].items():
        for r in series["rows"]:
            out.append(cable_spec(f"{key}:{r['id']}").as_dict())
    return out


def resolve_cable(inp: CableBusInput) -> CableSpec | None:
    if inp.cable_type not in CABLE_TYPES:
        raise ValueError(f"cable_type must be one of {', '.join(CABLE_TYPES)}")
    if inp.cable_type != "dlo_2000v":
        if inp.cable_id:
            raise ValueError("cable_id is only used with cable_type 'dlo_2000v'")
        return None
    if not inp.cable_id:
        raise ValueError("cable_type 'dlo_2000v' needs cable_id (see library_entries())")
    return cable_spec(inp.cable_id)


def _check_library(inp: CableBusInput, spec: CableSpec) -> None:
    if inp.material != "Cu":
        raise ValueError(f"{spec.cable_id} is tinned copper: set material 'Cu'")
    if inp.voltage_v > spec.rated_voltage_v:
        raise ValueError(f"{spec.cable_id} is rated {spec.rated_voltage_v:.0f} V; voltage_v {inp.voltage_v:.0f} is "
                         "above the cable rating")
    if inp.insulation_temp_c != spec.temp_c:
        raise ValueError(f"{spec.cable_id} is rated {spec.temp_c} C: set insulation_temp_c to {spec.temp_c}")
    if inp.insulation_mm is not None:
        raise ValueError("insulation_mm is not used with a library cable (its insulation comes from the data file)")


def _library_rdc_ohm_per_m(spec: CableSpec, temp_c: float) -> float:
    if spec.rdc_ref is None:
        return cond.rdc_from_area_ohm_per_m(spec.area_cmil, "Cu", temp_c, DLO_STRANDING_FACTOR)
    r_ref, t_ref = spec.rdc_ref
    return cond.rdc_datasheet_ohm_per_m(r_ref, t_ref, "Cu", temp_c)


def _library_method(inp: CableBusInput, spec: CableSpec) -> str:
    m = inp.ampacity_method
    if m == "calculated":
        raise ValueError("The calculated method is not available for library cables: use 'table' (standard NEC "
                         "sizes listed RHH/RHW) or 'datasheet'")
    if m not in ("auto", "table", "datasheet"):
        raise ValueError("ampacity_method must be auto, table or datasheet for library cables")
    table_ok = spec.standard_nec_size and spec.listed_rhh
    if m == "auto":
        return "table" if table_ok else "datasheet"
    if m == "table" and not table_ok:
        raise ValueError(f"{spec.size_label} has no code-table basis (non-standard NEC size or not listed "
                         "RHH/RHW): use 'datasheet'")
    return m


def _library_ampacity(inp: CableBusInput, spec: CableSpec) -> tuple[float, str]:
    if inp.cable_ampacity_a:   # user-supplied rating overrides the printed value
        base, ref, src = inp.cable_ampacity_a, inp.cable_ampacity_ambient_c, "Supplied rating"
    else:
        base, ref, src = spec.ampacity_free_air_a, spec.ampacity_ref_ambient_c, f"{spec.manufacturer} printed rating"
    f = ambient_factor_checked(inp.ambient_c, spec.temp_c, ref)
    return base * f, (f"{src} {base:.0f} A at {ref:.0f} C ({spec.temp_c} C conductor, basis: {spec.ampacity_basis}) "
                      f"x ambient factor {f:.3f} ({inp.ambient_c:.0f} C)")


def _library_notes(inp: CableBusInput, spec: CableSpec, method: str) -> list[str]:
    out = [f"Library cable {spec.cable_id}: {spec.manufacturer}, {spec.series}; {spec.size_label} "
           f"{spec.area_cmil:,.0f} cmil; data status {spec.status} ({spec.source_name}; {spec.source_date}). "
           f"Rated {spec.rated_voltage_v:.0f} V, {spec.temp_c} C."]
    if spec.rdc_ref is None:
        out.append(f"DC resistance: no printed value for this cable; calculated from {spec.area_cmil:,.0f} cmil, "
                   f"annealed copper, stranding factor {DLO_STRANDING_FACTOR} (UNVERIFIED for Class I stranding; "
                   "tinned-copper resistivity not applied).")
    else:
        out.append(f"DC resistance: printed {spec.rdc_ref[0]} ohm per 1000 ft at {spec.rdc_ref[1]:.0f} C, corrected "
                   f"to {inp.insulation_temp_c} C.")
    if spec.diameter_source == "proxy":
        out.append(f"Conductor diameter not printed for this size: estimated {spec.diameter_mm:.2f} mm "
                   "(sqrt(area) x 1.173, UNVERIFIED); used for GMR and skin effect only.")
    if method == "table":
        out.append(f"Ampacity basis: {inp.code} free-air table (90 C column), used because the size is a standard "
                   "NEC size and the cable is listed RHH/RHW.")
    else:
        out.append(f"Ampacity basis: manufacturer free-air rating ({spec.ampacity_basis}), corrected from "
                   f"{spec.ampacity_ref_ambient_c:.0f} C to {inp.ambient_c:.0f} C with the NEC 310.15(B)(1) "
                   "ambient equation. Used because the size is non-standard or not listed RHH/RHW.")
    if not spec.basis_stated:
        out.append("WARNING: the maker does not state the ampacity basis for this row. The 30 C free-air basis is "
                   "an assumption (UNVERIFIED); confirm with the manufacturer before using this rating.")
    out.append("Termination: fine-stranded (Class I/K) conductors need lugs or connectors listed for that stranding "
               "and this cable (NEC 110.14 / UL 486A-B, as attributed; UNVERIFIED here). Check the equipment "
               "listing and the lug catalogue. The termination check applies to the table basis only.")
    return out


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


def build_layout(inp: CableBusInput, pattern: str, od: float, spec: CableSpec | None = None) -> list[Conductor]:
    rows = _check_pattern(pattern, inp.conductors_per_phase, inp.tiers)
    pitch = inp.spacing_mm or 2 * od
    tier_pitch = inp.tier_spacing_mm or pitch
    if spec is None:
        r_core = cond.rac_ohm_per_m(inp.size, inp.material, inp.insulation_temp_c, inp.frequency_hz,
                                    spacing_mm=pitch)
        gmr = cond.gmr_mm(inp.size)
    else:
        r_core = cond.rac_from_rdc_ohm_per_m(_library_rdc_ohm_per_m(spec, inp.insulation_temp_c), spec.diameter_mm,
                                             inp.frequency_hz, spacing_mm=pitch)
        gmr = cond.gmr_from_diameter_mm(spec.diameter_mm)
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


def resolve_method(inp: CableBusInput, spec: CableSpec | None = None) -> str:
    if spec is not None:
        return _library_method(inp, spec)
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


def per_cable_ampacity(inp: CableBusInput, spec: CableSpec | None = None) -> tuple[float, str]:
    if resolve_method(inp, spec) == "datasheet":
        if spec is not None:
            return _library_ampacity(inp, spec)
        if not inp.cable_ampacity_a:
            raise ValueError("ampacity_method 'datasheet' needs cable_ampacity_a")
        f = ambient_factor_checked(inp.ambient_c, inp.insulation_temp_c, inp.cable_ampacity_ambient_c)
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
    f = ambient_factor_checked(inp.ambient_c, inp.insulation_temp_c, rated)
    return base * f, (f"{inp.code} {info.table_name} {base:.0f} A ({inp.insulation_temp_c} C column, "
                      f"data {info.status}) x ambient factor {f:.3f} ({inp.ambient_c:.0f} C)")


def _load_rated_ambient(code: str) -> float:
    return float(json.loads((amp.DATA / f"ampacity_{code.lower()}.json").read_text())["_meta"]["rated_ambient_c"])


def datasheet_shield_derating(lambda1_actual: float, lambda1_ref: float = 0.0) -> float:
    """Factor applied to a datasheet ampacity for shield circulating-current loss.

    Method: IEC 60287-1-1 section 2.3 (sheath/screen loss factor lambda1) applied
    through the steady-state rating equation of IEC 60287-1-1 section 1.4.1.1,
    which is the same heat balance as Neher-McGrath (AIEE 1957, "ycs" shield
    loss term):

        I = sqrt[(dtheta - Wd(...)) / (R T1 + n R (1 + lambda1) T2
                                        + n R (1 + lambda1 + lambda2)(T3 + T4))]

    For an unarmoured cable in air (lambda2 = 0, T2 = 0) with the external
    thermal resistance T3 + T4 dominant, I is proportional to
    1 / sqrt(1 + lambda1), so a rating made with loss factor lambda1_ref
    becomes, with the actual loss factor lambda1_actual:

        I_derated = I_datasheet * sqrt((1 + lambda1_ref) / (1 + lambda1_actual))

    Assumptions:
    - lambda1_actual is the circulating-current loss factor from the sharing
      solve (shield loss / core loss for the same cable); eddy loss lambda1''
      is neglected, as it is in IEC 60287 for both-ends-bonded single-core
      cables except large segmental conductors.
    - Neglecting T1 (insulation) and the dielectric loss term overstates the
      reduction slightly, so the factor is conservative.
    - The factor is capped at 1: a datasheet rating is never raised.
    - lambda1_ref is the loss factor the datasheet already assumes: 0 for
      single-point or cross-bonded ratings (the usual basis), unless the
      manufacturer states otherwise.
    [Equation form from memory; verify clause numbers against IEC 60287-1-1:2006.]
    """
    if lambda1_actual < 0 or lambda1_ref < 0:
        raise ValueError("Shield loss factors lambda1 must be >= 0")
    return min(1.0, math.sqrt((1 + lambda1_ref) / (1 + lambda1_actual)))


def phase_voltage_drops(res, voltage_v: float, power_factor: float, length_m: float,
                        lagging: bool = True) -> dict[str, tuple[float, float]]:
    """Voltage drop per phase, in % of that phase's own sending-end voltage.

    Each phase group p carries I_p at power factor pf, so its sending-end
    voltage is V_s,p = (V_LL / sqrt 3) at angle (arg I_p + phi), phi = acos(pf)
    (current lagging). The drop phasor dV_p = (group drop per m) x length comes
    from the sharing solve, which includes mutual coupling, unequal sharing and
    induced shield / enclosure currents. Per phase:

        exact  = (|V_s,p| - |V_s,p - dV_p|) / |V_s,p| x 100
        approx = Re(dV_p . conj(V_s,p)) / |V_s,p|^2 x 100

    The approximate form is the projection of the drop onto the source voltage,
    i.e. the usual I (R cos phi + X sin phi) L estimate (IEEE Std 141 /
    NEC Chapter 9 Table 9 Note 2 form) [from memory]. Measuring every phase
    against its own source voltage makes the result independent of how the
    phases are labelled.

    Returns {phase: (exact %, approx %)}.
    """
    v_ph = voltage_v / math.sqrt(3)
    phi = math.acos(max(-1.0, min(1.0, power_factor))) * (1 if lagging else -1)
    out = {}
    for p, d in res.group_drop_v_per_m.items():
        i_p = res.groups[p].current
        if not i_p:
            continue
        vs = cmath.rect(v_ph, cmath.phase(i_p) + phi)
        dv = d * length_m
        exact = (abs(vs) - abs(vs - dv)) / abs(vs) * 100
        approx = (dv * vs.conjugate()).real / abs(vs) ** 2 * 100
        out[p] = (exact, approx)
    return out



# --- shield standing voltage and bonding comparison --------------------------

SHEATH_LIMIT_NOTE = ("No verified public limit is loaded: a secondary source attributes ~25 V at normal load to "
                     "IEEE 575 practice (LOW confidence, clause not found), so it is not used as a default. Set the "
                     "utility / owner limit (shield_voltage_limit_v) to get a pass/fail.")
_SP_KEYS = ("e_v_per_km", "standing_v", "standing_v_fault", "worst_shield", "max_section_m_for_limit", "passed",
            "shields")


def shield_standing_voltages(cs: list[Conductor], currents: list[complex], shield_radius_mm: float,
                             freq: float) -> list[tuple[int, complex]]:
    """Induced voltage per metre on each open (single-point bonded) phase-cable shield.

    One current-free probe per phase conductor, concentric with it at the shield mean
    radius. E_i = sum_k z(shield_i, k) I_k over every current-carrying conductor (cores
    and, if modelled, enclosure filaments), using the impedance module's Carson mutual
    impedances (impedance.open_circuit_voltages). Returns [(core index, E in V/m)].
    """
    cores = [i for i, c in enumerate(cs) if c.group in PHASES]
    probes = [Conductor(cs[i].x_mm, cs[i].y_mm, "SHIELD", 0.0, shield_radius_mm, f"S-{cs[i].label}",
                        tube_radius_mm=shield_radius_mm) for i in cores]
    return list(zip(cores, open_circuit_voltages(cs, currents, probes, freq)))


def _shield_radius_mm(inp: CableBusInput, cons) -> float | None:
    d = inp.shield_mean_diameter_mm or (cons.shield_mean_diameter_mm if cons is not None and cons.shield_mm else None)
    return d / 2 if d else None


def _standing(inp: CableBusInput, cs, res, radius: float, section_m: float) -> dict:
    """Open-end standing voltage over one bonded section: normal load and balanced through-fault."""
    k_fault = inp.fault_ka * 1000 / inp.current_a if inp.fault_ka else None
    shields, mags = [], []
    for i, e in shield_standing_voltages(cs, res.currents, radius, inp.frequency_hz):
        v = abs(e) * section_m
        mags.append(abs(e))
        shields.append({"label": f"S-{cs[i].label}", "phase": cs[i].group, "x_mm": round(cs[i].x_mm, 1),
                        "y_mm": round(cs[i].y_mm, 1), "e_v_per_km": round(abs(e) * 1000, 3),
                        "standing_v": round(v, 2),
                        "standing_v_fault": None if k_fault is None else round(v * k_fault, 2)})
    e_max = max(mags)
    # First shield within 1e-9 of the maximum, so mirror-image ties resolve the same way in every port.
    worst = next(s for s, m in zip(shields, mags) if m >= e_max * (1 - 1e-9))
    v_max = e_max * section_m
    lim = inp.shield_voltage_limit_v
    return {"e_v_per_km": round(e_max * 1000, 3), "standing_v": round(v_max, 2),
            "standing_v_fault": None if k_fault is None else round(v_max * k_fault, 2),
            "worst_shield": worst["label"],
            "max_section_m_for_limit": None if lim is None else round(lim / e_max, 1),
            "passed": None if lim is None else bool(v_max <= lim), "shields": shields}


def _mode_summary(rows: list[ConductorRow], shield_i: float, shield_loss: float, lam_max: float,
                  sp: dict | None) -> dict:
    return {"shield_current_a": round(shield_i, 1), "shield_loss_w": round(shield_loss, 1),
            "max_lambda1": round(lam_max, 4), "min_ampacity_a": min(r.ampacity_a for r in rows),
            "max_loading_pct": max(r.loading_pct for r in rows),
            "standing_v": sp["standing_v"] if sp else None,
            "standing_v_fault": sp["standing_v_fault"] if sp else None}


def _recommendation(sh: dict, inp: CableBusInput) -> str:
    sp, be = sh["modes"]["single_point"], sh["modes"]["both_ends"]
    if sh["standing_v"] is None:
        return ("Single-point standing voltage not computed (give the shield mean diameter or the cable "
                "construction with a shield thickness). Cross-bonding is not modelled.")
    txt = (f"Single-point bonding: {sh['standing_v']:.1f} V at the open end of a {sh['section_length_m']:g} m "
           "bonded section at normal load")
    if sh["standing_v_fault"] is not None:
        txt += f" ({sh['standing_v_fault']:.0f} V during a {inp.fault_ka:g} kA balanced through-fault)"
    txt += ", no circulating loss."
    if be:
        txt += (f" Both-ends bonding: {be['shield_current_a']:.0f} A circulating, "
                f"{be['shield_loss_w'] / 1000:.2f} kW shield loss, worst lambda1 {be['max_lambda1']:.3f}, "
                f"lowest cable ampacity {sp['min_ampacity_a']:.0f} -> {be['min_ampacity_a']:.0f} A, "
                f"worst loading {sp['max_loading_pct']:.1f} -> {be['max_loading_pct']:.1f} %.")
    lim = sh["voltage_limit_v"]
    if lim is None:
        txt += " Set your utility / owner standing-voltage limit to get a pass/fail and a recommendation."
    elif sh["passed"]:
        txt += (f" Within the {lim:g} V limit, so single-point bonding is favoured (no circulating loss or ampacity "
                "derating); confirm the jacket and sheath voltage limiter (SVL) ratings against the fault voltage.")
    else:
        txt += (f" Exceeds the {lim:g} V limit: shorten the bonded section to <= {sh['max_section_m_for_limit']:g} m "
                "(minor sections or mid-point bonding), or accept both-ends bonding with its loss and derating, "
                "or use cross-bonding.")
    return txt + " Cross-bonding is not modelled."


def sheath_study(inp: CableBusInput, cons, cs, res, pattern: str, rows: list[ConductorRow], shield_i: float,
                 shield_loss: float, lam_max: float, compare_bonding: bool) -> dict:
    """Shield standing voltage (single-point bonding) and comparison with both-ends bonding.

    Standing voltage: each shield open at one end of a bonded section,
    E_i = |sum_k z(shield_i, k) I_k| (V/m) with the impedance module's mutual impedances,
    V = E x section length. Through-fault: currents scaled by fault_ka / current_a
    (balanced three-phase fault shared like load current). With compare_bonding the other
    bonding mode is solved for the same phase pattern.
    """
    section = inp.shield_section_length_m or inp.length_m
    mode = inp.shield_bonding
    other = "both_ends" if mode == "single_point" else "single_point"
    notes: list[str] = []
    alt = None
    if compare_bonding:
        try:
            alt = analyse(replace(inp, shield_bonding=other, pattern=pattern), compare_bonding=False)
        except ValueError as e:
            notes.append(f"{other.replace('_', '-')} bonding not compared: {e}")
    sp = None
    if mode == "single_point":
        radius = _shield_radius_mm(inp, cons)
        if radius:
            sp = _standing(inp, cs, res, radius, section)
        else:
            notes.append("Standing voltage needs the shield mean diameter (shield_mean_diameter_mm) or the cable "
                         "construction with a shield thickness.")
    elif alt is not None and alt.sheath["standing_v"] is not None:
        sp = {k: alt.sheath[k] for k in _SP_KEYS}
    modes = {"single_point": None, "both_ends": None}
    modes[mode] = _mode_summary(rows, shield_i, shield_loss, lam_max, sp if mode == "single_point" else None)
    if alt is not None:
        modes[other] = alt.sheath["modes"][other]
    lim = inp.shield_voltage_limit_v
    sh = {"bonding": mode, "section_length_m": section, "sections": math.ceil(inp.length_m / section - 1e-9),
          "voltage_limit_v": lim, "fault_ka": inp.fault_ka}
    sh.update({k: (sp[k] if sp else ([] if k == "shields" else None)) for k in _SP_KEYS})
    sh["modes"] = modes
    if lim is None:
        notes.append(SHEATH_LIMIT_NOTE)
    notes.append("Through-fault voltage assumes a balanced three-phase fault shared like load current; a "
                 "single-line-to-ground fault (earth / shield return) can give much higher shield voltages and is "
                 "not modelled. Compare the fault value with the jacket and sheath voltage limiter (SVL) ratings.")
    notes.append("Cross-bonding (three equal minor sections with transpositions) is not modelled.")
    sh["recommendation"] = _recommendation(sh, inp)
    sh["notes"] = notes
    return sh


# --- main -------------------------------------------------------------------

def analyse(inp: CableBusInput, compare_bonding: bool = True) -> CableBusResult:
    """Check a cable bus. With shielded cable, compare_bonding also solves the other bonding mode
    (single-point vs both-ends) for the sheath comparison; the designer turns it off for speed."""
    validate_input(inp)
    if inp.shield_section_length_m is not None and not 0 < inp.shield_section_length_m <= inp.length_m:
        raise ValueError("shield_section_length_m must be > 0 and no longer than length_m")
    if inp.shield_voltage_limit_v is not None and not inp.shield_voltage_limit_v > 0:
        raise ValueError("shield_voltage_limit_v must be > 0")
    if inp.fault_clearing_s is not None:
        validate.clearing_time("fault_clearing_s", inp.fault_clearing_s)
    if inp.ground_fault_ka is not None:
        validate.positive("ground_fault_ka", inp.ground_fault_ka, "kA")
    if inp.ground_fault_ka is not None and inp.shield_sc_limit_c <= inp.shield_temp_c:
        raise ValueError(f"shield_sc_limit_c ({inp.shield_sc_limit_c:g} C) must exceed shield_temp_c "
                         f"({inp.shield_temp_c:g} C)")
    spec = resolve_cable(inp)
    if spec is None:
        size = cond.normalize_size(inp.size)
    else:
        _check_library(inp, spec)
        size = spec.size
    inp.size = size
    notes: list[str] = []
    if inp.terminal_temp_c is None:
        inp.terminal_temp_c, term_basis = default_terminal_temp_c(inp.voltage_v)
        notes.append(term_basis)
    cons = None if spec else construction(inp)
    if inp.cable_od_mm is not None:
        bare = spec.diameter_mm if spec else cond.diameter_mm(size)
        if not inp.cable_od_mm > bare:
            raise ValueError(f"cable_od_mm ({inp.cable_od_mm:g} mm) must be greater than the conductor bare "
                             f"diameter ({bare:.2f} mm)")
    od = (inp.cable_od_mm or (spec.od_mm if spec else None) or (cons.de_mm if cons else None)
          or (cond.cable_od_mm(size) if inp.voltage_v <= 2000 else None))
    if od is None:
        raise ValueError("Above 2000 V give cable_od_mm or the cable construction (insulation_mm, shield_mm, jacket_mm)")
    if not inp.cable_od_mm and spec is None and cons is None and inp.voltage_v > 600:
        notes.append(f"Cable OD {od:.1f} mm is estimated from a 600 V insulation wall, but voltage_v is "
                     f"{inp.voltage_v:g} V: enter cable_od_mm for the real cable (the insulation wall, spacing and "
                     "enclosure depend on it).")
    with_shields = inp.shield_bonding == "both_ends"
    if with_shields and cons and cons.shield_mm:
        inp.shield_mean_diameter_mm = inp.shield_mean_diameter_mm or cons.shield_mean_diameter_mm
        inp.shield_area_mm2 = inp.shield_area_mm2 or math.pi * cons.shield_mean_diameter_mm * cons.shield_mm
    method = resolve_method(inp, spec)
    if spec:
        notes += _library_notes(inp, spec, method)
    size_text = spec.size_label if spec else cond.size_label(size)

    patterns = (candidate_patterns(inp.conductors_per_phase, inp.tiers) if inp.pattern == "auto"
                else [inp.pattern.upper()])
    scored = []
    for p in patterns:
        cs = build_layout(inp, p, od, spec)
        res = solve_sharing(cs, _groups(inp, with_shields), inp.frequency_hz)
        phase_idx = [i for i, c in enumerate(cs) if c.group in PHASES]
        scored.append((p, cs, res, max(res.share_pct(i) for i in phase_idx), sum(res.losses_w_per_m)))
    scored.sort(key=lambda s: (round(s[3], 1), s[4]))
    pattern, cs, res, _, _ = scored[0]
    compared = [PatternScore(p, round(m, 1), round(l, 2)) for p, _, _, m, l in scored]

    pitch = inp.spacing_mm or 2 * od
    labels = {c.label: i for i, c in enumerate(cs)}

    def shield_lambda1(i: int) -> float:
        # Circulating-current shield loss factor of cable i (0 without both-ends bonding).
        core_loss = res.losses_w_per_m[i]
        s = labels.get(f"S-{cs[i].label}")
        return round(res.losses_w_per_m[s] / core_loss, 4) if s is not None and core_loss else 0.0

    a_term = None
    if method == "calculated":
        if cons is None:
            raise ValueError("The calculated ampacity method needs the cable construction (insulation_mm etc.)")
        require_ambient_below(inp.ambient_c, inp.insulation_temp_c)
        installation = "isolated" if pitch - od >= 0.75 * od else "flat_touching"
        cache: dict[float, object] = {}

        def ampacity_for(i: int):
            lam = shield_lambda1(i)
            if lam not in cache:
                cache[lam] = free_air_ampacity(cons, inp.ambient_c, installation, lam, inp.frequency_hz, pitch)
            return cache[lam]
        notes.append("Calculated ampacity (IEC 60287 / Neher-McGrath thermal model) is permitted by NEC 310.14(B) / "
                     "315.60(B) under engineering supervision; model constants are UNVERIFIED pending check against "
                     "IEC 60287. Each cable's own shield loss factor (lambda1) from the sharing solve is included.")
    else:
        a_cable, basis_fixed = per_cable_ampacity(inp, spec)
    # Termination limit, whatever the ampacity method (NEC 110.14(C), Table 310.16).
    a_term, term_table, why = termination_ampacity(inp, size, inp.terminal_temp_c)
    if a_term is None:
        notes.append(f"Termination temperature not checked: {why}.")

    derate_ds = method == "datasheet" and with_shields
    ds_factors = []
    rows = []
    worst = None
    for i, c in enumerate(cs):
        if c.group not in PHASES:
            continue
        cur = abs(res.currents[i])
        if method == "calculated":
            ar = ampacity_for(i)
            a_i, basis_i = ar.ampacity_a, ar.summary()
        elif derate_ds:
            lam = shield_lambda1(i)
            k = datasheet_shield_derating(lam, inp.cable_ampacity_lambda1_ref)
            ds_factors.append((k, lam))
            a_i = a_cable * k
            basis_i = (f"{basis_fixed} x shield derating {k:.3f} (lambda1 {lam:.3f} vs datasheet "
                       f"{inp.cable_ampacity_lambda1_ref:.3f}, IEC 60287-1-1 2.3)")
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

    # Voltage drop: each phase against its own sending-end voltage; the worst phase is checked.
    vd_by_phase = phase_voltage_drops(res, inp.voltage_v, inp.power_factor, inp.length_m)
    vd_phase = max(vd_by_phase, key=lambda p: vd_by_phase[p][0])
    vd_pct = vd_by_phase[vd_phase][0]
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
    if inp.conductors_per_phase > 1 and spec is not None:
        check("Minimum size for paralleled conductors", clauses["parallel"], spec.area_cmil,
              cond.AREA_CMIL[min_size], "cmil", spec.area_cmil >= cond.AREA_CMIL[min_size],
              f"min {cond.size_label(min_size)} (area comparison for {spec.size_label})")
    elif inp.conductors_per_phase > 1:
        check("Minimum size for paralleled conductors", clauses["parallel"], cond.size_index(size),
              cond.size_index(min_size), "size index", cond.size_index(size) >= cond.size_index(min_size),
              f"min {cond.size_label(min_size)}")
    if method == "table":
        check("Spacing for free-air ampacity basis (>= 1 cable diameter clearance)",
              "NEC 370.80 / CEC 12-2252 [UNVERIFIED]", pitch - od, od, "mm", pitch - od >= od - 1e-6)
        if inp.tiers > 1:
            tier_pitch = inp.tier_spacing_mm or pitch      # centre-to-centre, same convention as spacing_mm
            check("Tier spacing for free-air ampacity basis (>= 1 cable diameter clearance between tiers)",
                  "NEC 370.80 / CEC 12-2252 [UNVERIFIED]", tier_pitch - od, od, "mm",
                  tier_pitch - od >= od - 1e-6)
    w = worst[0]
    check("Most heavily loaded conductor within its ampacity", basis, w.current_a, w.ampacity_a, "A",
          w.current_a <= w.ampacity_a, f"{w.phase} at x={w.x_mm} mm; current sharing solved for pattern {pattern}")
    if a_term is not None:
        check("Most heavily loaded conductor within termination rating", clauses["terminal"], max_cur, a_term,
              "A", max_cur <= a_term,
              f"{inp.terminal_temp_c} C column of {amp.table_info(inp.code, term_table).table_name}, "
              "no ambient correction; 110.14(C)(2) permits separately installed pressure connectors at their "
              "listed rating: set terminal_temp_c to it if used")
    check("Voltage drop (worst phase)", clauses["vd"], vd_pct, inp.max_vd_pct, "%", vd_pct <= inp.max_vd_pct,
          f"phase {vd_phase}, each phase against its own sending-end voltage")

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
        if inp.fault_clearing_s:
            # ICEA P-32-382 adiabatic withstand of all paralleled conductors of one phase (equal fault sharing).
            area = (spec.area_cmil if spec else cond.AREA_CMIL[size]) * inp.conductors_per_phase
            withstand_ka = cond.adiabatic_withstand_a(inp.material, area, inp.insulation_temp_c,
                                                      inp.insulation_sc_limit_c, inp.fault_clearing_s) / 1000
            check("Conductor short-circuit withstand", "ICEA P-32-382", withstand_ka, inp.fault_ka, "kA",
                  withstand_ka >= inp.fault_ka,
                  f"{inp.conductors_per_phase} x {size_text} {inp.material} per phase, "
                  f"{inp.fault_clearing_s} s clearing, {inp.insulation_temp_c}->{inp.insulation_sc_limit_c} C, "
                  "equal fault sharing among paralleled conductors assumed")
        else:
            check("Conductor short-circuit withstand (NOT CHECKED: fault_clearing_s missing)", "ICEA P-32-382",
                  0.0, inp.fault_ka, "kA", False,
                  "fault_ka is given but fault_clearing_s is not, so the conductor withstand cannot be checked; "
                  "give fault_clearing_s")
            notes.append("Conductor short-circuit withstand not checked: give fault_clearing_s.")
        shield_area = inp.shield_area_mm2 or (math.pi * cons.shield_mean_diameter_mm * cons.shield_mm
                                              if cons is not None and cons.shield_mm else None)
        if inp.ground_fault_ka is not None and inp.fault_clearing_s and shield_area:
            # Copper shield, adiabatic (same ICEA form as the conductor); 1 mm2 = 1973.525 cmil.
            per_cable_ka = inp.ground_fault_ka / inp.conductors_per_phase
            sh_ka = cond.adiabatic_withstand_a("Cu", shield_area * 1973.525, inp.shield_temp_c,
                                               inp.shield_sc_limit_c, inp.fault_clearing_s) / 1000
            check("Shield short-circuit withstand", "ICEA P-32-382 (copper shield)", sh_ka, per_cable_ka, "kA",
                  sh_ka >= per_cable_ka,
                  f"{shield_area:.1f} mm2 Cu shield per cable, {inp.fault_clearing_s} s clearing, "
                  f"{inp.shield_temp_c}->{inp.shield_sc_limit_c} C; {inp.ground_fault_ka} kA ground fault shared "
                  f"equally by {inp.conductors_per_phase} cables of the faulted phase")
            notes.append("Not checked: mutual heating between stacked tiers.")
        else:
            why = ("give ground_fault_ka with the shield area" if inp.ground_fault_ka is None
                   else "needs fault_clearing_s and a shield area")
            notes.append(f"Not checked: shield short-circuit withstand ({why}); mutual heating between stacked tiers.")

    if with_shields:
        notes.append(f"Shields bonded both ends: max circulating current {shield_i:.0f} A, "
                     f"shield loss {shield_loss/1000:.2f} kW ({shield_loss / max(cond_loss, 1e-9) * 100:.1f} % of "
                     f"conductor loss). Single-point or cross bonding removes most of this.")
    if derate_ds:
        k_min, lam_max = min(ds_factors)
        notes.append(
            "Datasheet ampacity derated for shield circulating current (shields bonded both ends): "
            "I = I_datasheet x sqrt((1 + lambda1_ref) / (1 + lambda1)), IEC 60287-1-1 2.3 shield loss factor in "
            "the IEC 60287 / Neher-McGrath rating equation. Assumes the datasheet rating already includes "
            f"lambda1_ref = {inp.cable_ampacity_lambda1_ref:.3f} (0 = single-point or cross-bonded rating), "
            "external thermal resistance dominant, eddy loss and dielectric loss term neglected (conservative), "
            f"factor capped at 1. Per-cable lambda1 from the sharing solve; worst lambda1 {lam_max:.3f}, "
            f"factor {k_min:.3f} (range {k_min:.3f}-{max(f for f, _ in ds_factors):.3f}). [UNVERIFIED method "
            "simplification; check against the cable maker's both-ends-bonded rating where available.]")
        if k_min < 0.9:
            notes.append(f"WARNING: shield circulating current derates the datasheet ampacity by "
                         f"{(1 - k_min) * 100:.1f} % (> 10 %). Consider single-point or cross bonding, or a "
                         "manufacturer rating for both-ends bonding.")
    if inp.voltage_v > 2000 and inp.shield_bonding == "none":
        notes.append("MV cable selected with shield_bonding 'none': set 'single_point' or 'both_ends' to state the design.")
    notes.append("Voltage drop by phase, exact / approximate I(R cos phi + X sin phi) form, each against its own "
                 "sending-end phase voltage: " + ", ".join(f"{p} {e:.2f} / {a:.2f} %"
                                                          for p, (e, a) in sorted(vd_by_phase.items())) + ".")
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

    sheath = None
    if inp.shield_bonding in ("single_point", "both_ends"):
        lam_max = max(shield_lambda1(r.index) for r in rows)
        sheath = sheath_study(inp, cons, cs, res, pattern, rows, shield_i, shield_loss, lam_max, compare_bonding)
        if inp.shield_bonding == "single_point" and inp.shield_voltage_limit_v is None:
            notes.append("Shield standing voltage was not checked against a limit: shield_voltage_limit_v is not "
                         "set (single-point bonding), so there is no pass/fail on the open-end voltage.")
        if (inp.shield_bonding == "single_point" and inp.shield_voltage_limit_v is not None
                and sheath["standing_v"] is not None):
            check("Shield standing voltage at open end (single-point bonding, normal load)",
                  "Owner / utility limit (IEEE 575 practice) [user-set limit, UNVERIFIED]",
                  sheath["standing_v"], inp.shield_voltage_limit_v, "V", sheath["passed"],
                  f"{sheath['worst_shield']}: {sheath['e_v_per_km']:.1f} V/km x {sheath['section_length_m']:g} m "
                  "bonded section")

    width = max(r.x_mm for r in rows) + od
    height = max(r.y_mm for r in rows) + od
    return CableBusResult(inp, pattern, compared, round(width, 1), round(height, 1), rows, basis,
                          round(max_loading, 1), round(vd_pct, 3), round(cond_loss, 1), round(shield_loss, 1),
                          round(shield_i, 1), round(encl_loss, 1), round(encl_i, 1), field_ut,
                          None if f_nm is None else round(f_nm, 1),
                          None if f_lbf is None else round(f_lbf, 1), None if support is None else round(support, 1),
                          checks, notes, round(od, 2), round(pitch, 2), round(inp.tier_spacing_mm or pitch, 2),
                          sheath, None if spec is None else spec.as_dict())
