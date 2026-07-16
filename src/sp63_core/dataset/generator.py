"""Synthetic dataset generation for the SP 63 MVP.

Dataset target values are produced only by the deterministic calculation core.
No ML model is used here.
"""

import csv
import random
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from sp63_core import __version__
from sp63_core.checks import (
    check_curvature_deflection_rectangular,
    check_normal_crack_formation_rectangular,
    check_normal_crack_width_rectangular,
)
from sp63_core.materials import STIRRUP_DIAMETERS, LoadDuration, get_concrete, get_rebar
from sp63_core.rebar import select_longitudinal_rebar, select_transverse_rebar
from sp63_core.report import build_calculation_protocol
from sp63_core.sections import RectangularBendingOrientation, RectangularSection

DATASET_VERSION = "0.3"
DATASET_SOURCE = "deterministic_sp63_core"
SYNTHETIC_BENDING_ORIENTATION = RectangularBendingOrientation(
    local_axes_id="synthetic-dataset-local-axes",
    moment_axis="local_z",
    tension_face="local_y_min",
)
_FULL_GRID_CACHE: dict[tuple[Any, ...], tuple["DatasetCase", ...]] = {}
DATASET_COLUMNS: tuple[str, ...] = (
    "case_id",
    "group_key",
    "element_type",
    "b",
    "h",
    "cover",
    "h0",
    "geometry_stirrup_diameter",
    "concrete_class",
    "rebar_class",
    "stirrup_class",
    "local_axes_id",
    "moment_axis",
    "tension_face",
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
    "section_b_mm",
    "section_h_mm",
    "effective_depth_mm",
    "cover_mm",
    "main_bar_diameter_mm",
    "stirrup_diameter_mm",
    "stirrup_spacing_mm",
    "main_rebar_class",
    "stirrup_rebar_class",
    "moment_nmm",
    "shear_n",
    "moment_service_nmm",
    "span_mm",
    "longitudinal_as_mm2",
    "transverse_asw_mm2",
    "bending_mult_nmm",
    "shear_qult_n",
    "mcrc_nmm",
    "crack_width_mm",
    "deflection_mm",
    "bending_status",
    "shear_status",
    "crack_formation_status",
    "crack_width_status",
    "deflection_status",
    "strength_status",
    "serviceability_status",
    "overall_status",
    "completeness_status",
    "evidence_status",
    "project_use_status",
    "project_use",
    "warnings_count",
    "requires_engineer_review",
    "unsafe_row",
    "dataset_source",
    "sp63_core_version",
    "dataset_version",
)


