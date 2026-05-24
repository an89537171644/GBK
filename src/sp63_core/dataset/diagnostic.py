"""Diagnostic dataset rows with pass, fail, and review cases."""

from collections import Counter
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from sp63_core.checks import (
    check_bending_rectangular,
    check_curvature_deflection_rectangular,
    check_normal_crack_formation_rectangular,
    check_normal_crack_width_rectangular,
    check_shear_rectangular,
)
from sp63_core.materials import area_by_diameter, get_concrete, get_rebar
from sp63_core.report import build_calculation_protocol
from sp63_core.sections import RectangularSection

DIAGNOSTIC_DATASET_SOURCE = "diagnostic_deterministic_sp63_core"
DIAGNOSTIC_REQUIRED_OVERALL_STATUSES = ("pass", "fail", "review_or_fail")
DIAGNOSTIC_MIN_CLASSIFICATION_ROWS = 30
_CANDIDATE_CASE_TYPES: tuple[str, ...] = (
    "pass_base",
    "bending_fail",
    "shear_fail",
    "crack_review_without_width",
    "crack_width_fail",
    "deflection_fail",
    "multiple_fail",
)


@dataclass(frozen=True)
class DiagnosticDatasetCase:
    """One deterministic diagnostic row for future ML classification datasets."""

    case_id: str
    case_type: str
    description: str
    section_b_mm: float
    section_h_mm: float
    effective_depth_mm: float
    cover_mm: float
    concrete_class: str
    main_rebar_class: str
    stirrup_rebar_class: str
    moment_nmm: float
    shear_n: float
    moment_service_nmm: float
    span_mm: float
    main_bar_count: int
    main_bar_diameter_mm: int
    stirrup_diameter_mm: int
    stirrup_legs: int
    stirrup_spacing_mm: int
    longitudinal_as_mm2: float
    transverse_asw_mm2: float
    bending_mult_nmm: float | None
    shear_qult_n: float | None
    mcrc_nmm: float | None
    crack_width_mm: float | None
    deflection_mm: float | None
    bending_status: str
    shear_status: str
    crack_formation_status: str
    crack_width_status: str
    deflection_status: str
    strength_status: str
    serviceability_status: str
    overall_status: str
    warnings_count: int
    warning_text: str
    failure_reason: str
    requires_engineer_review: bool
    dataset_source: str

    def as_row(self) -> dict[str, Any]:
        """Return a JSON/CSV-like diagnostic row."""
        return asdict(self)

    def as_readiness_row(self) -> dict[str, Any]:
        """Return a row compatible with the K22 ML readiness gate."""
        row = self.as_row()
        row["unsafe_row"] = self.overall_status != "pass"
        return row


def generate_diagnostic_dataset_cases(
    limit: int = 100,
) -> tuple[DiagnosticDatasetCase, ...]:
    """Generate deterministic diagnostic cases without changing the safe dataset."""
    if limit < 6:
        raise ValueError("limit must be at least 6 for diagnostic coverage")
    cases: list[DiagnosticDatasetCase] = [
        _pass_base_beam(),
        _bending_fail_low_as(),
        _crack_review_without_width(),
        _crack_width_fail(),
        _deflection_fail(),
        _shear_fail(),
    ]
    variant = 0
    while len(cases) < limit:
        case_type = _CANDIDATE_CASE_TYPES[(len(cases) - 6) % len(_CANDIDATE_CASE_TYPES)]
        if case_type == "pass_base":
            cases.append(_candidate_pass_base(len(cases) + 1, variant))
        elif case_type == "bending_fail":
            cases.append(_candidate_bending_fail(len(cases) + 1, variant))
        elif case_type == "shear_fail":
            cases.append(_candidate_shear_fail(len(cases) + 1, variant))
        elif case_type == "crack_review_without_width":
            cases.append(_candidate_crack_review_without_width(len(cases) + 1, variant))
        elif case_type == "crack_width_fail":
            cases.append(_candidate_crack_width_fail(len(cases) + 1, variant))
        elif case_type == "deflection_fail":
            cases.append(_candidate_deflection_fail(len(cases) + 1, variant))
        elif case_type == "multiple_fail":
            cases.append(_candidate_multiple_fail(len(cases) + 1, variant))
            variant += 1
    return tuple(cases[:limit])


