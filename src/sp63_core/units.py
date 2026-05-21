"""Unit conversions for SP 63 calculations.

Project convention:
- force: N
- moment: N*mm
- dimensions: mm
- stress: MPa = N/mm^2
- reinforcement area: mm^2
"""


def kN_to_N(value: float) -> float:
    """Convert kilonewtons to newtons."""
    return float(value) * 1_000.0


def kNm_to_Nmm(value: float) -> float:
    """Convert kilonewton-meters to newton-millimeters."""
    return float(value) * 1_000_000.0


def cm2_to_mm2(value: float) -> float:
    """Convert square centimeters to square millimeters."""
    return float(value) * 100.0


def mm2_to_cm2(value: float) -> float:
    """Convert square millimeters to square centimeters."""
    return float(value) / 100.0


def MPa_to_N_per_mm2(value: float) -> float:
    """Numerically MPa equals N/mm^2; kept for explicitness."""
    return float(value)
