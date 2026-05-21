"""Rectangular reinforced concrete section geometry.

All dimensions are in millimeters. This module contains geometry helpers only;
it does not perform strength checks.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RectangularSection:
    """Rectangular section geometry for the MVP bending element."""

    b: float
    h: float
    cover: float
    stirrup_diameter: float
    main_bar_diameter: float
    compression_bar_diameter: float | None = None

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

    def compression_rebar_depth(self) -> float:
        """Return a_prime for compression reinforcement centroid, mm.

        If compression_bar_diameter is not set, the MVP assumes the main bar
        diameter for a_prime and the caller should report this simplification.
        """
        self._validate_positive_dimensions()
        diameter = self.compression_bar_diameter or self.main_bar_diameter
        return self.cover + self.stirrup_diameter + diameter / 2.0

    def validate_geometry(self) -> None:
        """Validate basic MVP geometry constraints."""
        self._validate_positive_dimensions()
        self.effective_depth()
        if self.compression_rebar_depth() >= self.h:
            raise ValueError("compression reinforcement depth must be less than section height")

    def _validate_positive_dimensions(self) -> None:
        checks = {
            "b": self.b,
            "h": self.h,
            "cover": self.cover,
            "stirrup_diameter": self.stirrup_diameter,
            "main_bar_diameter": self.main_bar_diameter,
        }
        if self.compression_bar_diameter is not None:
            checks["compression_bar_diameter"] = self.compression_bar_diameter

        for name, value in checks.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")
