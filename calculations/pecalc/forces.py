"""Short-circuit electromagnetic forces on parallel conductors.

Time-domain method: the asymmetrical fault current of each phase is

    i_p(t) = sqrt(2) I [sin(wt + a - phi - 120 deg k) - sin(a - phi - 120 deg k) e^(-t/tau)]

with tau = (X/R) / w. Each conductor carries its share of its phase (ratio from
the impedance solver) and the force per metre on conductor i is the vector sum
of 2e-7 i_i i_j / d_ij over all other conductors (Ampere's force law, the basis
of IEEE 605 and IEC 60865). The worst case over fault inception angle and the
first cycles is reported. For two-conductor or three-phase flat layouts this
reproduces the classic 2e-7 i^2 / d and 0.866 peak factor results.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import validate
from .impedance import Conductor

N_PER_M_TO_LBF_PER_FT = 0.0685218


def peak_factor(x_over_r: float, freq: float = 60.0) -> float:
    """Ratio of first asymmetrical peak to RMS symmetrical current.

    Approximation k = sqrt(2) (1.02 + 0.98 e^(-3 R/X)) (IEC 60909-0 eq. 55),
    used for reporting; the force calculation itself is time-domain.
    """
    validate.x_over_r("x_over_r", x_over_r)
    return math.sqrt(2) * (1.02 + 0.98 * math.exp(-3 / x_over_r))


@dataclass
class ForceResult:
    peak_n_per_m: list[float]       # worst-case peak force magnitude per conductor
    worst_index: int
    worst_n_per_m: float
    peak_current_ka: float          # largest instantaneous phase current
    x_over_r: float
    body_peak_n_per_m: dict | None = None   # worst-case resultant per body (bar / phase pack)
    body_peak_xy: dict | None = None        # (|Fx| max, |Fy| max) per body

    @property
    def worst_lbf_per_ft(self) -> float:
        return self.worst_n_per_m * N_PER_M_TO_LBF_PER_FT


def fault_forces(conductors: list[Conductor], share: dict[int, complex], fault_ka_rms: float,
                 x_over_r: float, freq: float = 60.0, phases: tuple[str, ...] = ("A", "B", "C"),
                 cycles: float = 1.0, steps_per_cycle: int = 96, angle_steps: int = 24,
                 bodies: dict[int, str] | None = None) -> ForceResult:
    """share[i] = conductor i's complex fraction of its phase current (from solve_sharing).

    Conductors whose group is not in `phases` (e.g. shields) are ignored.
    bodies maps conductor index -> body name (e.g. filaments of one bar); the
    vector sum per body is tracked, so a bar split into filaments gets its
    true resultant (internal filament forces cancel in pairs).
    """
    validate.x_over_r("x_over_r", x_over_r)
    w = 2 * math.pi * freq
    tau = x_over_r / w
    phi = math.atan(x_over_r)
    amp = math.sqrt(2) * fault_ka_rms * 1000
    idx = [i for i, c in enumerate(conductors) if c.group in phases]
    pos = {i: (conductors[i].x_mm / 1000, conductors[i].y_mm / 1000) for i in idx}
    # Pre-compute geometry: unit vectors and 2e-7/d.
    geo = {}
    for i in idx:
        for j in idx:
            if i != j:
                dx, dy = pos[i][0] - pos[j][0], pos[i][1] - pos[j][1]
                d = math.hypot(dx, dy)
                geo[i, j] = (2e-7 / d, dx / d, dy / d)

    worst = [0.0] * len(conductors)
    body_names = sorted(set(bodies.values())) if bodies else []
    body_worst = {b: 0.0 for b in body_names}
    body_xy = {b: [0.0, 0.0] for b in body_names}
    i_peak = 0.0
    n_t = int(cycles * steps_per_cycle) + 1
    for a_step in range(angle_steps):
        alpha = math.pi * a_step / angle_steps
        for t_step in range(n_t):
            t = t_step / (steps_per_cycle * freq)
            decay = math.exp(-t / tau)
            # Instantaneous phase currents; conductor share applied via magnitude/angle.
            inst = {}
            for i in idx:
                k = phases.index(conductors[i].group)
                s = share[i]
                th = alpha - phi - 2 * math.pi * k / 3 + math.atan2(s.imag, s.real)
                inst[i] = abs(s) * amp * (math.sin(w * t + th) - math.sin(th) * decay)
                i_peak = max(i_peak, abs(inst[i]) / abs(s) if abs(s) > 1e-12 else 0)
            acc = {b: [0.0, 0.0] for b in body_names}
            for i in idx:
                fx = fy = 0.0
                for j in idx:
                    if i != j:
                        k_d, ux, uy = geo[i, j]
                        f = k_d * inst[i] * inst[j]   # attractive if same sign
                        fx -= f * ux
                        fy -= f * uy
                mag = math.hypot(fx, fy)
                if mag > worst[i]:
                    worst[i] = mag
                if bodies and i in bodies:
                    a = acc[bodies[i]]
                    a[0] += fx
                    a[1] += fy
            for b, (fx, fy) in acc.items():
                body_worst[b] = max(body_worst[b], math.hypot(fx, fy))
                body_xy[b][0] = max(body_xy[b][0], abs(fx))
                body_xy[b][1] = max(body_xy[b][1], abs(fy))
    w_i = max(range(len(worst)), key=worst.__getitem__)
    return ForceResult(worst, w_i, worst[w_i], i_peak / 1000, x_over_r,
                       body_worst or None, {b: tuple(v) for b, v in body_xy.items()} or None)
