"""Multi-conductor series impedance and current sharing.

Any 2-D arrangement of parallel straight conductors (cable bus, busbars,
transformer leads, cable in tray) is modelled with Carson's simplified
earth-return impedances:

    z_ii = R_i + pi^2 f 1e-7 + j w 2e-7 ln(De / GMR_i)      ohm/m
    z_ij =       pi^2 f 1e-7 + j w 2e-7 ln(De / d_ij)

    De = 658.5 sqrt(rho / f)  (equivalent earth-return depth, m)

When the phase currents sum to zero the earth terms cancel, so balanced
results do not depend on soil resistivity. Each conductor belongs to a group:

- "phase" groups: conductors paralleled at both ends; the group total
  current is given, every member has the same voltage drop (unknown).
- "bonded" groups: metallic shields or sheaths bonded to ground at both ends;
  voltage drop is zero, currents are induced (circulating).

Solving gives each conductor's current phasor, each phase group's voltage
drop, and the losses. Reference: Carson (1926); Anderson, "Analysis of Faulted
Power Systems", ch. 4; IEC 60287-1-1 section 2.3 for sheath circulating loss.
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass, field

MU0_2PI = 2e-7


@dataclass
class Conductor:
    x_mm: float
    y_mm: float
    group: str           # phase name ("A", "B", "C", "N") or bonded group name
    r_ohm_per_m: float   # AC resistance at operating temperature
    gmr_mm: float
    label: str = ""
    tube_radius_mm: float | None = None  # set for concentric shields/sheaths


@dataclass
class Group:
    name: str
    kind: str                      # "phase" or "bonded"
    current: complex = 0j          # total current for phase groups


@dataclass
class SharingResult:
    currents: list[complex]
    group_drop_v_per_m: dict[str, complex]
    losses_w_per_m: list[float]
    conductors: list[Conductor]
    groups: dict[str, Group]

    def group_members(self, name: str) -> list[int]:
        return [i for i, c in enumerate(self.conductors) if c.group == name]

    def share_pct(self, i: int) -> float:
        """Conductor current as % of an equal share of its phase group."""
        c = self.conductors[i]
        g = self.groups[c.group]
        members = self.group_members(c.group)
        if g.kind != "phase" or not g.current:
            return float("nan")
        return abs(self.currents[i]) / (abs(g.current) / len(members)) * 100

    def group_loss_w_per_m(self, kind: str) -> float:
        return sum(p for p, c in zip(self.losses_w_per_m, self.conductors)
                   if self.groups[c.group].kind == kind)


def earth_depth_m(freq: float, soil_ohm_m: float = 100.0) -> float:
    return 658.5 * math.sqrt(soil_ohm_m / freq)


def impedance_matrix(conductors: list[Conductor], freq: float = 60.0,
                     soil_ohm_m: float = 100.0) -> list[list[complex]]:
    w = 2 * math.pi * freq
    de = earth_depth_m(freq, soil_ohm_m) * 1000  # mm
    rg = math.pi ** 2 * freq * 1e-7
    n = len(conductors)
    z = [[0j] * n for _ in range(n)]
    for i, a in enumerate(conductors):
        for j, b in enumerate(conductors):
            if i == j:
                z[i][j] = complex(a.r_ohm_per_m + rg, w * MU0_2PI * math.log(de / a.gmr_mm))
            else:
                d = math.hypot(a.x_mm - b.x_mm, a.y_mm - b.y_mm)
                if d <= 0:
                    # Concentric pair (core and its shield): flux linking both
                    # lies outside the tube, so use the tube's mean radius.
                    tube = max(a.tube_radius_mm or 0, b.tube_radius_mm or 0)
                    if not tube:
                        raise ValueError(f"Conductors {i} and {j} share a position")
                    d = tube
                z[i][j] = complex(rg, w * MU0_2PI * math.log(de / d))
    return z


def solve_complex(a: list[list[complex]], b: list[complex]) -> list[complex]:
    """Gaussian elimination with partial pivoting."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-30:
            raise ValueError("Singular system: check groups and constraints")
        m[col], m[piv] = m[piv], m[col]
        for r in range(col + 1, n):
            f = m[r][col] / m[col][col]
            if f:
                for k in range(col, n + 1):
                    m[r][k] -= f * m[col][k]
    x = [0j] * n
    for r in range(n - 1, -1, -1):
        x[r] = (m[r][n] - sum(m[r][k] * x[k] for k in range(r + 1, n))) / m[r][r]
    return x


def solve_sharing(conductors: list[Conductor], groups: dict[str, Group],
                  freq: float = 60.0, soil_ohm_m: float = 100.0) -> SharingResult:
    """Solve Z I = V with group constraints.

    Unknowns: every conductor current, plus one voltage drop per phase group.
    Rows: one per conductor (Z_k . I - V_group = 0, or = 0 for bonded), plus
    one current-sum row per phase group.
    """
    for c in conductors:
        if c.group not in groups:
            raise ValueError(f"Conductor group {c.group!r} is not defined")
    n = len(conductors)
    phase_names = [g for g in groups if groups[g].kind == "phase"]
    vidx = {g: n + k for k, g in enumerate(phase_names)}
    size = n + len(phase_names)
    z = impedance_matrix(conductors, freq, soil_ohm_m)

    a = [[0j] * size for _ in range(size)]
    b = [0j] * size
    for i, c in enumerate(conductors):
        a[i][:n] = z[i]
        if groups[c.group].kind == "phase":
            a[i][vidx[c.group]] = -1
    for k, g in enumerate(phase_names):
        row = n + k
        for i, c in enumerate(conductors):
            if c.group == g:
                a[row][i] = 1
        b[row] = groups[g].current

    x = solve_complex(a, b)
    currents = x[:n]
    drops = {g: x[vidx[g]] for g in phase_names}
    losses = [abs(i) ** 2 * c.r_ohm_per_m for i, c in zip(currents, conductors)]
    return SharingResult(currents, drops, losses, conductors, groups)


def balanced_three_phase(i_rms: float, pf: float = 1.0, lagging: bool = True,
                         names: tuple[str, str, str] = ("A", "B", "C")) -> dict[str, Group]:
    phi = math.acos(max(-1.0, min(1.0, pf))) * (-1 if lagging else 1)
    return {n: Group(n, "phase", cmath.rect(i_rms, phi + k * -2 * math.pi / 3))
            for k, n in enumerate(names)}
