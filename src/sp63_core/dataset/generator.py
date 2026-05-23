"""Synthetic dataset generation for the SP 63 MVP.

Dataset target values are produced only by the deterministic calculation core.
No ML model is used here.
"""

import csv
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sp63_core import __version__
from sp63_core.materials import LoadDuration, get_concrete, get_rebar
from sp63_core.rebar import select_longitudinal_rebar, select_transverse_rebar
from sp63_core.sections import RectangularSection

DATASET_VERSION = "0.1"
DATASET_COLUMNS: tuple[str, ...] = (
    "case_id",
    "element_type",
    "b",
    "h",
    "h0",
    "concrete_class",
    "rebar_class",
    "stirrup_class",
    "load_duration",
    "M",
    "Q",
    "As_required",
    "As_provided",
    "main_bar_count",
    "main_bar_diameter",
    "main_rebar_scheme",
    "main_rebar_constructive_status",
    "main_rebar_ratio_percent",
    "main_rebar_layout_feasible",
    "stirrup_scheme",
    "stirrup_diameter",
    "stirrup_legs",
    "stirrup_spacing",
    "stirrup_Asw",
    "stirrup_steel_consumption",
    "stirrup_constructive_status",
    "stirrup_constructive_max_spacing",
    "stirrup_sw_max_by_shear_rule",
    "stirrup_qsw_rule_status",
    "stirrup_transverse_reinforcement_countable",
    "Mult",
    "Qult",
    "bending_utilization",
    "shear_utilization",
    "status",
    "sp63_core_version",
    "dataset_version",
)


@dataclass(frozen=True)
class DatasetCase:
    """One row of the MVP dataset schema."""

    case_id: str
    element_type: str
    b: float
    h: float
    h0: float
    concrete_class: str
    rebar_class: str
    stirrup_class: str
    load_duration: str
    M: float
    Q: float
    As_required: float
    As_provided: float
    main_bar_count: int
    main_bar_diameter: int
    main_rebar_scheme: str
    main_rebar_constructive_status: str
    main_rebar_ratio_percent: float
    main_rebar_layout_feasible: bool
    stirrup_scheme: str
    stirrup_diameter: int
    stirrup_legs: int
    stirrup_spacing: int
    stirrup_Asw: float
    stirrup_steel_consumption: float
    stirrup_constructive_status: str
    stirrup_constructive_max_spacing: float
    stirrup_sw_max_by_shear_rule: float
    stirrup_qsw_rule_status: str
    stirrup_transverse_reinforcement_countable: bool
    Mult: float
    Qult: float
    bending_utilization: float
    shear_utilization: float
    status: str
    sp63_core_version: str
    dataset_version: str

    def as_row(self) -> dict[str, Any]:
        """Return a CSV-ready row ordered by DATASET_COLUMNS."""
        raw = asdict(self)
        return {column: raw[column] for column in DATASET_COLUMNS}