def diagnostic_status_counts(
    cases: tuple[DiagnosticDatasetCase, ...],
) -> dict[str, dict[str, int]]:
    """Return status counts for diagnostic dataset rows."""
    return {
        "overall_status": dict(
            sorted(Counter(case.overall_status for case in cases).items())
        ),
        "strength_status": dict(
            sorted(Counter(case.strength_status for case in cases).items())
        ),
        "serviceability_status": dict(
            sorted(Counter(case.serviceability_status for case in cases).items())
        ),
        "failure_reason": dict(
            sorted(
                Counter(case.failure_reason for case in cases if case.failure_reason).items()
            )
        ),
    }


def diagnostic_dataset_warnings(
    cases: tuple[DiagnosticDatasetCase, ...],
) -> tuple[str, ...]:
    """Return warnings about diagnostic dataset coverage."""
    present = {case.overall_status for case in cases}
    missing = [
        status for status in DIAGNOSTIC_REQUIRED_OVERALL_STATUSES if status not in present
    ]
    if not missing:
        warnings = []
    else:
        warnings = [
            f"diagnostic dataset is missing overall_status values: {', '.join(missing)}"
        ]
    if len(cases) < DIAGNOSTIC_MIN_CLASSIFICATION_ROWS:
        warnings.append(
            "diagnostic dataset is small; classification metrics are smoke metrics only"
        )
    return tuple(warnings)


def _pass_base_beam() -> DiagnosticDatasetCase:
    section = _section(main_bar_diameter=20, stirrup_diameter=8)
    concrete = get_concrete("B25")
    rebar = get_rebar("A500")
    stirrup_rebar = get_rebar("A240")
    As = 3 * area_by_diameter(20)
    Asw = 2 * area_by_diameter(8)
    bending = check_bending_rectangular(section, concrete, rebar, As=As, M=150_000_000)
    shear = check_shear_rectangular(section, concrete, stirrup_rebar, Q=80_000, Asw=Asw, sw=200)
    crack = check_normal_crack_formation_rectangular(section, concrete, Mser=30_000_000)
    crack_width = check_normal_crack_width_rectangular(
        section,
        concrete,
        rebar,
        Mser=30_000_000,
        As=As,
        main_bar_diameter=20,
        crack_formation=crack,
    )
    deflection = check_curvature_deflection_rectangular(
        section,
        concrete,
        rebar,
        Mser=30_000_000,
        As=As,
        span=6000,
        crack_formation=crack,
    )
    return _build_case(
        case_id="diagnostic_case_01",
        case_type="pass_base_beam",
        description="Passing strength and draft serviceability case.",
        section=section,
        concrete_class="B25",
        main_rebar_class="A500",
        stirrup_rebar_class="A240",
        M=150_000_000,
        Q=80_000,
        Mser=30_000_000,
        span=6000,
        main_bar_count=3,
        main_bar_diameter=20,
        stirrup_diameter=8,
        stirrup_legs=2,
        stirrup_spacing=200,
        As=As,
        Asw=Asw,
        checks={
            "bending": bending,
            "shear": shear,
            "crack_formation": crack,
            "crack_width": crack_width,
            "deflection": deflection,
        },
        failure_reason="",
    )


def _bending_fail_low_as() -> DiagnosticDatasetCase:
    section = _section(main_bar_diameter=16, stirrup_diameter=8)
    concrete = get_concrete("B25")
    rebar = get_rebar("A500")
    As = 2 * area_by_diameter(16)
    bending = check_bending_rectangular(section, concrete, rebar, As=As, M=150_000_000)
    return _build_case(
        case_id="diagnostic_case_02",
        case_type="bending_fail_low_as",
        description="Insufficient longitudinal reinforcement fails bending.",
        section=section,
        concrete_class="B25",
        main_rebar_class="A500",
        stirrup_rebar_class="A240",
        M=150_000_000,
        Q=0.0,
        Mser=0.0,
        span=0.0,
        main_bar_count=2,
        main_bar_diameter=16,
        stirrup_diameter=8,
        stirrup_legs=2,
        stirrup_spacing=200,
        As=As,
        Asw=2 * area_by_diameter(8),
        checks={"bending": bending},
        failure_reason="bending capacity fails",
    )


