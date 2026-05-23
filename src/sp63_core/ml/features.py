"""Feature extraction for the experimental baseline ML sandbox."""

from collections.abc import Sequence

from sp63_core.dataset import DatasetCase

CONCRETE_CLASS_CODES: dict[str, float] = {
    "B15": 15.0,
    "B20": 20.0,
    "B25": 25.0,
    "B30": 30.0,
    "B35": 35.0,
    "B40": 40.0,
}
REBAR_CLASS_CODES: dict[str, float] = {
    "A240": 240.0,
    "A400": 400.0,
    "A500": 500.0,
}
LOAD_DURATION_CODES: dict[str, float] = {
    "short": 0.0,
    "long": 1.0,
}
FEATURE_COLUMNS: tuple[str, ...] = (
    "b",
    "h",
    "h0",
    "M",
    "Q",
    "concrete_class_code",
    "rebar_class_code",
    "stirrup_class_code",
    "load_duration_long",
    "geometry_stirrup_diameter",
)
TARGET_COLUMNS: tuple[str, ...] = (
    "As_provided",
    "main_bar_count",
    "main_bar_diameter",
    "stirrup_diameter",
    "stirrup_legs",
    "stirrup_spacing",
    "bending_utilization",
    "shear_utilization",
)


def build_feature_matrix(
    cases: Sequence[DatasetCase],
) -> tuple[list[dict[str, float]], list[dict[str, float | int | str]]]:
    """Build numeric ML features and target dictionaries from dataset cases.

    Utilization and selected reinforcement values are targets only. They are not
    included in the input feature dictionaries.
    """
    features: list[dict[str, float]] = []
    targets: list[dict[str, float | int | str]] = []
    for case in cases:
        features.append(
            {
                "b": float(case.b),
                "h": float(case.h),
                "h0": float(case.h0),
                "M": float(case.M),
                "Q": float(case.Q),
                "concrete_class_code": _class_code(
                    CONCRETE_CLASS_CODES,
                    case.concrete_class,
                    "concrete_class",
                ),
                "rebar_class_code": _class_code(
                    REBAR_CLASS_CODES,
                    case.rebar_class,
                    "rebar_class",
                ),
                "stirrup_class_code": _class_code(
                    REBAR_CLASS_CODES,
                    case.stirrup_class,
                    "stirrup_class",
                ),
                "load_duration_long": _class_code(
                    LOAD_DURATION_CODES,
                    case.load_duration,
                    "load_duration",
                ),
                "geometry_stirrup_diameter": float(case.geometry_stirrup_diameter),
            }
        )
        targets.append(
            {
                "As_provided": float(case.As_provided),
                "main_bar_count": int(case.main_bar_count),
                "main_bar_diameter": int(case.main_bar_diameter),
                "stirrup_diameter": int(case.stirrup_diameter),
                "stirrup_legs": int(case.stirrup_legs),
                "stirrup_spacing": int(case.stirrup_spacing),
                "bending_utilization": float(case.bending_utilization),
                "shear_utilization": float(case.shear_utilization),
            }
        )
    return features, targets


def _class_code(mapping: dict[str, float], value: str, field_name: str) -> float:
    try:
        return mapping[value]
    except KeyError as exc:
        supported = ", ".join(mapping)
        message = f"unsupported {field_name} {value!r}; expected one of {supported}"
        raise ValueError(message) from exc
