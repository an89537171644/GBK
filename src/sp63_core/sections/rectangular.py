"""Rectangular reinforced concrete section geometry.

All dimensions are in millimeters. This module contains geometry helpers only;
it does not perform strength checks.
"""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class RectangularSection:
    """Rectangular section geometry for the one-row MVP layout.

    ``cover`` is the distance from the concrete face to the outer surface of
    the stirrup. The checked face is supplied separately by the explicit
    bending-orientation contract. Effective depth is always derived from the
    declared geometry; arbitrary overrides are intentionally unsupported.
    """

    b: float
    h: float
    cover: float
    stirrup_diameter: float
    main_bar_diameter: float

    def gross_area(self) -> float:
        """Return gross concrete area b*h, mm^2."""
        self.validate_geometry()
        return self.b * self.h

    def effective_depth(self) -> float:
        """Return h0 for tensile reinforcement centroid, mm."""
        self._validate_positive_dimensions()
        h0 = self.h - self.cover - self.stirrup_diameter - self.main_bar_diameter / 2.0
        if h0 <= 0:
            raise ValueError("effective depth h0 must be positive")
        return h0

    def validate_geometry(self) -> None:
        """Validate basic MVP geometry constraints."""
        self._validate_positive_dimensions()
        self.effective_depth()

    def _validate_positive_dimensions(self) -> None:
        checks = {
            "b": self.b,
            "h": self.h,
            "cover": self.cover,
            "stirrup_diameter": self.stirrup_diameter,
            "main_bar_diameter": self.main_bar_diameter,
        }

        for name, value in checks.items():
            if not isfinite(value):
                raise ValueError(f"{name} must be finite")
            if value <= 0:
                raise ValueError(f"{name} must be positive")
