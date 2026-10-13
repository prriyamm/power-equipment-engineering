"""Shared input validation: every module raises the same ValueError messages.

Checks are applied where a value enters the engine (the module entry points
and the shared solvers), so a bad value fails loudly instead of producing a
silent NaN, a negative ampacity or a zero-division.
"""

from __future__ import annotations

import math


def _finite(name: str, value: float) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number, got {value!r}") from None
    if not math.isfinite(v):
        raise ValueError(f"{name} must be finite, got {value!r}")
    return v


def voltage(name: str, value: float) -> float:
    """Voltage must be > 0 V."""
    v = _finite(name, value)
    if v <= 0:
        raise ValueError(f"{name} must be greater than 0 V, got {value!r}")
    return v


def power_factor(name: str, value: float) -> float:
    """Power factor magnitude must be in (0, 1]; leading/lagging is a separate flag."""
    v = _finite(name, value)
    if not 0 < v <= 1:
        raise ValueError(f"{name} must be in the range (0, 1], got {value!r}")
    return v


def clearing_time(name: str, value: float) -> float:
    """Fault clearing / duration time must be > 0 s."""
    v = _finite(name, value)
    if v <= 0:
        raise ValueError(f"{name} must be greater than 0 s, got {value!r}")
    return v


def x_over_r(name: str, value: float) -> float:
    """X/R ratio must be > 0."""
    v = _finite(name, value)
    if v <= 0:
        raise ValueError(f"{name} must be greater than 0, got {value!r}")
    return v
