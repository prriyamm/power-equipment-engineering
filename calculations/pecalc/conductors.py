"""Conductor sizes, geometry, resistance and reactance.

DC resistance is computed from resistivity, stranding and temperature rather
than looked up, and the tests check it against NEC Chapter 9 Table 8. AC
resistance adds skin and proximity effect with the IEC 60287-1-1 formulas,
the same basis Neher-McGrath (IEEE 835) uses. Reactance comes from the
geometric-mean-distance formula, so it works for any spacing (cable bus).
"""

from __future__ import annotations

import math

SIZES = (
    "14", "12", "10", "8", "6", "4", "3", "2", "1",
    "1/0", "2/0", "3/0", "4/0",
    "250", "300", "350", "400", "500", "600", "700", "750", "800", "900",
    "1000", "1250", "1500", "1750", "2000",
)

# Conductor area in circular mils (AWG by definition, kcmil = 1000 cmil).
AREA_CMIL = {
    "14": 4110, "12": 6530, "10": 10380, "8": 16510, "6": 26240,
    "4": 41740, "3": 52620, "2": 66360, "1": 83690,
    "1/0": 105600, "2/0": 133100, "3/0": 167800, "4/0": 211600,
    **{s: int(s) * 1000 for s in SIZES[13:]},
}

# Bare Class B stranded conductor diameter, inches.
# Source: NEC Chapter 9 Table 8. [UNVERIFIED: entered from memory]
DIAMETER_IN = {
    "14": 0.073, "12": 0.092, "10": 0.116, "8": 0.146, "6": 0.184,
    "4": 0.232, "3": 0.260, "2": 0.292, "1": 0.332,
    "1/0": 0.372, "2/0": 0.418, "3/0": 0.470, "4/0": 0.528,
    "250": 0.575, "300": 0.630, "350": 0.681, "400": 0.728, "500": 0.813,
    "600": 0.893, "700": 0.964, "750": 0.998, "800": 1.030, "900": 1.094,
    "1000": 1.152, "1250": 1.289, "1500": 1.412, "1750": 1.526, "2000": 1.632,
}

# Typical 600 V XHHW-2 / RW90 insulation wall, inches, by size band.
# Used only when the caller gives no cable OD. [UNVERIFIED: typical values;
# use the manufacturer's datasheet OD for design work]
_INSULATION_IN = (
    (("14", "12", "10"), 0.030),
    (("8", "6", "4", "3", "2"), 0.045),
    (("1", "1/0", "2/0", "3/0", "4/0"), 0.055),
    (("250", "300", "350", "400", "500"), 0.065),
    (("600", "700", "750", "800", "900", "1000"), 0.080),
    (("1250", "1500", "1750", "2000"), 0.095),
)

# Resistivity at 20 C in ohm-cmil/ft and the inferred zero-resistance
# temperature used for temperature correction.
MATERIALS = {
    "Cu": {"rho20": 10.371, "t0": 234.5},  # annealed copper, 100 % IACS
    "Al": {"rho20": 16.946, "t0": 228.1},  # 1350 aluminum, 61.2 % IACS
}
STRANDING_FACTOR = 1.02  # lay-length increase for concentric stranding

MU0 = 4e-7 * math.pi
FT = 0.3048
INCH = 0.0254
CMIL_TO_MM2 = 5.067075e-4


def normalize_size(size: str | int) -> str:
    """Accept '500', '500 kcmil', '#2', '2 AWG', '4/0' and return the key."""
    s = str(size).strip().lower()
    for token in ("kcmil", "mcm", "awg", "#"):
        s = s.replace(token, "")
    s = s.strip()
    if s not in AREA_CMIL:
        raise ValueError(f"Unknown conductor size {size!r}; expected one of {', '.join(SIZES)}")
    return s


def size_label(size: str) -> str:
    size = normalize_size(size)
    return f"{size} kcmil" if SIZES.index(size) >= SIZES.index("250") else f"{size} AWG"


def size_index(size: str) -> int:
    return SIZES.index(normalize_size(size))


def area_mm2(size: str) -> float:
    return AREA_CMIL[normalize_size(size)] * CMIL_TO_MM2


def diameter_mm(size: str) -> float:
    return DIAMETER_IN[normalize_size(size)] * 25.4


