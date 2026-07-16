"""Explicit local-axis contract for rectangular bending checks."""

from dataclasses import dataclass
from typing import Literal

MomentAxis = Literal["local_z"]
TensionFace = Literal["local_y_min", "local_y_max"]


@dataclass(frozen=True)
class RectangularBendingOrientation:
    """Identify the checked local axis and the tension face.

    ``M`` is supplied to the bending check as a non-negative magnitude. The
    tension face must therefore be stated explicitly instead of being inferred
    from an undocumented sign convention.
    """

    local_axes_id: str
    moment_axis: MomentAxis
    tension_face: TensionFace

    def __post_init__(self) -> None:
        if not isinstance(self.local_axes_id, str) or not self.local_axes_id.strip():
            raise ValueError("local_axes_id must be a non-empty string")
        if self.moment_axis != "local_z":
            raise ValueError("moment_axis must be 'local_z'")
        if self.tension_face not in ("local_y_min", "local_y_max"):
            raise ValueError("tension_face must be 'local_y_min' or 'local_y_max'")

    @property
    def compression_face(self) -> TensionFace:
        """Return the face opposite to the explicitly declared tension face."""
        if self.tension_face == "local_y_min":
            return "local_y_max"
        return "local_y_min"