def _crack_review_without_width() -> DiagnosticDatasetCase:
    section = _section(main_bar_diameter=20, stirrup_diameter=8)
    concrete = get_concrete("B25")
    rebar = get_rebar("A500")
    stirrup_rebar = get_rebar("A240")
    As = 3 * area_by_diameter(20)
    Asw = 2 * area_by_diameter(8)
    bending = check_bending_rectangular(section, concrete, rebar, As=As, M=150_000_000)
    shear = check_shear_rectangular(section, concrete, stirrup_rebar, Q=80_000, Asw=Asw, sw=200)
    crack = check_normal_crack_formation_rectangular(section, concrete, Mser=30_000_000)
    return _build_case(
        case_id="diagnostic_case_03",
        case_type="crack_review_without_width",
        description="Cracks are expected but crack width is intentionally not checked.",
        section=section,
        concrete_class="B25",
        main_rebar_class="A500",
        stirrup_rebar_class="A240",
        M=150_000_000,
        Q=80_000,
        Mser=30_000_000,
        span=6000,
        main_bar_count=3,
        main_bar_diameter=20,
        stirrup_diameter=8,
        stirrup_legs=2,
        stirrup_spacing=200,
        As=As,
        Asw=Asw,
        checks={"bending": bending, "shear": shear, "crack_formation": crack},
        failure_reason="normal cracks expected without crack width check",
    )


def _crack_width_fail() -> DiagnosticDatasetCase:
    section = _section(main_bar_diameter=16, stirrup_diameter=8)
    concrete = get_concrete("B25")
    rebar = get_rebar("A500")
    As = 2 * area_by_diameter(16)
    crack = check_normal_crack_formation_rectangular(section, concrete, Mser=90_000_000)
    crack_width = check_normal_crack_width_rectangular(
        section,
        concrete,
        rebar,
        Mser=90_000_000,
        As=As,
        main_bar_diameter=16,
        crack_formation=crack,
    )
    return _build_case(
        case_id="diagnostic_case_04",
        case_type="crack_width_fail",
        description="Small reinforcement and high service moment fail crack width.",
        section=section,
        concrete_class="B25",
        main_rebar_class="A500",
        stirrup_rebar_class="A240",
        M=0.0,
        Q=0.0,
        Mser=90_000_000,
        span=0.0,
        main_bar_count=2,
        main_bar_diameter=16,
        stirrup_diameter=8,
        stirrup_legs=2,
        stirrup_spacing=200,
        As=As,
        Asw=2 * area_by_diameter(8),
        checks={"crack_formation": crack, "crack_width": crack_width},
        failure_reason="crack width exceeds draft limit",
    )


def _deflection_fail() -> DiagnosticDatasetCase:
    section = _section(main_bar_diameter=16, stirrup_diameter=8)
    concrete = get_concrete("B25")
    rebar = get_rebar("A500")
    As = 2 * area_by_diameter(16)
    crack = check_normal_crack_formation_rectangular(section, concrete, Mser=80_000_000)
    deflection = check_curvature_deflection_rectangular(
        section,
        concrete,
        rebar,
        Mser=80_000_000,
        As=As,
        span=12_000,
        crack_formation=crack,
    )
    return _build_case(
        case_id="diagnostic_case_05",
        case_type="deflection_fail",
        description="Long span and high service moment fail draft deflection.",
        section=section,
        concrete_class="B25",
        main_rebar_class="A500",
        stirrup_rebar_class="A240",
        M=0.0,
        Q=0.0,
        Mser=80_000_000,
        span=12_000,
        main_bar_count=2,
        main_bar_diameter=16,
        stirrup_diameter=8,
        stirrup_legs=2,
        stirrup_spacing=200,
        As=As,
        Asw=2 * area_by_diameter(8),
        checks={"crack_formation": crack, "deflection": deflection},
        failure_reason="deflection exceeds draft limit",
    )


def _shear_fail() -> DiagnosticDatasetCase:
    section = _section(main_bar_diameter=20, stirrup_diameter=6)
    concrete = get_concrete("B25")
    stirrup_rebar = get_rebar("A240")
    Asw = 2 * area_by_diameter(6)
    shear = check_shear_rectangular(section, concrete, stirrup_rebar, Q=200_000, Asw=Asw, sw=300)
    return _build_case(
        case_id="diagnostic_case_06",
        case_type="shear_fail",
        description="Sparse D6 stirrups fail the draft shear check.",
        section=section,
        concrete_class="B25",
        main_rebar_class="A500",
        stirrup_rebar_class="A240",
        M=0.0,
        Q=200_000,
        Mser=0.0,
        span=0.0,
        main_bar_count=3,
        main_bar_diameter=20,
        stirrup_diameter=6,
        stirrup_legs=2,
        stirrup_spacing=300,
        As=3 * area_by_diameter(20),
        Asw=Asw,
        checks={"shear": shear},
        failure_reason="shear capacity fails",
    )


