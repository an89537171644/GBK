"""Manual SP63 verification cases for the deterministic draft core."""

from collections.abc import Mapping
from dataclasses import dataclass
from math import pi
from typing import Any

from sp63_core.checks import (
    check_bending_rectangular,
    check_curvature_deflection_rectangular,
    check_normal_crack_formation_rectangular,
    check_normal_crack_width_rectangular,
    check_shear_rectangular,
)
from sp63_core.materials import get_concrete, get_rebar
from sp63_core.report import build_calculation_protocol
from sp63_core.sections import RectangularSection

ManualValue = float | str | bool


@dataclass(frozen=True)
class ManualVerificationCase:
    """Manual verification case definition."""

    case_id: str
    title: str
    description: str
    inputs: dict[str, Any]
    expected_values: dict[str, ManualValue]
    tolerances: dict[str, float]
    expected_statuses: dict[str, str]
    source_note: str
    requires_engineer_review: bool = True


@dataclass(frozen=True)
class ManualVerificationResult:
    """Manual verification case comparison result."""

    case_id: str
    title: str
    status: str
    passed: bool
    expected_values: dict[str, ManualValue]
    actual_values: dict[str, ManualValue]
    tolerances: dict[str, float]
    expected_statuses: dict[str, str]
    actual_statuses: dict[str, str]
    warnings: tuple[str, ...]
    source_note: str
    requires_engineer_review: bool = True


SOURCE_NOTE = (
    "Manual SP63 verification cases K20; draft MVP values require engineer review"
)


def run_manual_verification_cases() -> tuple[ManualVerificationResult, ...]:
    """Run all manual SP63 verification cases against the current program core."""
    cases_and_actuals = (
        _case_01(),
        _case_02(),
        _case_03(),
        _case_04(),
        _case_05(),
        _case_06(),
    )
    return tuple(
        _build_result(case, actual_values, actual_statuses, warnings)
        for case, actual_values, actual_statuses, warnings in cases_and_actuals
    )


def _case_01() -> tuple[
    ManualVerificationCase,
    dict[str, ManualValue],
    dict[str, str],
    tuple[str, ...],
]:
    section = _section(main_bar_diameter=20)
    concrete = get_concrete("B25")
    rebar = get_rebar("A500")
    stirrup_rebar = get_rebar("A240")
    As = 942.48
    Asw = 2.0 * pi * 8.0**2 / 4.0

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
    )
    deflection = check_curvature_deflection_rectangular(
        section,
        concrete,
        rebar,
        Mser=30_000_000,
        As=As,
        span=6000,
        deflection_limit_ratio=250,
    )
    protocol = build_calculation_protocol(
        input_data={},
        materials={},
        geometry={},
        reinforcement={},
        checks={
            "bending": bending,
            "shear": shear,
            "crack_formation": crack,
            "crack_width": crack_width,
            "deflection": deflection,
        },
    )
    case = ManualVerificationCase(
        case_id="manual_case_01",
        title="Basic passing rectangular beam",
        description="Passing strength and serviceability case with 3D20 and D8/200 stirrups.",
        inputs={
            "b": 300,
            "h": 500,
            "cover": 32,
            "stirrup_diameter": 8,
            "main_bar_diameter": 20,
            "concrete": "B25",
            "rebar": "A500",
            "stirrup_rebar": "A240",
            "As": As,
            "Asw": Asw,
            "M": 150_000_000,
            "Q": 80_000,
            "Mser": 30_000_000,
            "span": 6000,
        },
        expected_values={
            "h0": 450.0,
            "bending_x": 94.25,
            "bending_xi": 0.209,
            "bending_xi_R": 0.493,
            "bending_Mult_kNm": 165.17,
            "bending_utilization": 0.908,
            "shear_Qult_kN": 163.99,
            "shear_utilization": 0.488,
            "Mcrc_kNm": 19.375,
            "crack_width_acrc": 0.157,
            "deflection": 4.38,
        },
        tolerances={
            "h0": 1e-9,
            "bending_x": 0.5,
            "bending_xi": 0.002,
            "bending_xi_R": 0.002,
            "bending_Mult_kNm": 1.7,
            "bending_utilization": 0.01,
            "shear_Qult_kN": 1.7,
            "shear_utilization": 0.01,
            "Mcrc_kNm": 0.2,
            "crack_width_acrc": 0.005,
            "deflection": 0.05,
        },
        expected_statuses={
            "bending_status": "pass",
            "shear_status": "pass",
            "crack_formation_status": "crack",
            "crack_width_status": "pass",
            "deflection_status": "pass",
            "strength_status": "pass",
            "serviceability_status": "pass",
            "overall_status": "pass",
        },
        source_note=SOURCE_NOTE,
    )
    actual_values: dict[str, ManualValue] = {
        "h0": section.effective_depth(),
        "bending_x": bending.x,
        "bending_xi": bending.xi,
        "bending_xi_R": bending.xi_R,
        "bending_Mult_kNm": bending.Mult / 1_000_000.0,
        "bending_utilization": bending.utilization,
        "shear_Qult_kN": shear.Qult / 1000.0,
        "shear_utilization": shear.utilization,
        "Mcrc_kNm": crack.Mcrc / 1_000_000.0,
        "crack_width_acrc": crack_width.acrc,
        "deflection": deflection.deflection,
    }
    actual_statuses = {
        "bending_status": bending.status,
        "shear_status": shear.status,
        "crack_formation_status": crack.status,
        "crack_width_status": crack_width.status,
        "deflection_status": deflection.status,
        "strength_status": protocol.strength_status,
        "serviceability_status": protocol.serviceability_status,
        "overall_status": protocol.overall_status,
    }
    return case, actual_values, actual_statuses, protocol.warnings


