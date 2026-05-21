"""Draft concrete catalog for heavy concrete classes B15-B40."""

from pydantic import BaseModel, ConfigDict


class Concrete(BaseModel):
    """Concrete design properties, MPa except Eb in MPa."""

    model_config = ConfigDict(frozen=True)

    class_name: str
    Rb: float
    Rbt: float
    Eb: float
    draft_requires_engineer_review: bool = True


CONCRETE_CATALOG: dict[str, Concrete] = {
    "B15": Concrete(class_name="B15", Rb=8.5, Rbt=0.75, Eb=24_000),
    "B20": Concrete(class_name="B20", Rb=11.5, Rbt=0.90, Eb=27_500),
    "B25": Concrete(class_name="B25", Rb=14.5, Rbt=1.05, Eb=30_000),
    "B30": Concrete(class_name="B30", Rb=17.0, Rbt=1.15, Eb=32_500),
    "B35": Concrete(class_name="B35", Rb=19.5, Rbt=1.30, Eb=34_500),
    "B40": Concrete(class_name="B40", Rb=22.0, Rbt=1.40, Eb=36_000),
}


def get_concrete(class_name: str) -> Concrete:
    """Return draft concrete properties for a supported MVP class."""
    key = class_name.upper()
    try:
        return CONCRETE_CATALOG[key]
    except KeyError as exc:
        supported = ", ".join(CONCRETE_CATALOG)
        message = f"unsupported concrete class {class_name!r}; expected one of {supported}"
        raise ValueError(message) from exc
