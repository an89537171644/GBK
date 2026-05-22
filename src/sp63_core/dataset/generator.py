"""Synthetic dataset generation for the SP 63 MVP.

Dataset target values are produced only by the deterministic design service.
No ML model is used here.
"""

import csv
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from math import isclose
from pathlib import Path
from typing import Any

from sp63_core import __version__
from sp63_core.materials import get_concrete, get_rebar
from sp63_core.sections import RectangularSection
from sp63_core.services import RectangularDesignResult, design_rectangular_element

DATASET_VERSION = "0.2"
DATASET_COLUMNS: tuple[str, ...] = (
    "case_id",
    "element_type",
    "b",
    "h",
    "h0",
    "concrete_class",
    "rebar_class",
    "stirrup_class",
    "M",
    "Q",
    "As_required",
    "As_provided",
    "main_rebar_scheme",
    "stirrup_scheme",
    "Mult",
    "Qult",
    "bending_utilization",
    "shear_utilization",
    "status",
    "sp63_core_version",
    "dataset_version",
    "main_bar_count",
    "main_bar_diameter",
    "stirrup_diameter",
    "stirrup_legs",
    "stirrup_spacing",
    "Asw",
    "layout_clear_width",
    "layout_required_width",
    "layout_feasible",
    "requires_engineer_review",
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
    M: float
    Q: float
    As_required: float
    As_provided: float
    main_rebar_scheme: str
    stirrup_scheme: str
    Mult: float
    Qult: float
    bending_utilization: float
    shear_utilization: float
    status: str
    sp63_core_version: str
    dataset_version: str
    main_bar_count: int
    main_bar_diameter: float
    stirrup_diameter: float
    stirrup_legs: int
    stirrup_spacing: float
    Asw: float
    layout_clear_width: float
    layout_required_width: float
    layout_feasible: bool
    requires_engineer_review: bool

    def as_row(self) -> dict[str, Any]:
        """Return a CSV-ready row ordered by DATASET_COLUMNS."""
        raw = asdict(self)
        return {column: raw[column] for column in DATASET_COLUMNS}


def generate_dataset_cases(
    *,
    limit: int = 1000,
    element_types: Iterable[str] = ("beam", "slab"),
    widths: Iterable[float] = (250, 300, 350, 400, 500),
    heights: Iterable[float] = (400, 450, 500, 550, 600),
    cover: float = 32.0,
    section_stirrup_diameter: float = 8.0,
    section_main_bar_diameter: float = 20.0,
    concrete_classes: Iterable[str] = ("B20", "B25", "B30", "B35"),
    rebar_classes: Iterable[str] = ("A400", "A500"),
    stirrup_classes: Iterable[str] = ("A240", "A400"),
    moments: Iterable[float] = (80_000_000, 120_000_000, 150_000_000, 200_000_000),
    shears: Iterable[float] = (50_000, 80_000, 120_000, 160_000),
) -> tuple[DatasetCase, ...]:
    """Generate checked dataset rows following docs/dataset_schema.md."""
    if limit <= 0:
        raise ValueError("limit must be positive")

    rows: list[DatasetCase] = []
    for element_type in element_types:
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
                                for Q in shears:
                                    design = design_rectangular_element(
                                        section=section,
                                        concrete=concrete,
                                        longitudinal_rebar=rebar,
                                        transverse_rebar=stirrup_rebar,
                                        M=M,
                                        Q=Q,
                                        longitudinal_max_results=1,
                                        transverse_max_results=1,
                                    )
                                    if not _is_safe_dataset_design(design):
                                        continue

                                    rows.append(
                                        _case_from_design(
                                            design=design,
                                            case_id=f"case_{len(rows) + 1:06d}",
                                            element_type=element_type,
                                        )
                                    )
                                    if len(rows) >= limit:
                                        return tuple(rows)

    return tuple(rows)


def split_dataset_cases(
    cases: Sequence[DatasetCase],
    train_ratio: float = 0.70,
    validation_ratio: float = 0.15,
    test_ratio: float = 0.15,
) -> dict[str, tuple[DatasetCase, ...]]:
    """Split cases deterministically into train, validation, and test sets."""
    _validate_split_ratios(
        train_ratio=train_ratio,
        validation_ratio=validation_ratio,
        test_ratio=test_ratio,
    )
    if not cases:
        return {"train": (), "validation": (), "test": ()}

    total = len(cases)
    train_count = int(total * train_ratio)
    validation_count = int(total * validation_ratio)
    train_end = train_count
    validation_end = train_end + validation_count

    return {
        "train": tuple(cases[:train_end]),
        "validation": tuple(cases[train_end:validation_end]),
        "test": tuple(cases[validation_end:]),
    }


def export_dataset_splits(
    cases: Sequence[DatasetCase],
    output_dir: str | Path,
) -> dict[str, Path]:
    """Export train, validation, and test CSV files."""
    root = Path(output_dir)
    splits = split_dataset_cases(cases)
    return {
        split_name: export_dataset_csv(split_cases, root / f"{split_name}.csv")
        for split_name, split_cases in splits.items()
    }


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


def _is_safe_dataset_design(design: RectangularDesignResult) -> bool:
    longitudinal = design.selected_longitudinal
    transverse = design.selected_transverse
    return (
        design.status == "pass"
        and longitudinal is not None
        and transverse is not None
        and design.protocol is not None
        and longitudinal.utilization <= 1.0
        and transverse.utilization <= 1.0
        and longitudinal.layout.layout_feasible is True
    )


def _case_from_design(
    *,
    design: RectangularDesignResult,
    case_id: str,
    element_type: str,
) -> DatasetCase:
    longitudinal = design.selected_longitudinal
    transverse = design.selected_transverse
    if longitudinal is None or transverse is None:
        raise ValueError("safe dataset design must include selected reinforcement")

    section = longitudinal.section
    return DatasetCase(
        case_id=case_id,
        element_type=element_type,
        b=section.b,
        h=section.h,
        h0=section.effective_depth(),
        concrete_class=design.concrete.class_name,
        rebar_class=design.longitudinal_rebar.class_name,
        stirrup_class=design.transverse_rebar.class_name,
        M=design.M,
        Q=design.Q,
        As_required=longitudinal.As,
        As_provided=longitudinal.As,
        main_rebar_scheme=longitudinal.scheme,
        stirrup_scheme=transverse.scheme,
        Mult=longitudinal.bending.Mult,
        Qult=transverse.shear.Qult,
        bending_utilization=longitudinal.bending.utilization,
        shear_utilization=transverse.shear.utilization,
        status=design.status,
        sp63_core_version=__version__,
        dataset_version=DATASET_VERSION,
        main_bar_count=longitudinal.bar_count,
        main_bar_diameter=longitudinal.diameter,
        stirrup_diameter=transverse.diameter,
        stirrup_legs=transverse.legs,
        stirrup_spacing=transverse.spacing,
        Asw=transverse.Asw,
        layout_clear_width=longitudinal.layout.clear_width,
        layout_required_width=longitudinal.layout.required_width,
        layout_feasible=longitudinal.layout.layout_feasible,
        requires_engineer_review=design.requires_engineer_review,
    )


def _validate_split_ratios(
    *,
    train_ratio: float,
    validation_ratio: float,
    test_ratio: float,
) -> None:
    ratios = (train_ratio, validation_ratio, test_ratio)
    if any(ratio < 0 for ratio in ratios):
        raise ValueError("split ratios must be non-negative")
    if not isclose(sum(ratios), 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("split ratios must sum to 1.0")