def insulation_mm(size: str) -> float:
    size = normalize_size(size)
    for sizes, wall in _INSULATION_IN:
        if size in sizes:
            return wall * 25.4
    raise AssertionError(size)


def cable_od_mm(size: str) -> float:
    """Estimated single-conductor 600 V cable OD (conductor + insulation)."""
    return diameter_mm(size) + 2 * insulation_mm(size)


def rdc_ohm_per_m(size: str, material: str, temp_c: float = 75.0) -> float:
    m = MATERIALS[material]
    r20_per_ft = m["rho20"] / AREA_CMIL[normalize_size(size)] * STRANDING_FACTOR
    r_per_ft = r20_per_ft * (m["t0"] + temp_c) / (m["t0"] + 20.0)
    return r_per_ft / FT


def _f(x4: float) -> float:
    return x4 / (192.0 + 0.8 * x4)


def ac_factors(rdc: float, freq: float, d_mm: float, spacing_mm: float | None) -> tuple[float, float]:
    """Skin (ys) and proximity (yp) factors, IEC 60287-1-1 section 2.1.

    Uses ks = 1 and kp = 0.8 (round stranded conductor). spacing_mm is the
    centre-to-centre distance to the neighbouring phase; None skips yp.
    """
    xs4 = (8 * math.pi * freq * 1e-7 * 1.0 / rdc) ** 2
    ys = _f(xs4)
    yp = 0.0
    if spacing_mm:
        xp4 = (8 * math.pi * freq * 1e-7 * 0.8 / rdc) ** 2
        ratio2 = (d_mm / spacing_mm) ** 2
        fp = _f(xp4)
        yp = fp * ratio2 * (0.312 * ratio2 + 1.18 / (fp + 0.27))
    return ys, yp


def rac_ohm_per_m(size: str, material: str, temp_c: float = 75.0, freq: float = 60.0,
                  spacing_mm: float | None = None) -> float:
    rdc = rdc_ohm_per_m(size, material, temp_c)
    ys, yp = ac_factors(rdc, freq, diameter_mm(size), spacing_mm)
    return rdc * (1 + ys + yp)


# ICEA P-32-382 adiabatic constants: (K with A in cmil and I in A, T0 in C).
# [UNVERIFIED: K = 0.0297 Cu / 0.0125 Al with A in cmil, I in A; T0 = 234 Cu / 228 Al]
ADIABATIC = {"Cu": (0.0297, 234.0), "Al": (0.0125, 228.0)}


def adiabatic_withstand_a(material: str, area_cmil: float, initial_c: float, final_c: float,
                          time_s: float) -> float:
    """ICEA P-32-382 adiabatic short-circuit withstand current, A.

    (I/A)^2 t = K log10((T2 + T0) / (T1 + T0)), so
    I = A sqrt(K log10((T2 + T0) / (T1 + T0)) / t), A in cmil, t in s.
    [UNVERIFIED: K = 0.0297 Cu / 0.0125 Al with A in cmil, I in A; T0 = 234 Cu / 228 Al]
    """
    k, t0 = ADIABATIC["Cu"] if material == "Cu" else ADIABATIC["Al"]
    return area_cmil * math.sqrt(k * math.log10((final_c + t0) / (initial_c + t0)) / time_s)


def adiabatic_temperature_c(material: str, area_cmil: float, initial_c: float, i2t_a2s: float) -> float:
    """Conductor temperature after a fault with let-through energy i2t = integral of i^2 dt (A^2 s).

    Inverse of adiabatic_withstand_a with the same constants: (I/A)^2 t -> i2t / A^2, so
    T2 = (T1 + T0) 10^(i2t / (K A^2)) - T0.
    """
    k, t0 = ADIABATIC["Cu"] if material == "Cu" else ADIABATIC["Al"]
    return (initial_c + t0) * 10 ** (i2t_a2s / (k * area_cmil ** 2)) - t0


def gmr_mm(size: str) -> float:
    """Geometric mean radius, approximated as 0.7788 r (solid-round value)."""
    return 0.7788 * diameter_mm(size) / 2


def reactance_ohm_per_m(size: str, gmd_mm: float, freq: float = 60.0) -> float:
    """Positive-sequence series reactance for a transposed/symmetric group."""
    return 2 * math.pi * freq * (MU0 / (2 * math.pi)) * math.log(gmd_mm / gmr_mm(size))
