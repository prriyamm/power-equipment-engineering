"""Magnetic flux density around long parallel conductors (2-D Biot-Savart).

For a straight filament carrying phasor current I at (xi, yi), the flux density
at (x, y) is B = mu0 I / (2 pi r^2) * (-dy, dx). Phasor components are summed
over all conductors (phases, shields, enclosure filaments) and the RMS
resultant sqrt(|Bx|^2 + |By|^2) is reported, the quantity a 3-axis meter reads
(IEEE 644 / IEEE 1308).

Exposure reference levels at 60 Hz:
- ICNIRP 1998: 83.3 uT general public, 416.7 uT occupational
  [VERIFIED from the ICNIRP 1998 guideline tables, f = 60 Hz]
- ICNIRP 2010: 200 uT public, 1000 uT occupational [UNVERIFIED]
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .impedance import Conductor

MU0_2PI = 2e-7

LIMITS_UT = {
    "ICNIRP 1998 public": 83.3,
    "ICNIRP 1998 occupational": 416.7,
    "ICNIRP 2010 public [UNVERIFIED]": 200.0,
    "ICNIRP 2010 occupational [UNVERIFIED]": 1000.0,
}


@dataclass
class FieldPoint:
    x_mm: float
    y_mm: float
    b_ut: float


def b_rms_ut(conductors: list[Conductor], currents: list[complex], x_mm: float, y_mm: float) -> float:
    bx = by = 0j
    for c, i in zip(conductors, currents):
        dx = (x_mm - c.x_mm) / 1000
        dy = (y_mm - c.y_mm) / 1000
        r2 = dx * dx + dy * dy
        if r2 < 1e-12:
            continue
        k = MU0_2PI * i / r2
        bx += -k * dy
        by += k * dx
    return math.sqrt(abs(bx) ** 2 + abs(by) ** 2) * 1e6


def profile(conductors: list[Conductor], currents: list[complex], y_mm: float,
            x_from_mm: float, x_to_mm: float, steps: int = 41) -> list[FieldPoint]:
    out = []
    for k in range(steps):
        x = x_from_mm + (x_to_mm - x_from_mm) * k / (steps - 1)
        out.append(FieldPoint(round(x, 1), y_mm, round(b_rms_ut(conductors, currents, x, y_mm), 2)))
    return out


def far_field_flat_ut(i_rms: float, spacing_m: float, distance_m: float) -> float:
    """Closed form for a balanced flat 3-phase circuit at large distance:
    B ~ (mu0 I / 2 pi) sqrt(3) s / d^2."""
    return MU0_2PI * i_rms * math.sqrt(3) * spacing_m / distance_m ** 2 * 1e6
