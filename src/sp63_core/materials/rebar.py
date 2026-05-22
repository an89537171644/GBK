"""Draft reinforcement catalog and diameter helpers for MVP inputs."""

from math import pi
from typing import Literal

from pydantic import BaseModel, ConfigDict


class Rebar(BaseModel):
    """Reinforcement design properties, MPa."""

    model_config = ConfigDict(frozen=True)

    class_name: str
    Rsn: float
    Rs: float
    Rsc_long: float
    Rsc_short: float
    Rsw: float
    Es: float
    draft_requires_engineer_review: bool = True

    @property
    def Rsc(self) -> float:
        """Default MVP compression resistance for short-term action."""
        return self.Rsc_short

    def compression_resistance(self, load_duration: Literal["short", "long"] = "short") -> float:
        """Return compression resistance for the requested load duration."""
        if load_duration == "short":
            return self.Rsc_short
        if load_duration == "long":
            return self.Rsc_long
        raise ValueError("load_duration must be 'short' or 'long'")


REBAR_CATALOG: dict[str, Rebar] = {
    "A240": Rebar(
        class_name="A240",
        Rsn=240,
        Rs=210,
        Rsc_long=210,
        Rsc_short=210,
        Rsw=170,
        Es=200_000,
    ),
    "A400": Rebar(
        class_name="A400",
        Rsn=400,
        Rs=350,
        Rsc_long=350,
        Rsc_short=350,
        Rsw=280,
        Es=200_000,
    ),
    "A500": Rebar(
        class_name="A500",
        Rsn=500,
        Rs=435,
        Rsc_long=435,
        Rsc_short=400,
        Rsw=300,
        Es=200_000,
    ),
}

LONGITUDINAL_DIAMETERS: tuple[int, ...] = (10, 12, 14, 16, 18, 20, 22, 25, 28, 32)
STIRRUP_DIAMETERS: tuple[int, ...] = (6, 8, 10, 12)


def get_rebar(class_name: str) -> Rebar:
    """Return draft reinforcement properties for a supported MVP class."""
    key = class_name.upper()
    try:
        return REBAR_CATALOG[key]
    except KeyError as exc:
        supported = ", ".join(REBAR_CATALOG)
        message = f"unsupported rebar class {class_name!r}; expected one of {supported}"
        raise ValueError(message) from exc


def area_by_diameter(diameter: float) -> float:
    """Return circular bar area by diameter, mm^2."""
    if diameter <= 0:
        raise ValueError("diameter must be positive")
    return pi * diameter**2 / 4.0
