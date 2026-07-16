"""Draft golden-case validation for the calculation core."""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.resources import files
from math import isfinite

from sp63_core.checks import (
    check_bending_rectangular,
    check_curvature_deflection_rectangular,
    check_normal_crack_formation_rectangular,
    check_normal_crack_width_rectangular,
    check_shear_rectangular,
)
from sp63_core.design import RectangularDesignInput, design_rectangular_element
from sp63_core.materials import area_by_diameter, get_concrete, get_rebar
from sp63_core.sections import RectangularBendingOrientation, RectangularSection

GoldenValue = float | str | bool | None
GOLDEN_BENDING_ORIENTATION = RectangularBendingOrientation(
    local_axes_id="golden-case-local-axes",
    moment_axis="local_z",
    tension_face="local_y_min",
)
STEP3_BENDING_BENCHMARK_RESOURCE = "data/uls_bend_rect_step3_benchmarks.json"


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
        orientation=GOLDEN_BENDING_ORIENTATION,
        load_duration="short",
    )
    failing = check_bending_rectangular(
        section=section,
        concrete=concrete,
        rebar=rebar,
        As=402.12,
        M=150_000_000,
        orientation=GOLDEN_BENDING_ORIENTATION,
        load_duration="short",
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


def run_step3_bending_benchmark_cases() -> tuple[GoldenCaseResult, ...]:
    """Run BMR-01--BMR-05 from the Step 3 provisional regression fixture.

    The fixture remains assumption-level evidence pending independent
    engineering reproduction. Loading it here makes the same five safety
    regressions part of both normal and acceptance ``validate --golden`` paths.
    """
    suite_text = (
        files("sp63_core.validation")
        .joinpath(STEP3_BENDING_BENCHMARK_RESOURCE)
        .read_text(encoding="utf-8")
    )
    suite = json.loads(suite_text)
    _validate_step3_benchmark_metadata(suite)
    orientation = RectangularBendingOrientation(**suite["orientation"])
    results: list[GoldenCaseResult] = []

    for case in suite["cases"]:
        input_data = case["input"]
        expected_fixture = case["expected"]
        section = RectangularSection(
            b=input_data["b"],
            h=input_data["h"],
            cover=input_data["cover"],
            stirrup_diameter=input_data["stirrup_diameter"],
            main_bar_diameter=input_data["main_bar_diameter"],
        )
        As = input_data["bar_count"] * area_by_diameter(
            input_data["main_bar_diameter"]
        )
        As_prime = 0.0
        if input_data["As_prime_bar_count"]:
            As_prime = input_data["As_prime_bar_count"] * area_by_diameter(
                input_data["As_prime_bar_diameter"]
            )
        bending = check_bending_rectangular(
            section=section,
            concrete=get_concrete(input_data["concrete_class"]),
            rebar=get_rebar(input_data["rebar_class"]),
            As=As,
            As_prime=As_prime,
            M=input_data["M"],
            orientation=orientation,
            load_duration=input_data["load_duration"],
        )

        expected: dict[str, GoldenValue] = {
            "h0": expected_fixture["h0"],
            "x": expected_fixture["x"],
            "xi": expected_fixture["xi"],
            "xi_R": expected_fixture["xi_R"],
            "x_limit": expected_fixture["x_limit"],
            "Mult": expected_fixture["Mult"],
            "utilization": expected_fixture["utilization"],
            "calculation_status": expected_fixture["status"],
            "capacity_applicable": expected_fixture["capacity_applicable"],
        }
        actual: dict[str, GoldenValue] = {
            "h0": section.effective_depth(),
            "x": bending.x,
            "xi": bending.xi,
            "xi_R": bending.xi_R,
            "x_limit": bending.intermediate_values["x_limit"],
            "Mult": bending.Mult,
            "utilization": bending.utilization,
            "calculation_status": bending.status,
            "capacity_applicable": bending.capacity_applicable,
        }
        for key in ("Rb_base", "gamma_b1", "Rb_effective", "applicability_reason"):
            if key in expected_fixture:
                expected[key] = expected_fixture[key]
                actual[key] = bending.intermediate_values.get(key)

        results.append(
            _build_result(
                case_id=case["case_id"],
                expected=expected,
                actual=actual,
                tolerances={
                    "h0": 1e-9,
                    "x": 1e-6,
                    "xi": 1e-9,
                    "xi_R": 1e-9,
                    "x_limit": 1e-6,
                    "Mult": 1e-3,
                    "utilization": 1e-9,
                    "Rb_base": 1e-9,
                    "gamma_b1": 1e-12,
                    "Rb_effective": 1e-9,
                },
                warnings=(
                    *bending.warnings,
                    "Step 3 BMR expected values are assumption-level until independent "
                    "engineering sign-off",
                ),
            )
        )

    return tuple(results)


def _validate_step3_benchmark_metadata(suite: Mapping[str, object]) -> None:
    """Reject benchmark resources that lose their assumption/review gates."""
    expected = {
        "decision_status": "ASSUMPTION",
        "completeness_status": "incomplete",
        "evidence_status": "needs_engineer_review",
        "project_use_status": "prohibited",
        "project_use": False,
        "requires_engineer_review": True,
    }
    invalid = [key for key, value in expected.items() if suite.get(key) != value]
    if invalid:
        raise ValueError(
            "Step 3 benchmark safety metadata is invalid: " + ", ".join(invalid)
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
            local_axes_id="golden-case-local-axes",
            moment_axis="local_z",
            tension_face="local_y_min",
            load_duration="short",
        )
    )
    protocol_status = "" if design.protocol is None else design.protocol.status
    protocol_strength_status = "" if design.protocol is None else design.protocol.strength_status
    protocol_serviceability_status = (
        "" if design.protocol is None else design.protocol.serviceability_status
    )
    protocol_overall_status = "" if design.protocol is None else design.protocol.overall_status
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
                "strength_status": "pass",
                "serviceability_status": "not_checked",
                "overall_status": "pass",
                "protocol_status": "pass",
                "protocol_strength_status": "pass",
                "protocol_serviceability_status": "not_checked",
                "protocol_overall_status": "pass",
                "bending_status": "pass",
                "shear_status": "pass",
            },
            actual={
                "design_status": design.status,
                "strength_status": design.strength_status,
                "serviceability_status": design.serviceability_status,
                "overall_status": design.overall_status,
                "protocol_status": protocol_status,
                "protocol_strength_status": protocol_strength_status,
                "protocol_serviceability_status": protocol_serviceability_status,
                "protocol_overall_status": protocol_overall_status,
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


def run_crack_width_golden_cases() -> tuple[GoldenCaseResult, ...]:
    """Run draft normal crack width golden cases."""
    section = _golden_section()
    concrete = get_concrete("B25")
    rebar = get_rebar("A500")
    Mser = 30_000_000.0
    As = 942.48
    acrc_limit = 0.3
    crack_width = check_normal_crack_width_rectangular(
        section=section,
        concrete=concrete,
        rebar=rebar,
        Mser=Mser,
        As=As,
        main_bar_diameter=20,
        acrc_limit=acrc_limit,
    )
    h0 = section.effective_depth()
    z = 0.9 * h0
    sigma_s = Mser / (As * z)
    epsilon_s = sigma_s / rebar.Es
    rho_eff = As / (section.b * h0)
    crack_spacing = min(max(0.5 * 20 / rho_eff, 100.0), 400.0)
    acrc = epsilon_s * crack_spacing
    return (
        _build_result(
            case_id="crack_width_rectangular_case_01",
            expected={
                "z": z,
                "sigma_s": sigma_s,
                "epsilon_s": epsilon_s,
                "rho_eff": rho_eff,
                "crack_spacing": crack_spacing,
                "acrc": acrc,
                "calculation_status": "pass" if acrc <= acrc_limit else "fail",
            },
            actual={
                "z": crack_width.intermediate_values["z"],
                "sigma_s": crack_width.sigma_s,
                "epsilon_s": crack_width.epsilon_s,
                "rho_eff": crack_width.intermediate_values["rho_eff"],
                "crack_spacing": crack_width.crack_spacing,
                "acrc": crack_width.acrc,
                "calculation_status": crack_width.status,
            },
            tolerances={
                "z": 0.001,
                "sigma_s": 0.001,
                "epsilon_s": 1e-9,
                "rho_eff": 1e-9,
                "crack_spacing": 0.001,
                "acrc": 1e-9,
            },
            warnings=crack_width.warnings,
        ),
    )


def run_deflection_golden_cases() -> tuple[GoldenCaseResult, ...]:
    """Run draft curvature and deflection golden cases."""
    section = _golden_section()
    concrete = get_concrete("B25")
    rebar = get_rebar("A500")
    Mser = 30_000_000.0
    As = 942.48
    span = 6000.0
    deflection_limit_ratio = 250.0
    deflection = check_curvature_deflection_rectangular(
        section=section,
        concrete=concrete,
        rebar=rebar,
        Mser=Mser,
        As=As,
        span=span,
        deflection_limit_ratio=deflection_limit_ratio,
        loading_scheme="simply_supported_uniform",
    )
    h0 = section.effective_depth()
    I_gross = section.b * section.h**3 / 12.0
    n = rebar.Es / concrete.Eb
    neutral_axis_x = _cracked_neutral_axis_depth(
        b=section.b,
        h0=h0,
        As=As,
        n=n,
    )
    I_cracked = section.b * neutral_axis_x**3 / 3.0 + n * As * (h0 - neutral_axis_x) ** 2
    I_eff = I_cracked
    curvature = Mser / (concrete.Eb * I_eff)
    deflection_value = 5.0 / 48.0 * curvature * span**2
    deflection_limit = span / deflection_limit_ratio
    return (
        _build_result(
            case_id="deflection_rectangular_case_01",
            expected={
                "I_gross": I_gross,
                "n": n,
                "neutral_axis_x": neutral_axis_x,
                "I_cracked": I_cracked,
                "I_eff": I_eff,
                "curvature": curvature,
                "deflection": deflection_value,
                "deflection_limit": deflection_limit,
                "calculation_status": "pass" if deflection_value <= deflection_limit else "fail",
            },
            actual={
                "I_gross": deflection.I_gross,
                "n": deflection.intermediate_values["n"],
                "neutral_axis_x": deflection.intermediate_values["neutral_axis_x"],
                "I_cracked": deflection.I_cracked,
                "I_eff": deflection.I_eff,
                "curvature": deflection.curvature,
                "deflection": deflection.deflection,
                "deflection_limit": deflection.deflection_limit,
                "calculation_status": deflection.status,
            },
            tolerances={
                "I_gross": 1.0,
                "n": 1e-9,
                "neutral_axis_x": 1e-6,
                "I_cracked": 1.0,
                "I_eff": 1.0,
                "curvature": 1e-12,
                "deflection": 1e-9,
                "deflection_limit": 1e-9,
            },
            warnings=deflection.warnings,
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


def _cracked_neutral_axis_depth(*, b: float, h0: float, As: float, n: float) -> float:
    a = 0.5 * b
    coefficient_b = n * As
    coefficient_c = -n * As * h0
    discriminant = coefficient_b**2 - 4.0 * a * coefficient_c
    return (-coefficient_b + discriminant**0.5) / (2.0 * a)


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
            actual_number = float(actual_value)
            if not isfinite(actual_number) or not isfinite(expected_value):
                return False
            if abs(actual_number - expected_value) > tolerances.get(key, 0.0):
                return False
        elif actual_value != expected_value:
            return False
    return True