def _candidate_pass_base(index: int, variant: int) -> DiagnosticDatasetCase:
    b, h = _variant_section_dimensions(variant)
    main_bar_diameter = 20
    main_bar_count = 3
    stirrup_spacing = (150, 150, 200)[variant % 3]
    section = _section(
        b=b,
        h=h,
        main_bar_diameter=main_bar_diameter,
        stirrup_diameter=8,
    )
    concrete_class = _variant_concrete_class(variant)
    rebar_class = "A500"
    concrete = get_concrete(concrete_class)
    rebar = get_rebar(rebar_class)
    stirrup_rebar = get_rebar("A240")
    M = (45_000_000, 55_000_000, 65_000_000)[variant % 3]
    Q = (25_000, 35_000, 45_000)[variant % 3]
    Mser = 0.2 * M
    span = (4000, 4500, 5000)[variant % 3]
    As = main_bar_count * area_by_diameter(main_bar_diameter)
    Asw = 2 * area_by_diameter(8)
    bending = check_bending_rectangular(section, concrete, rebar, As=As, M=M)
    shear = check_shear_rectangular(
        section,
        concrete,
        stirrup_rebar,
        Q=Q,
        Asw=Asw,
        sw=stirrup_spacing,
    )
    crack = check_normal_crack_formation_rectangular(section, concrete, Mser=Mser)
    crack_width = check_normal_crack_width_rectangular(
        section,
        concrete,
        rebar,
        Mser=Mser,
        As=As,
        main_bar_diameter=main_bar_diameter,
        crack_formation=crack,
    )
    deflection = check_curvature_deflection_rectangular(
        section,
        concrete,
        rebar,
        Mser=Mser,
        As=As,
        span=span,
        crack_formation=crack,
    )
    return _build_case(
        case_id=_candidate_case_id(index),
        case_type="pass_base",
        description="Generated passing diagnostic beam candidate.",
        section=section,
        concrete_class=concrete_class,
        main_rebar_class=rebar_class,
        stirrup_rebar_class="A240",
        M=M,
        Q=Q,
        Mser=Mser,
        span=span,
        main_bar_count=main_bar_count,
        main_bar_diameter=main_bar_diameter,
        stirrup_diameter=8,
        stirrup_legs=2,
        stirrup_spacing=stirrup_spacing,
        As=As,
        Asw=Asw,
        checks={
            "bending": bending,
            "shear": shear,
            "crack_formation": crack,
            "crack_width": crack_width,
            "deflection": deflection,
        },
        failure_reason="",
    )


def _candidate_bending_fail(index: int, variant: int) -> DiagnosticDatasetCase:
    b, h = _variant_section_dimensions(variant)
    main_bar_diameter = (12, 14, 16)[variant % 3]
    section = _section(b=b, h=h, main_bar_diameter=main_bar_diameter, stirrup_diameter=8)
    concrete_class = _variant_concrete_class(variant)
    rebar_class = _variant_rebar_class(variant)
    concrete = get_concrete(concrete_class)
    rebar = get_rebar(rebar_class)
    M = (170_000_000, 190_000_000, 220_000_000)[variant % 3]
    As = 2 * area_by_diameter(main_bar_diameter)
    bending = check_bending_rectangular(section, concrete, rebar, As=As, M=M)
    return _build_case(
        case_id=_candidate_case_id(index),
        case_type="bending_fail",
        description="Generated diagnostic candidate with insufficient bending capacity.",
        section=section,
        concrete_class=concrete_class,
        main_rebar_class=rebar_class,
        stirrup_rebar_class="A240",
        M=M,
        Q=0.0,
        Mser=0.0,
        span=0.0,
        main_bar_count=2,
        main_bar_diameter=main_bar_diameter,
        stirrup_diameter=8,
        stirrup_legs=2,
        stirrup_spacing=200,
        As=As,
        Asw=2 * area_by_diameter(8),
        checks={"bending": bending},
        failure_reason="bending capacity fails",
    )