def generate_dataset_cases(
    *,
    limit: int = 1000,
    element_types: Iterable[str] = ("beam",),
    widths: Iterable[float] = (250, 300, 350, 400, 500),
    heights: Iterable[float] = (400, 450, 500, 550, 600),
    cover: float = 32.0,
    section_stirrup_diameter: float = 8.0,
    section_main_bar_diameter: float = 20.0,
    concrete_classes: Iterable[str] = ("B20", "B25", "B30", "B35"),
    rebar_classes: Iterable[str] = ("A400", "A500"),
    stirrup_classes: Iterable[str] = ("A240", "A400"),
    load_duration: LoadDuration = "short",
    moments: Iterable[float] = (80_000_000, 120_000_000, 150_000_000, 200_000_000),
    shears: Iterable[float] = (50_000, 80_000, 120_000, 160_000),
) -> tuple[DatasetCase, ...]:
    """Generate checked dataset rows following docs/dataset_schema.md.

    Rows are emitted only when both bending and shear checks pass, so no unsafe
    accepted cases are included.
    """
    if limit <= 0:
        raise ValueError("limit must be positive")

    normalized_element_types = tuple(element_types)
    unsupported_element_types = [
        element_type for element_type in normalized_element_types if element_type != "beam"
    ]
    if unsupported_element_types:
        raise ValueError("only beam element_type is supported in dataset MVP")

    rows: list[DatasetCase] = []

    for element_type in normalized_element_types:
        for b in widths:
            for h in heights:
                section = RectangularSection(
                    b=b,
                    h=h,
                    cover=cover,
                    stirrup_diameter=section_stirrup_diameter,
                    main_bar_diameter=section_main_bar_diameter,
                )
                for concrete_class in concrete_classes:
                    concrete = get_concrete(concrete_class)
                    for rebar_class in rebar_classes:
                        rebar = get_rebar(rebar_class)
                        for stirrup_class in stirrup_classes:
                            stirrup_rebar = get_rebar(stirrup_class)
                            for M in moments:
                                options = select_longitudinal_rebar(
                                    section=section,
                                    concrete=concrete,
                                    rebar=rebar,
                                    M=M,
                                    max_results=1,
                                    load_duration=load_duration,
                                )
                                if not options:
                                    continue

                                option = options[0]
                                for Q in shears:
                                    transverse_options = select_transverse_rebar(
                                        section=option.section,
                                        concrete=concrete,
                                        stirrup_rebar=stirrup_rebar,
                                        Q=Q,
                                        max_results=1,
                                    )
                                    if not transverse_options:
                                        continue
                                    transverse_option = transverse_options[0]
                                    main_constructive_values = (
                                        option.constructive.intermediate_values
                                    )
                                    stirrup_constructive_values = (
                                        transverse_option.constructive.intermediate_values
                                    )
                                    stirrup_shear_values = (
                                        transverse_option.shear.intermediate_values
                                    )

                                    case_id = f"case_{len(rows) + 1:06d}"
                                    rows.append(
                                        DatasetCase(
                                            case_id=case_id,
                                            element_type=element_type,
                                            b=b,
                                            h=h,
                                            h0=option.section.effective_depth(),
                                            concrete_class=concrete_class,
                                            rebar_class=rebar_class,
                                            stirrup_class=stirrup_class,
                                            load_duration=load_duration,
                                            M=M,
                                            Q=Q,
                                            As_required=option.As,
                                            As_provided=option.As,
                                            main_bar_count=option.bar_count,
                                            main_bar_diameter=option.diameter,
                                            main_rebar_scheme=option.scheme,
                                            main_rebar_constructive_status=(
                                                option.constructive.status
                                            ),
                                            main_rebar_ratio_percent=main_constructive_values[
                                                "reinforcement_ratio_percent"
                                            ],
                                            main_rebar_layout_feasible=option.layout.layout_feasible,
                                            stirrup_scheme=transverse_option.scheme,
                                            stirrup_diameter=transverse_option.diameter,
                                            stirrup_legs=transverse_option.legs,
                                            stirrup_spacing=transverse_option.spacing,
                                            stirrup_Asw=transverse_option.Asw,
                                            stirrup_steel_consumption=(
                                                transverse_option.steel_consumption
                                            ),
                                            stirrup_constructive_status=(
                                                transverse_option.constructive.status
                                            ),
                                            stirrup_constructive_max_spacing=(
                                                stirrup_constructive_values["max_spacing"]
                                            ),
                                            stirrup_sw_max_by_shear_rule=stirrup_shear_values[
                                                "sw_max_by_shear_rule"
                                            ],
                                            stirrup_qsw_rule_status=stirrup_shear_values[
                                                "qsw_rule_status"
                                            ],
                                            stirrup_transverse_reinforcement_countable=(
                                                stirrup_shear_values[
                                                    "transverse_reinforcement_countable"
                                                ]
                                            ),
                                            Mult=option.bending.Mult,
                                            Qult=transverse_option.shear.Qult,
                                            bending_utilization=option.bending.utilization,
                                            shear_utilization=transverse_option.shear.utilization,
                                            status="pass",
                                            sp63_core_version=__version__,
                                            dataset_version=DATASET_VERSION,
                                        )
                                    )
                                    if len(rows) >= limit:
                                        return tuple(rows)

    return tuple(rows)


def export_dataset_csv(
    cases: Iterable[DatasetCase | Mapping[str, Any]],
    path: str | Path,
) -> Path:
    """Export dataset cases to CSV using the documented column order."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=DATASET_COLUMNS)
        writer.writeheader()
        for case in cases:
            row = case.as_row() if isinstance(case, DatasetCase) else dict(case)
            writer.writerow({column: row[column] for column in DATASET_COLUMNS})

    return output_path
