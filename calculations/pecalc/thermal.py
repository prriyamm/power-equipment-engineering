"""Calculated cable ampacity: IEC 60287 thermal model for cables in free air.

IEC 60287 and Neher-McGrath (IEEE 835 / NEC 310.14(B) and 315.60(B)
"engineering supervision") use the same steady-state thermal circuit:

    I = sqrt( (dT - Wd [0.5 T1 + T2 + T3 + T4])
              / (R T1 + R (1 + l1) T2 + R (1 + l1 + l2) (T3 + T4)) )

R: AC resistance at max conductor temperature (ohm/m); Wd: dielectric loss
(W/m); l1, l2: shield and armour loss factors; T1..T4: thermal resistances of
insulation, bedding, jacket and the surrounding air (K m/W). Single-core
cables (n = 1). T4 for cables in free air comes from IEC 60287-2-1 clause
2.2.1 with the surface-temperature iteration.

The shield loss factor l1 for bonded shields comes from the multi-conductor
impedance solver, so it reflects the actual layout and bonding.

[UNVERIFIED: constants below are from memory of IEC 60287-1-1 / -2-1 and must
be checked against the standard; results are validated against NEC free-air
tables in the tests]
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import conductors as cond
from . import validate

# Thermal resistivity K m/W (IEC 60287-2-1 Table 1).
THERMAL_RESISTIVITY = {"XLPE": 3.5, "EPR": 5.0, "PVC": 5.0, "PE": 3.5, "XHHW": 3.5, "RW90": 3.5}
# EPR depends on the cable's rated voltage: 3.5 K m/W up to and including 3 kV, 5.0 above.
# [UNVERIFIED: IEC 60287-2-1 Table 1 as reproduced in secondary sources; not checked against the standard]
EPR_LV_RESISTIVITY, EPR_LV_MAX_KV = 3.5, 3.0


def insulation_resistivity(insulation: str, rated_voltage_v: float) -> float:
    """Insulation thermal resistivity (K m/W); EPR switches at 3 kV rated voltage."""
    if insulation == "EPR" and rated_voltage_v <= EPR_LV_MAX_KV * 1000:
        return EPR_LV_RESISTIVITY
    return THERMAL_RESISTIVITY[insulation]
# Relative permittivity and loss tangent (IEC 60287-1-1 Table 3).
DIELECTRIC = {"XLPE": (2.5, 0.001), "EPR": (3.0, 0.005), "PVC": (8.0, 0.1), "XHHW": (2.5, 0.001),
              "RW90": (2.5, 0.001)}
# Free-air constants Z, E, g (IEC 60287-2-1 Table 2) for the installation.
AIR_CONSTANTS = {
    "isolated": (0.21, 3.94, 0.60),          # single cable, or cables spaced > 0.75 De apart
    "two_touching": (0.29, 2.35, 0.50),
    "trefoil_touching": (0.96, 1.25, 0.20),
    "flat_touching": (0.62, 1.95, 0.25),
}


@dataclass
class CableConstruction:
    size: str
    material: str = "Cu"
    insulation: str = "XLPE"
    insulation_mm: float = 1.65        # incl. conductor and insulation screens for MV
    shield_mm: float = 0.0             # metallic shield thickness (0: none)
    jacket_mm: float = 0.0
    jacket: str = "PVC"
    voltage_v: float = 600.0           # line-to-line, for dielectric loss
    max_temp_c: float = 90.0
    rated_voltage_v: float | None = None  # cable voltage rating; None: use voltage_v

    @property
    def dc_mm(self) -> float:
        return cond.diameter_mm(self.size)

    @property
    def di_mm(self) -> float:
        return self.dc_mm + 2 * self.insulation_mm

    @property
    def da_mm(self) -> float:
        return self.di_mm + 2 * self.shield_mm

    @property
    def de_mm(self) -> float:
        return self.da_mm + 2 * self.jacket_mm

    @property
    def shield_mean_diameter_mm(self) -> float:
        return self.di_mm + self.shield_mm


@dataclass
class AmpacityResult:
    ampacity_a: float
    r_ac_ohm_per_m: float
    wd_w_per_m: float
    t1: float
    t3: float
    t4: float
    lambda1: float
    surface_rise_c: float
    installation: str
    ambient_c: float

    def summary(self) -> str:
        return (f"IEC 60287 calculated {self.ampacity_a:.0f} A ({self.installation}, {self.ambient_c:.0f} C ambient; "
                f"T1 {self.t1:.3f}, T3 {self.t3:.3f}, T4 {self.t4:.3f} K.m/W, lambda1 {self.lambda1:.3f}) [UNVERIFIED]")


def dielectric_loss(c: CableConstruction, freq: float = 60.0) -> float:
    validate.voltage("voltage_v", c.voltage_v)
    eps, tan_d = DIELECTRIC.get(c.insulation, (2.5, 0.001))
    cap = eps / (18 * math.log(c.di_mm / c.dc_mm)) * 1e-9  # F/m
    u0 = c.voltage_v / math.sqrt(3)
    return 2 * math.pi * freq * cap * u0 ** 2 * tan_d


def free_air_ampacity(c: CableConstruction, ambient_c: float = 40.0, installation: str = "isolated",
                      lambda1: float = 0.0, freq: float = 60.0, spacing_mm: float | None = None) -> AmpacityResult:
    validate.voltage("voltage_v", c.voltage_v)
    rated_v = c.rated_voltage_v if c.rated_voltage_v is not None else c.voltage_v
    validate.voltage("rated_voltage_v", rated_v)
    rho_i = insulation_resistivity(c.insulation, rated_v)
    t1 = rho_i / (2 * math.pi) * math.log(1 + 2 * c.insulation_mm / c.dc_mm)
    t2 = 0.0
    t3 = (THERMAL_RESISTIVITY[c.jacket] / (2 * math.pi) * math.log(1 + 2 * c.jacket_mm / c.da_mm)
          if c.jacket_mm else 0.0)
    r = cond.rac_ohm_per_m(c.size, c.material, c.max_temp_c, freq, spacing_mm=spacing_mm)
    wd = dielectric_loss(c, freq)
    lambda2 = 0.0
    d_theta = c.max_temp_c - ambient_c
    if d_theta <= 0:
        return AmpacityResult(0.0, r, wd, t1, t3, float("inf"), lambda1, 0.0, installation, ambient_c)

    z, e, g = AIR_CONSTANTS[installation]
    de_m = c.de_mm / 1000
    h = z / de_m ** g + e
    k_a = math.pi * de_m * h / (1 + lambda1 + lambda2) * (t1 + t2 * (1 + lambda1) + t3 * (1 + lambda1 + lambda2))
    d_theta_d = wd * ((1 / (1 + lambda1 + lambda2) - 0.5) * t1 - t2 * lambda1 / (1 + lambda1 + lambda2))
    s = 2.0  # (surface rise)^(1/4) starting value
    for _ in range(200):
        nxt = ((d_theta + d_theta_d) / (1 + k_a * s)) ** 0.25
        if abs(nxt - s) < 1e-9:
            break
        s = nxt
    t4 = 1 / (math.pi * de_m * h * s)

    num = d_theta - wd * (0.5 * t1 + t2 + t3 + t4)
    den = r * t1 + r * (1 + lambda1) * t2 + r * (1 + lambda1 + lambda2) * (t3 + t4)
    amp = math.sqrt(max(num, 0) / den)
    return AmpacityResult(amp, r, wd, t1, t3, t4, lambda1, s ** 4, installation, ambient_c)