def _candidate_shear_fail(index: int, variant: int) -> DiagnosticDatasetCase:
    b, h = _variant_section_dimensions(variant)
    section = _section(b=b, h=h, main_bar_diameter=20, stirrup_diameter=6)
    concrete_class = _variant_concrete_class(variant)
    concrete = get_concrete(concrete_class)
    stirrup_rebar = get_rebar("A240")
    Q = (180_000, 210_000, 240_000)[variant % 3]
    stirrup_spacing = (300, 350, 400)[variant % 3]
    Asw = 2 * area_by_diameter(6)
    shear = check_shear_rectangular(
        section,
        concrete,
        stirrup_rebar,
        Q=Q,
        Asw=Asw,
        sw=stirrup_spacing,
    )
    return _build_case(
        case_id=_candidate_case_id(index),
        case_type="shear_fail",
        description="Generated diagnostic candidate with insufficient shear capacity.",
        section=section,
        concrete_class=concrete_class,
        main_rebar_class="A500",
        stirrup_rebar_class="A240",
        M=0.0,
        Q=Q,
        Mser=0.0,
        span=0.0,
        main_bar_count=3,
        main_bar_diameter=20,
        stirrup_diameter=6,
        stirrup_legs=2,
        stirrup_spacing=stirrup_spacing,
        As=3 * area_by_diameter(20),
        Asw=Asw,
        checks={"shear": shear},
        failure_reason="shear capacity fails",
    )


def _candidate_crack_review_without_width(
    index: int,
    variant: int,
) -> DiagnosticDatasetCase:
    b, h = _variant_section_dimensions(variant)
    section = _section(b=b, h=h, main_bar_diameter=20, stirrup_diameter=8)
    concrete_class = _variant_concrete_class(variant)
    rebar_class = _variant_rebar_class(variant)
    concrete = get_concrete(concrete_class)
    rebar = get_rebar(rebar_class)
    stirrup_rebar = get_rebar("A240")
    M = (90_000_000, 110_000_000, 130_000_000)[variant % 3]
    Q = (40_000, 55_000, 70_000)[variant % 3]
    Mser = max(30_000_000, 0.35 * M)
    As = 4 * area_by_diameter(20)
    Asw = 2 * area_by_diameter(8)
    bending = check_bending_rectangular(section, concrete, rebar, As=As, M=M)
    shear = check_shear_rectangular(section, concrete, stirrup_rebar, Q=Q, Asw=Asw, sw=200)
    crack = check_normal_crack_formation_rectangular(section, concrete, Mser=Mser)
    return _build_case(
        case_id=_candidate_case_id(index),
        case_type="crack_review_without_width",
        description="Generated diagnostic candidate with cracks but no crack-width check.",
        section=section,
        concrete_class=concrete_class,
        main_rebar_class=rebar_class,
        stirrup_rebar_class="A240",
        M=M,
        Q=Q,
        Mser=Mser,
        span=6000,
        main_bar_count=4,
        main_bar_diameter=20,
        stirrup_diameter=8,
        stirrup_legs=2,
        stirrup_spacing=200,
        As=As,
        Asw=Asw,
        checks={"bending": bending, "shear": shear, "crack_formation": crack},
        failure_reason="normal cracks expected without crack width check",
    )


def _candidate_crack_width_fail(index: int, variant: int) -> DiagnosticDatasetCase:
    b, h = _variant_section_dimensions(variant)
    main_bar_diameter = (12, 14, 16)[variant % 3]
    section = _section(b=b, h=h, main_bar_diameter=main_bar_diameter, stirrup_diameter=8)
    concrete_class = _variant_concrete_class(variant)
    rebar_class = _variant_rebar_class(variant)
    concrete = get_concrete(concrete_class)
    rebar = get_rebar(rebar_class)
    Mser = (70_000_000, 85_000_000, 100_000_000)[variant % 3]
    As = 2 * area_by_diameter(main_bar_diameter)
    crack = check_normal_crack_formation_rectangular(section, concrete, Mser=Mser)
    crack_width = check_normal_crack_width_rectangular(
        section,
        concrete,
        rebar,
        Mser=Mser,
        As=As,
        main_bar_diameter=main_bar_diameter,
        crack_formation=crack,
    )
    return _build_case(
        case_id=_candidate_case_id(index),
        case_type="crack_width_fail",
        description="Generated diagnostic candidate with crack-width failure.",
        section=section,
        concrete_class=concrete_class,
        main_rebar_class=rebar_class,
        stirrup_rebar_class="A240",
        M=0.0,
        Q=0.0,
        Mser=Mser,
        span=0.0,
        main_bar_count=2,
        main_bar_diameter=main_bar_diameter,
        stirrup_diameter=8,
        stirrup_legs=2,
        stirrup_spacing=200,
        As=As,
        Asw=2 * area_by_diameter(8),
        checks={"crack_formation": crack, "crack_width": crack_width},
        failure_reason="crack width exceeds draft limit",
    )