def _case_02() -> tuple[
    ManualVerificationCase,
    dict[str, ManualValue],
    dict[str, str],
    tuple[str, ...],
]:
    section = _section(main_bar_diameter=16)
    bending = check_bending_rectangular(
        section,
        get_concrete("B25"),
        get_rebar("A500"),
        As=402.12,
        M=150_000_000,
    )
    protocol = build_calculation_protocol(
        input_data={},
        materials={},
        geometry={},
        reinforcement={},
        checks={"bending": bending},
    )
    case = ManualVerificationCase(
        case_id="manual_case_02",
        title="Bending failure from insufficient longitudinal reinforcement",
        description="2D16 reinforcement does not pass the bending capacity check.",
        inputs={"As": 402.12, "M": 150_000_000, "main_bar_diameter": 16},
        expected_values={
            "h0": 452.0,
            "bending_x": 40.21,
            "bending_Mult_kNm": 75.55,
            "bending_utilization": 1.985,
        },
        tolerances={
            "h0": 1e-9,
            "bending_x": 0.3,
            "bending_Mult_kNm": 0.8,
            "bending_utilization": 0.02,
        },
        expected_statuses={
            "bending_status": "fail",
            "strength_status": "fail",
            "serviceability_status": "not_checked",
            "overall_status": "fail",
        },
        source_note=SOURCE_NOTE,
    )
    actual_values: dict[str, ManualValue] = {
        "h0": section.effective_depth(),
        "bending_x": bending.x,
        "bending_Mult_kNm": bending.Mult / 1_000_000.0,
        "bending_utilization": bending.utilization,
    }
    actual_statuses = {
        "bending_status": bending.status,
        "strength_status": protocol.strength_status,
        "serviceability_status": protocol.serviceability_status,
        "overall_status": protocol.overall_status,
    }
    return case, actual_values, actual_statuses, protocol.warnings


def _case_03() -> tuple[
    ManualVerificationCase,
    dict[str, ManualValue],
    dict[str, str],
    tuple[str, ...],
]:
    section = _section(main_bar_diameter=20)
    concrete = get_concrete("B25")
    rebar = get_rebar("A500")
    stirrup_rebar = get_rebar("A240")
    bending = check_bending_rectangular(section, concrete, rebar, As=942.48, M=150_000_000)
    shear = check_shear_rectangular(
        section,
        concrete,
        stirrup_rebar,
        Q=80_000,
        Asw=2.0 * pi * 8.0**2 / 4.0,
        sw=200,
    )
    crack = check_normal_crack_formation_rectangular(section, concrete, Mser=30_000_000)
    protocol = build_calculation_protocol(
        input_data={},
        materials={},
        geometry={},
        reinforcement={},
        checks={"bending": bending, "shear": shear, "crack_formation": crack},
    )
    case = ManualVerificationCase(
        case_id="manual_case_03",
        title="Cracks expected but crack width is not checked",
        description=(
            "Strength passes, crack formation returns crack, and serviceability needs review."
        ),
        inputs={"Mser": 30_000_000, "check_crack_width": False},
        expected_values={"Mcrc_kNm": 19.375, "crack_warning_present": True},
        tolerances={"Mcrc_kNm": 0.2},
        expected_statuses={
            "crack_formation_status": "crack",
            "strength_status": "pass",
            "serviceability_status": "review_or_fail",
            "overall_status": "review_or_fail",
        },
        source_note=SOURCE_NOTE,
    )
    actual_values: dict[str, ManualValue] = {
        "Mcrc_kNm": crack.Mcrc / 1_000_000.0,
        "crack_warning_present": any(
            "crack width check is required" in warning for warning in crack.warnings
        ),
    }
    actual_statuses = {
        "crack_formation_status": crack.status,
        "strength_status": protocol.strength_status,
        "serviceability_status": protocol.serviceability_status,
        "overall_status": protocol.overall_status,
    }
    return case, actual_values, actual_statuses, protocol.warnings


