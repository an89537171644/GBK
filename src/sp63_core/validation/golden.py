"""Draft golden-case validation for the calculation core."""

from collections.abc import Mapping
from dataclasses import dataclass

from sp63_core.checks import (
    check_bending_rectangular,
    check_normal_crack_formation_rectangular,
    check_shear_rectangular,
)
from sp63_core.design import RectangularDesignInput, design_rectangular_element
from sp63_core.materials import area_by_diameter, get_concrete, get_rebar
from sp63_core.sections import RectangularSection

GoldenValue = float | str | bool


@dataclass(frozen=True)
class GoldenCaseResult:
    """One golden-case comparison result."""

    case_id: str
    status: str
    expected: dict[str, GoldenValue]
    actual: dict[str, GoldenValue]
    tolerances: dict[str, float]
    passed: bool
    warnings: tuple[str, ...]


def run_bending_golden_cases() -> tuple[GoldenCaseResult, ...]:
    """Run draft bending golden cases."""
    section = _golden_section()
    concrete = get_concrete("B25")
    rebar = get_rebar("A500")

    passing = check_bending_rectangular(
        section=section,
        concrete=concrete,
        rebar=rebar,
        As=942.48,
        M=150_000_000,
    )
    failing = check_bending_rectangular(
        section=section,
        concrete=concrete,
        rebar=rebar,
        As=402.12,
        M=150_000_000,
    )

    return (
        _build_result(
            case_id="bending_rectangular_case_01",
            expected={
                "x": 94.25,
                "xi": 0.209,
                "xi_R": 0.493,
                "Mult": 165_170_000.0,
                "utilization": 0.908,
                "calculation_status": "pass",
            },
            actual={
                "x": passing.x,
                "xi": passing.xi,
                "xi_R": passing.xi_R,
                "Mult": passing.Mult,
                "utilization": passing.utilization,
                "calculation_status": passing.status,
            },
            tolerances={
                "x": 0.05,
                "xi": 0.002,
                "xi_R": 0.002,
                "Mult": 200_000.0,
                "utilization": 0.003,
            },
            warnings=passing.warnings,
        ),
        _build_result(
            case_id="bending_rectangular_case_02",
            expected={
                "x": 40.21,
                "Mult": 75_200_000.0,
                "utilization": 1.995,
                "calculation_status": "fail",
            },
            actual={
                "x": failing.x,
                "Mult": failing.Mult,
                "utilization": failing.utilization,
                "calculation_status": failing.status,
            },
            tolerances={
                "x": 0.05,
                "Mult": 200_000.0,
                "utilization": 0.005,
            },
            warnings=failing.warnings,
        ),
    )


def run_shear_golden_cases() -> tuple[GoldenCaseResult, ...]:
    """Run draft shear golden cases."""
    shear = check_shear_rectangular(
        section=_golden_section(),
        concrete=get_concrete("B25"),
        stirrup_rebar=get_rebar("A240"),
        Q=80_000,
        Asw=2 * area_by_diameter(8),
        sw=200,
    )
    return (
        _build_result(
            case_id="shear_rectangular_case_01",
            expected={
                "qsw": 85.45,
                "Q_strip": 587_250.0,
                "Qb": 106_310.0,
                "Qsw": 57_680.0,
                "Qult": 163_990.0,
                "calculation_status": "pass",
            },
            actual={
                "qsw": shear.qsw,
                "Q_strip": shear.Q_strip,
                "Qb": shear.Qb,
                "Qsw": shear.Qsw,
                "Qult": shear.Qult,
                "calculation_status": shear.status,
            },
            tolerances={
                "qsw": 0.1,
                "Q_strip": 1.0,
                "Qb": 200.0,
                "Qsw": 200.0,
                "Qult": 300.0,
            },
            warnings=shear.warnings,
        ),
    )


def run_design_golden_cases() -> tuple[GoldenCaseResult, ...]:
    """Run draft end-to-end design golden cases."""
    design = design_rectangular_element(
        RectangularDesignInput(
            b=300,
            h=500,
            cover=32,
            stirrup_diameter_for_geometry=8,
            concrete_class="B25",
            longitudinal_rebar_class="A500",
            stirrup_rebar_class="A240",
            M=150_000_000,
            Q=80_000,
            load_duration="short",
        )
    )
    protocol_status = "" if design.protocol is None else design.protocol.status
    bending_status = (
        ""
        if design.selected_longitudinal is None
        else design.selected_longitudinal.bending.status
    )
    shear_status = (
        "" if design.selected_transverse is None else design.selected_transverse.shear.status
    )
    return (
        _build_result(
            case_id="design_rectangular_case_01",
            expected={
                "design_status": "pass",
                "protocol_status": "pass",
                "bending_status": "pass",
                "shear_status": "pass",
            },
            actual={
                "design_status": design.status,
                "protocol_status": protocol_status,
                "bending_status": bending_status,
                "shear_status": shear_status,
            },
            tolerances={},
            warnings=design.warnings,
        ),
    )


def run_crack_formation_golden_cases() -> tuple[GoldenCaseResult, ...]:
    """Run draft normal crack formation golden cases."""
    crack = check_normal_crack_formation_rectangular(
        section=_golden_section(),
        concrete=get_concrete("B25"),
        Mser=30_000_000,
    )
    return (
        _build_result(
            case_id="crack_formation_rectangular_case_01",
            expected={
                "W": 12_500_000.0,
                "Mcrc": 19_375_000.0,
                "utilization": 30_000_000 / 19_375_000,
                "calculation_status": "crack",
            },
            actual={
                "W": crack.intermediate_values["W"],
                "Mcrc": crack.Mcrc,
                "utilization": crack.utilization,
                "calculation_status": crack.status,
            },
            tolerances={
                "W": 1.0,
                "Mcrc": 1.0,
                "utilization": 0.001,
            },
            warnings=crack.warnings,
        ),
    )


def _golden_section() -> RectangularSection:
    return RectangularSection(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )


def _build_result(
    *,
    case_id: str,
    expected: dict[str, GoldenValue],
    actual: dict[str, GoldenValue],
    tolerances: dict[str, float],
    warnings: tuple[str, ...],
) -> GoldenCaseResult:
    passed = _matches_expected(expected=expected, actual=actual, tolerances=tolerances)
    return GoldenCaseResult(
        case_id=case_id,
        status="pass" if passed else "fail",
        expected=expected,
        actual=actual,
        tolerances=tolerances,
        passed=passed,
        warnings=warnings,
    )


def _matches_expected(
    *,
    expected: Mapping[str, GoldenValue],
    actual: Mapping[str, GoldenValue],
    tolerances: Mapping[str, float],
) -> bool:
    for key, expected_value in expected.items():
        if key not in actual:
            return False
        actual_value = actual[key]
        if isinstance(expected_value, float):
            if not isinstance(actual_value, float | int):
                return False
            if abs(float(actual_value) - expected_value) > tolerances.get(key, 0.0):
                return False
        elif actual_value != expected_value:
            return False
    return True