def _candidate_deflection_fail(index: int, variant: int) -> DiagnosticDatasetCase:
    b, h = _variant_section_dimensions(variant)
    main_bar_diameter = (14, 16, 18)[variant % 3]
    section = _section(b=b, h=h, main_bar_diameter=main_bar_diameter, stirrup_diameter=8)
    concrete_class = _variant_concrete_class(variant)
    rebar_class = _variant_rebar_class(variant)
    concrete = get_concrete(concrete_class)
    rebar = get_rebar(rebar_class)
    Mser = (65_000_000, 80_000_000, 95_000_000)[variant % 3]
    span = (11_000, 12_000, 13_000)[variant % 3]
    As = 2 * area_by_diameter(main_bar_diameter)
    crack = check_normal_crack_formation_rectangular(section, concrete, Mser=Mser)
    deflection = check_curvature_deflection_rectangular(
        section,
        concrete,
        rebar,
        Mser=Mser,
        As=As,
        span=span,
        crack_formation=crack,
    )
    return _build_case(
        case_id=_candidate_case_id(index),
        case_type="deflection_fail",
        description="Generated diagnostic candidate with deflection failure.",
        section=section,
        concrete_class=concrete_class,
        main_rebar_class=rebar_class,
        stirrup_rebar_class="A240",
        M=0.0,
        Q=0.0,
        Mser=Mser,
        span=span,
        main_bar_count=2,
        main_bar_diameter=main_bar_diameter,
        stirrup_diameter=8,
        stirrup_legs=2,
        stirrup_spacing=200,
        As=As,
        Asw=2 * area_by_diameter(8),
        checks={"crack_formation": crack, "deflection": deflection},
        failure_reason="deflection exceeds draft limit",
    )


def _candidate_multiple_fail(index: int, variant: int) -> DiagnosticDatasetCase:
    b, h = _variant_section_dimensions(variant)
    main_bar_diameter = (12, 14, 16)[variant % 3]
    section = _section(b=b, h=h, main_bar_diameter=main_bar_diameter, stirrup_diameter=6)
    concrete_class = _variant_concrete_class(variant)
    rebar_class = _variant_rebar_class(variant)
    concrete = get_concrete(concrete_class)
    rebar = get_rebar(rebar_class)
    stirrup_rebar = get_rebar("A240")
    M = (180_000_000, 210_000_000, 240_000_000)[variant % 3]
    Q = (190_000, 220_000, 250_000)[variant % 3]
    Mser = (75_000_000, 90_000_000, 105_000_000)[variant % 3]
    span = (11_000, 12_000, 13_000)[variant % 3]
    As = 2 * area_by_diameter(main_bar_diameter)
    Asw = 2 * area_by_diameter(6)
    bending = check_bending_rectangular(section, concrete, rebar, As=As, M=M)
    shear = check_shear_rectangular(section, concrete, stirrup_rebar, Q=Q, Asw=Asw, sw=350)
    crack = check_normal_crack_formation_rectangular(section, concrete, Mser=Mser)
    crack_width = check_normal_crack_width_rectangular(
        section,
        concrete,
        rebar,
        Mser=Mser,
        As=As,
        main_bar_diameter=main_bar_diameter,
        crack_formation=crack,
    )
    deflection = check_curvature_deflection_rectangular(
        section,
        concrete,
        rebar,
        Mser=Mser,
        As=As,
        span=span,
        crack_formation=crack,
    )
    return _build_case(
        case_id=_candidate_case_id(index),
        case_type="multiple_fail",
        description="Generated diagnostic candidate with multiple deterministic failures.",
        section=section,
        concrete_class=concrete_class,
        main_rebar_class=rebar_class,
        stirrup_rebar_class="A240",
        M=M,
        Q=Q,
        Mser=Mser,
        span=span,
        main_bar_count=2,
        main_bar_diameter=main_bar_diameter,
        stirrup_diameter=6,
        stirrup_legs=2,
        stirrup_spacing=350,
        As=As,
        Asw=Asw,
        checks={
            "bending": bending,
            "shear": shear,
            "crack_formation": crack,
            "crack_width": crack_width,
            "deflection": deflection,
        },
        failure_reason="multiple deterministic checks fail",
    )