def _case_04() -> tuple[
    ManualVerificationCase,
    dict[str, ManualValue],
    dict[str, str],
    tuple[str, ...],
]:
    section = _section(main_bar_diameter=16)
    concrete = get_concrete("B25")
    rebar = get_rebar("A500")
    crack = check_normal_crack_formation_rectangular(section, concrete, Mser=90_000_000)
    crack_width = check_normal_crack_width_rectangular(
        section,
        concrete,
        rebar,
        Mser=90_000_000,
        As=402.12,
        main_bar_diameter=16,
    )
    protocol = build_calculation_protocol(
        input_data={},
        materials={},
        geometry={},
        reinforcement={},
        checks={"crack_formation": crack, "crack_width": crack_width},
    )
    case = ManualVerificationCase(
        case_id="manual_case_04",
        title="Crack width failure",
        description=(
            "Small reinforcement and high service moment exceed the draft crack width limit."
        ),
        inputs={"As": 402.12, "Mser": 90_000_000, "main_bar_diameter": 16},
        expected_values={
            "sigma_s": 550.18,
            "acrc": 1.100,
            "utilization": 3.668,
            "Rsser_warning_present": True,
            "crack_width_warning_present": True,
        },
        tolerances={"sigma_s": 6.0, "acrc": 0.005, "utilization": 0.05},
        expected_statuses={
            "crack_width_status": "fail",
            "strength_status": "not_checked",
            "serviceability_status": "fail",
            "overall_status": "fail",
        },
        source_note=SOURCE_NOTE,
    )
    actual_values: dict[str, ManualValue] = {
        "sigma_s": crack_width.sigma_s,
        "acrc": crack_width.acrc,
        "utilization": crack_width.utilization,
        "Rsser_warning_present": any("Rsser" in warning for warning in crack_width.warnings),
        "crack_width_warning_present": any(
            "crack width exceeds draft limit" in warning for warning in crack_width.warnings
        ),
    }
    actual_statuses = {
        "crack_width_status": crack_width.status,
        "strength_status": protocol.strength_status,
        "serviceability_status": protocol.serviceability_status,
        "overall_status": protocol.overall_status,
    }
    return case, actual_values, actual_statuses, protocol.warnings


def _case_05() -> tuple[
    ManualVerificationCase,
    dict[str, ManualValue],
    dict[str, str],
    tuple[str, ...],
]:
    section = _section(main_bar_diameter=16)
    concrete = get_concrete("B25")
    rebar = get_rebar("A500")
    crack = check_normal_crack_formation_rectangular(section, concrete, Mser=80_000_000)
    deflection = check_curvature_deflection_rectangular(
        section,
        concrete,
        rebar,
        Mser=80_000_000,
        As=402.12,
        span=12_000,
        deflection_limit_ratio=250,
        crack_formation=crack,
    )
    protocol = build_calculation_protocol(
        input_data={},
        materials={},
        geometry={},
        reinforcement={},
        checks={"crack_formation": crack, "deflection": deflection},
    )
    case = ManualVerificationCase(
        case_id="manual_case_05",
        title="Deflection failure",
        description=(
            "Small reinforcement, high service moment, and long span exceed draft "
            "deflection limit."
        ),
        inputs={"As": 402.12, "Mser": 80_000_000, "span": 12_000, "main_bar_diameter": 16},
        expected_values={
            "I_cracked": 422_131_603.0,
            "deflection": 94.76,
            "utilization": 1.974,
            "deflection_warning_present": True,
        },
        tolerances={"I_cracked": 4_300_000.0, "deflection": 0.05, "utilization": 0.02},
        expected_statuses={
            "deflection_status": "fail",
            "strength_status": "not_checked",
            "serviceability_status": "fail",
            "overall_status": "fail",
        },
        source_note=SOURCE_NOTE,
    )
    actual_values: dict[str, ManualValue] = {
        "I_cracked": deflection.I_cracked,
        "deflection": deflection.deflection,
        "utilization": deflection.utilization,
        "deflection_warning_present": any(
            "deflection exceeds draft limit" in warning for warning in deflection.warnings
        ),
    }
    actual_statuses = {
        "deflection_status": deflection.status,
        "strength_status": protocol.strength_status,
        "serviceability_status": protocol.serviceability_status,
        "overall_status": protocol.overall_status,
    }
    return case, actual_values, actual_statuses, protocol.warnings


