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
from sp63_core.checks import check_shear_rectangular
from sp63_core.materials import area_by_diameter, get_concrete, get_rebar
from sp63_core.rebar import select_longitudinal_rebar
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
    stirrup_diameter: float = 8.0,
    stirrup_legs: int = 2,
    stirrup_spacing: float = 200.0,
) -> tuple[DatasetCase, ...]:
    """Generate checked dataset rows following docs/dataset_schema.md.

    Rows are emitted only when both bending and shear checks pass, so no unsafe
    accepted cases are included.
    """
    if limit <= 0:
        raise ValueError("limit must be positive")
    if stirrup_legs <= 0:
        raise ValueError("stirrup_legs must be positive")

    rows: list[DatasetCase] = []
    Asw = stirrup_legs * area_by_diameter(stirrup_diameter)
    stirrup_scheme = f"D{stirrup_diameter:g}/{stirrup_spacing:g}, {stirrup_legs} legs"

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
                                options = select_longitudinal_rebar(
                                    section=section,
                                    concrete=concrete,
                                    rebar=rebar,
                                    M=M,
                                    max_results=1,
                                )
                                if not options:
                                    continue

                                option = options[0]
                                for Q in shears:
                                    shear = check_shear_rectangular(
                                        section=option.section,
                                        concrete=concrete,
                                        stirrup_rebar=stirrup_rebar,
                                        Q=Q,
                                        Asw=Asw,
                                        sw=stirrup_spacing,
                                    )
                                    if shear.status != "pass":
                                        continue

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
                                            M=M,
                                            Q=Q,
                                            As_required=option.As,
                                            As_provided=option.As,
                                            main_rebar_scheme=option.scheme,
                                            stirrup_scheme=stirrup_scheme,
                                            Mult=option.bending.Mult,
                                            Qult=shear.Qult,
                                            bending_utilization=option.bending.utilization,
                                            shear_utilization=shear.utilization,
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