@dataclass(frozen=True)
class DatasetCase:
    """One row of the MVP dataset schema."""

    case_id: str
    group_key: str
    element_type: str
    b: float
    h: float
    cover: float
    h0: float
    geometry_stirrup_diameter: int
    concrete_class: str
    rebar_class: str
    stirrup_class: str
    local_axes_id: str
    moment_axis: str
    tension_face: str
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
    section_b_mm: float
    section_h_mm: float
    effective_depth_mm: float
    cover_mm: float
    main_bar_diameter_mm: int
    stirrup_diameter_mm: int
    stirrup_spacing_mm: int
    main_rebar_class: str
    stirrup_rebar_class: str
    moment_nmm: float
    shear_n: float
    moment_service_nmm: float
    span_mm: float
    longitudinal_as_mm2: float
    transverse_asw_mm2: float
    bending_mult_nmm: float
    shear_qult_n: float
    mcrc_nmm: float
    crack_width_mm: float
    deflection_mm: float
    bending_status: str
    shear_status: str
    crack_formation_status: str
    crack_width_status: str
    deflection_status: str
    strength_status: str
    serviceability_status: str
    overall_status: str
    completeness_status: str
    evidence_status: str
    project_use_status: str
    project_use: bool
    warnings_count: int
    requires_engineer_review: bool
    unsafe_row: bool
    dataset_source: str
    sp63_core_version: str
    dataset_version: str

    def __post_init__(self) -> None:
        """Reject legacy or incomplete provenance instead of inferring it."""
        if self.dataset_version != DATASET_VERSION:
            raise ValueError(
                f"unsupported dataset_version {self.dataset_version!r}; "
                f"expected {DATASET_VERSION!r}"
            )
        RectangularBendingOrientation(
            local_axes_id=self.local_axes_id,
            moment_axis=self.moment_axis,
            tension_face=self.tension_face,
        )
        if self.load_duration != "short":
            raise ValueError(
                "dataset v0.3 load_duration must be 'short' until the "
                "shear load-combination context is implemented"
            )
        if self.completeness_status != "incomplete":
            raise ValueError("dataset v0.3 completeness_status must be 'incomplete'")
        if self.evidence_status != "needs_engineer_review":
            raise ValueError(
                "dataset v0.3 evidence_status must be 'needs_engineer_review'"
            )
        if self.project_use_status != "prohibited":
            raise ValueError("dataset v0.3 project_use_status must be 'prohibited'")
        if self.project_use is not False:
            raise ValueError("dataset v0.3 project_use must be false")
        if self.requires_engineer_review is not True:
            raise ValueError("dataset v0.3 requires_engineer_review must be true")
        if self.dataset_source != DATASET_SOURCE:
            raise ValueError(
                f"dataset v0.3 dataset_source must be {DATASET_SOURCE!r}"
            )

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
    load_duration: LoadDuration,
    moments: Iterable[float] = (80_000_000, 120_000_000, 150_000_000, 200_000_000),
    shears: Iterable[float] = (50_000, 80_000, 120_000, 160_000),
    service_moment_ratio: float = 0.2,
    span: float = 6000.0,
    shuffle: bool = True,
    seed: int = 42,
) -> tuple[DatasetCase, ...]:
    """Generate checked dataset rows following docs/dataset_schema.md.

    Rows are emitted only when both bending and shear checks pass, so no unsafe
    accepted cases are included.
    """
    if limit <= 0:
        raise ValueError("limit must be positive")
    if service_moment_ratio < 0:
        raise ValueError("service_moment_ratio must be non-negative")
    if span <= 0:
        raise ValueError("span must be positive")
    if load_duration not in ("short", "long"):
        raise ValueError("load_duration must be 'short' or 'long'")
    if load_duration == "long":
        raise ValueError(
            "load_duration='long' is unsupported for dataset generation "
            "until the shear load-combination context is implemented"
        )

    normalized_element_types = tuple(element_types)
    normalized_widths = tuple(widths)
    normalized_heights = tuple(heights)
    normalized_concrete_classes = tuple(concrete_classes)
    normalized_rebar_classes = tuple(rebar_classes)
    normalized_stirrup_classes = tuple(stirrup_classes)
    normalized_moments = tuple(moments)
    normalized_shears = tuple(shears)
    unsupported_element_types = [
        element_type for element_type in normalized_element_types if element_type != "beam"
    ]
    if unsupported_element_types:
        raise ValueError("only beam element_type is supported in dataset MVP")

    geometry_stirrup_diameter = _normalize_geometry_stirrup_diameter(
        section_stirrup_diameter
    )

    cache_key = (
        normalized_element_types,
        normalized_widths,
        normalized_heights,
        cover,
        geometry_stirrup_diameter,
        section_main_bar_diameter,
        normalized_concrete_classes,
        normalized_rebar_classes,
        normalized_stirrup_classes,
        load_duration,
        normalized_moments,
        normalized_shears,
        service_moment_ratio,
        span,
    )
    cached_rows = _FULL_GRID_CACHE.get(cache_key)
    if cached_rows is None:
        all_rows = _build_full_grid_rows(
            element_types=normalized_element_types,
            widths=normalized_widths,
            heights=normalized_heights,
            cover=cover,
            geometry_stirrup_diameter=geometry_stirrup_diameter,
            section_main_bar_diameter=section_main_bar_diameter,
            concrete_classes=normalized_concrete_classes,
            rebar_classes=normalized_rebar_classes,
            stirrup_classes=normalized_stirrup_classes,
            load_duration=load_duration,
            moments=normalized_moments,
            shears=normalized_shears,
            service_moment_ratio=service_moment_ratio,
            span=span,
        )
        _FULL_GRID_CACHE[cache_key] = tuple(all_rows)
    else:
        all_rows = list(cached_rows)

    if shuffle:
        random.Random(seed).shuffle(all_rows)

    selected_rows = all_rows[:limit]
    return tuple(
        replace(row, case_id=f"case_{index:06d}")
        for index, row in enumerate(selected_rows, start=1)
    )