def _build_case(
    *,
    case_id: str,
    case_type: str,
    description: str,
    section: RectangularSection,
    concrete_class: str,
    main_rebar_class: str,
    stirrup_rebar_class: str,
    M: float,
    Q: float,
    Mser: float,
    span: float,
    main_bar_count: int,
    main_bar_diameter: int,
    stirrup_diameter: int,
    stirrup_legs: int,
    stirrup_spacing: int,
    As: float,
    Asw: float,
    checks: Mapping[str, Any],
    failure_reason: str,
) -> DiagnosticDatasetCase:
    protocol = build_calculation_protocol(
        input_data={},
        materials={},
        geometry={},
        reinforcement={},
        checks=checks,
    )
    return DiagnosticDatasetCase(
        case_id=case_id,
        case_type=case_type,
        description=description,
        section_b_mm=section.b,
        section_h_mm=section.h,
        effective_depth_mm=section.effective_depth(),
        cover_mm=section.cover,
        concrete_class=concrete_class,
        main_rebar_class=main_rebar_class,
        stirrup_rebar_class=stirrup_rebar_class,
        moment_nmm=M,
        shear_n=Q,
        moment_service_nmm=Mser,
        span_mm=span,
        main_bar_count=main_bar_count,
        main_bar_diameter_mm=main_bar_diameter,
        stirrup_diameter_mm=stirrup_diameter,
        stirrup_legs=stirrup_legs,
        stirrup_spacing_mm=stirrup_spacing,
        longitudinal_as_mm2=As,
        transverse_asw_mm2=Asw,
        bending_mult_nmm=_value(checks, "bending", "Mult"),
        shear_qult_n=_value(checks, "shear", "Qult"),
        mcrc_nmm=_value(checks, "crack_formation", "Mcrc"),
        crack_width_mm=_value(checks, "crack_width", "acrc"),
        deflection_mm=_value(checks, "deflection", "deflection"),
        bending_status=_status(checks, "bending"),
        shear_status=_status(checks, "shear"),
        crack_formation_status=_status(checks, "crack_formation"),
        crack_width_status=_status(checks, "crack_width"),
        deflection_status=_status(checks, "deflection"),
        strength_status=protocol.strength_status,
        serviceability_status=protocol.serviceability_status,
        overall_status=protocol.overall_status,
        warnings_count=len(protocol.warnings),
        warning_text=" | ".join(protocol.warnings),
        failure_reason=failure_reason,
        requires_engineer_review=True,
        dataset_source=DIAGNOSTIC_DATASET_SOURCE,
    )


def _candidate_case_id(index: int) -> str:
    return f"diagnostic_case_{index:03d}"


def _variant_section_dimensions(variant: int) -> tuple[float, float]:
    dimensions = (
        (250.0, 450.0),
        (300.0, 500.0),
        (350.0, 550.0),
        (400.0, 600.0),
    )
    return dimensions[variant % len(dimensions)]


def _variant_concrete_class(variant: int) -> str:
    return ("B20", "B25", "B30", "B35")[variant % 4]


def _variant_rebar_class(variant: int) -> str:
    return ("A400", "A500")[variant % 2]


def _section(
    *,
    main_bar_diameter: float,
    stirrup_diameter: float,
    b: float = 300.0,
    h: float = 500.0,
    cover: float = 32.0,
) -> RectangularSection:
    return RectangularSection(
        b=b,
        h=h,
        cover=cover,
        stirrup_diameter=stirrup_diameter,
        main_bar_diameter=main_bar_diameter,
    )


def _status(checks: Mapping[str, Any], check_name: str) -> str:
    check = checks.get(check_name)
    return "not_checked" if check is None else str(check.status)


def _value(checks: Mapping[str, Any], check_name: str, attr_name: str) -> float | None:
    check = checks.get(check_name)
    if check is None:
        return None
    value = getattr(check, attr_name)
    return float(value)
