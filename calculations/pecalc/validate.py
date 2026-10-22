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


def count_at_least(name: str, value: int, minimum: int = 1) -> int:
    """Whole-number count (conductors per phase, tiers) that must be >= minimum."""
    v = _finite(name, value)
    if v != int(v) or v < minimum:
        raise ValueError(f"{name} must be a whole number of at least {minimum}, got {value!r}")
    return int(v)


def x_over_r(name: str, value: float) -> float:
    """X/R ratio must be > 0."""
    v = _finite(name, value)
    if v <= 0:
        raise ValueError(f"{name} must be greater than 0, got {value!r}")
    return v


def non_negative(name: str, value: float, unit: str = "") -> float:
    """Value must be finite and >= 0."""
    v = _finite(name, value)
    if v < 0:
        raise ValueError(f"{name} must be 0{' ' + unit if unit else ''} or greater, got {value!r}")
    return v


def positive(name: str, value: float, unit: str = "") -> float:
    """Value must be finite and > 0."""
    v = _finite(name, value)
    if v <= 0:
        raise ValueError(f"{name} must be greater than 0{' ' + unit if unit else ''}, got {value!r}")
    return v


def in_range(name: str, value: float, low: float, high: float, unit: str = "") -> float:
    """Value must be finite and within [low, high]."""
    v = _finite(name, value)
    if not low <= v <= high:
        raise ValueError(f"{name} must be in the range [{low:g}, {high:g}]{' ' + unit if unit else ''}, got {value!r}")
    return v


def integer_at_least(name: str, value: int, minimum: int) -> int:
    """Value must be an integer (not bool, not a fractional float) >= minimum."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) \
            or value != int(value):
        raise ValueError(f"{name} must be a whole number, got {value!r}")
    if value < minimum:
        raise ValueError(f"{name} must be {minimum} or greater, got {value!r}")
    return int(value)


def one_of(name: str, value, allowed: tuple) -> object:
    """Value must be one of the allowed choices."""
    if isinstance(value, bool) or value not in allowed:
        raise ValueError(f"{name} must be one of {tuple(allowed)}, got {value!r}")
    return value