def _build_full_grid_rows(
    *,
    element_types: tuple[str, ...],
    widths: tuple[float, ...],
    heights: tuple[float, ...],
    cover: float,
    geometry_stirrup_diameter: int,
    section_main_bar_diameter: float,
    concrete_classes: tuple[str, ...],
    rebar_classes: tuple[str, ...],
    stirrup_classes: tuple[str, ...],
    load_duration: LoadDuration,
    moments: tuple[float, ...],
    shears: tuple[float, ...],
    service_moment_ratio: float,
    span: float,
) -> list[DatasetCase]:
    all_rows: list[DatasetCase] = []
    longitudinal_cache: dict[tuple[Any, ...], Any] = {}
    transverse_cache: dict[tuple[Any, ...], Any] = {}
    for element_type in element_types:
        for b in widths:
            for h in heights:
                section = RectangularSection(
                    b=b,
                    h=h,
                    cover=cover,
                    stirrup_diameter=geometry_stirrup_diameter,
                    main_bar_diameter=section_main_bar_diameter,
                )
                for concrete_class in concrete_classes:
                    concrete = get_concrete(concrete_class)
                    for rebar_class in rebar_classes:
                        rebar = get_rebar(rebar_class)
                        for stirrup_class in stirrup_classes:
                            stirrup_rebar = get_rebar(stirrup_class)
                            for M in moments:
                                longitudinal_key = (
                                    b,
                                    h,
                                    cover,
                                    geometry_stirrup_diameter,
                                    section_main_bar_diameter,
                                    concrete_class,
                                    rebar_class,
                                    load_duration,
                                    M,
                                )
                                options = longitudinal_cache.get(longitudinal_key)
                                if options is None:
                                    options = select_longitudinal_rebar(
                                        section=section,
                                        concrete=concrete,
                                        rebar=rebar,
                                        M=M,
                                        orientation=SYNTHETIC_BENDING_ORIENTATION,
                                        load_duration=load_duration,
                                        max_results=1,
                                    )
                                    longitudinal_cache[longitudinal_key] = options
                                if not options:
                                    continue

                                option = options[0]
                                for Q in shears:
                                    transverse_key = (
                                        option.section.b,
                                        option.section.h,
                                        option.section.cover,
                                        option.section.stirrup_diameter,
                                        option.section.main_bar_diameter,
                                        concrete_class,
                                        stirrup_class,
                                        Q,
                                        geometry_stirrup_diameter,
                                    )
                                    transverse_options = transverse_cache.get(transverse_key)
                                    if transverse_options is None:
                                        transverse_options = select_transverse_rebar(
                                            section=option.section,
                                            concrete=concrete,
                                            stirrup_rebar=stirrup_rebar,
                                            Q=Q,
                                            diameters=(geometry_stirrup_diameter,),
                                            max_results=1,
                                        )
                                        transverse_cache[transverse_key] = transverse_options
                                    if not transverse_options:
                                        continue
                                    transverse_option = transverse_options[0]
                                    moment_service = service_moment_ratio * M
                                    crack_formation = (
                                        check_normal_crack_formation_rectangular(
                                            section=option.section,
                                            concrete=concrete,
                                            Mser=moment_service,
                                        )
                                    )
                                    crack_width = check_normal_crack_width_rectangular(
                                        section=option.section,
                                        concrete=concrete,
                                        rebar=rebar,
                                        Mser=moment_service,
                                        As=option.As,
                                        main_bar_diameter=option.diameter,
                                        crack_formation=crack_formation,
                                    )
                                    deflection = check_curvature_deflection_rectangular(
                                        section=option.section,
                                        concrete=concrete,
                                        rebar=rebar,
                                        Mser=moment_service,
                                        As=option.As,
                                        span=span,
                                        crack_formation=crack_formation,
                                    )
                                    protocol = build_calculation_protocol(
                                        input_data={},
                                        materials={},
                                        geometry={},
                                        reinforcement={},
                                        checks={
                                            "bending": option.bending,
                                            "shear": transverse_option.shear,
                                            "crack_formation": crack_formation,
                                            "crack_width": crack_width,
                                            "deflection": deflection,
                                        },
                                    )
                                    unsafe_row = (
                                        protocol.overall_status != "pass"
                                        or option.bending.utilization > 1.0
                                        or transverse_option.shear.utilization > 1.0
                                        or option.constructive.status != "pass"
                                        or transverse_option.constructive.status
                                        not in ("pass", "warning")
                                        or transverse_option.shear.intermediate_values[
                                            "transverse_reinforcement_countable"
                                        ]
                                        is not True
                                    )
                                    if unsafe_row:
                                        continue

                                    main_constructive_values = (
                                        option.constructive.intermediate_values
                                    )
                                    stirrup_constructive_values = (
                                        transverse_option.constructive.intermediate_values
                                    )
                                    stirrup_shear_values = (
                                        transverse_option.shear.intermediate_values
                                    )

                                    group_key = _build_group_key(
                                        element_type=element_type,
                                        b=b,
                                        h=h,
                                        concrete_class=concrete_class,
                                        rebar_class=rebar_class,
                                        stirrup_class=stirrup_class,
                                        load_duration=load_duration,
                                    )
                                    all_rows.append(
                                        DatasetCase(
                                            case_id="pending",
                                            group_key=group_key,
                                            element_type=element_type,
                                            b=b,
                                            h=h,
                                            cover=cover,
                                            h0=option.section.effective_depth(),
                                            geometry_stirrup_diameter=(
                                                geometry_stirrup_diameter
                                            ),
                                            concrete_class=concrete_class,
                                            rebar_class=rebar_class,
                                            stirrup_class=stirrup_class,
                                            local_axes_id=(
                                                option.bending.intermediate_values[
                                                    "local_axes_id"
                                                ]
                                            ),
                                            moment_axis=(
                                                option.bending.intermediate_values[
                                                    "moment_axis"
                                                ]
                                            ),
                                            tension_face=(
                                                option.bending.intermediate_values[
                                                    "tension_face"
                                                ]
                                            ),
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
                                            status=protocol.status,
                                            section_b_mm=b,
                                            section_h_mm=h,
                                            effective_depth_mm=(
                                                option.section.effective_depth()
                                            ),
                                            cover_mm=cover,
                                            main_bar_diameter_mm=option.diameter,
                                            stirrup_diameter_mm=transverse_option.diameter,
                                            stirrup_spacing_mm=transverse_option.spacing,
                                            main_rebar_class=rebar_class,
                                            stirrup_rebar_class=stirrup_class,
                                            moment_nmm=M,
                                            shear_n=Q,
                                            moment_service_nmm=moment_service,
                                            span_mm=span,
                                            longitudinal_as_mm2=option.As,
                                            transverse_asw_mm2=transverse_option.Asw,
                                            bending_mult_nmm=option.bending.Mult,
                                            shear_qult_n=transverse_option.shear.Qult,
                                            mcrc_nmm=crack_formation.Mcrc,
                                            crack_width_mm=crack_width.acrc,
                                            deflection_mm=deflection.deflection,
                                            bending_status=option.bending.status,
                                            shear_status=transverse_option.shear.status,
                                            crack_formation_status=crack_formation.status,
                                            crack_width_status=crack_width.status,
                                            deflection_status=deflection.status,
                                            strength_status=protocol.strength_status,
                                            serviceability_status=(
                                                protocol.serviceability_status
                                            ),
                                            overall_status=protocol.overall_status,
                                            completeness_status=(
                                                protocol.completeness_status
                                            ),
                                            evidence_status=protocol.evidence_status,
                                            project_use_status=protocol.project_use_status,
                                            project_use=protocol.project_use,
                                            warnings_count=len(protocol.warnings),
                                            requires_engineer_review=True,
                                            unsafe_row=unsafe_row,
                                            dataset_source=DATASET_SOURCE,
                                            sp63_core_version=__version__,
                                            dataset_version=DATASET_VERSION,
                                        )
                                    )
    return all_rows


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


def _normalize_geometry_stirrup_diameter(section_stirrup_diameter: float) -> int:
    diameter = int(section_stirrup_diameter)
    if (
        float(section_stirrup_diameter) != float(diameter)
        or diameter not in STIRRUP_DIAMETERS
    ):
        raise ValueError(
            "section_stirrup_diameter must be one of supported stirrup diameters "
            "for dataset MVP"
        )
    return diameter


def _build_group_key(
    *,
    element_type: str,
    b: float,
    h: float,
    concrete_class: str,
    rebar_class: str,
    stirrup_class: str,
    load_duration: str,
) -> str:
    return (
        f"{element_type}|b={b}|h={h}|concrete={concrete_class}|rebar={rebar_class}|"
        f"stirrup={stirrup_class}|duration={load_duration}"
    )