def _case_06() -> tuple[
    ManualVerificationCase,
    dict[str, ManualValue],
    dict[str, str],
    tuple[str, ...],
]:
    section = _section(main_bar_diameter=20)
    shear = check_shear_rectangular(
        section,
        get_concrete("B25"),
        get_rebar("A240"),
        Q=200_000,
        Asw=2.0 * pi * 6.0**2 / 4.0,
        sw=300,
    )
    protocol = build_calculation_protocol(
        input_data={},
        materials={},
        geometry={},
        reinforcement={},
        checks={"shear": shear},
    )
    case = ManualVerificationCase(
        case_id="manual_case_06",
        title="Shear failure",
        description="D6/300 stirrups do not pass the draft shear check for Q = 200 kN.",
        inputs={"Q": 200_000, "Asw": 2.0 * pi * 6.0**2 / 4.0, "sw": 300},
        expected_values={
            "Asw": 56.55,
            "qsw": 32.04,
            "Qult_kN": 127.94,
            "utilization": 1.563,
            "qsw_warning_present": True,
        },
        tolerances={"Asw": 0.01, "qsw": 0.4, "Qult_kN": 1.3, "utilization": 0.02},
        expected_statuses={
            "shear_status": "fail",
            "strength_status": "fail",
            "serviceability_status": "not_checked",
            "overall_status": "fail",
        },
        source_note=SOURCE_NOTE,
    )
    actual_values: dict[str, ManualValue] = {
        "Asw": 2.0 * pi * 6.0**2 / 4.0,
        "qsw": shear.qsw,
        "Qult_kN": shear.Qult / 1000.0,
        "utilization": shear.utilization,
        "qsw_warning_present": any("qsw is below" in warning for warning in shear.warnings),
    }
    actual_statuses = {
        "shear_status": shear.status,
        "strength_status": protocol.strength_status,
        "serviceability_status": protocol.serviceability_status,
        "overall_status": protocol.overall_status,
    }
    return case, actual_values, actual_statuses, protocol.warnings


def _build_result(
    case: ManualVerificationCase,
    actual_values: dict[str, ManualValue],
    actual_statuses: dict[str, str],
    warnings: tuple[str, ...],
) -> ManualVerificationResult:
    values_passed = _values_match(
        expected=case.expected_values,
        actual=actual_values,
        tolerances=case.tolerances,
    )
    statuses_passed = all(
        actual_statuses.get(name) == expected
        for name, expected in case.expected_statuses.items()
    )
    passed = values_passed and statuses_passed
    return ManualVerificationResult(
        case_id=case.case_id,
        title=case.title,
        status="pass" if passed else "fail",
        passed=passed,
        expected_values=case.expected_values,
        actual_values=actual_values,
        tolerances=case.tolerances,
        expected_statuses=case.expected_statuses,
        actual_statuses=actual_statuses,
        warnings=warnings,
        source_note=case.source_note,
        requires_engineer_review=True,
    )


def _values_match(
    *,
    expected: Mapping[str, ManualValue],
    actual: Mapping[str, ManualValue],
    tolerances: Mapping[str, float],
) -> bool:
    for name, expected_value in expected.items():
        if name not in actual:
            return False
        actual_value = actual[name]
        if isinstance(expected_value, float):
            if not isinstance(actual_value, float | int):
                return False
            if abs(float(actual_value) - expected_value) > tolerances.get(name, 0.0):
                return False
        elif actual_value != expected_value:
            return False
    return True


def _section(*, main_bar_diameter: float) -> RectangularSection:
    return RectangularSection(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter=8,
        main_bar_diameter=main_bar_diameter,
    )
