from inspect import signature

import pytest

from sp63_core.checks import check_bending_rectangular
from sp63_core.materials import area_by_diameter, get_concrete, get_rebar
from sp63_core.sections import RectangularBendingOrientation, RectangularSection

ORIENTATION = RectangularBendingOrientation(
    local_axes_id="test-section-local-axes",
    moment_axis="local_z",
    tension_face="local_y_min",
)


def golden_section() -> RectangularSection:
    return RectangularSection(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )


def _check(
    section: RectangularSection,
    *,
    As: float,
    M: float,
    concrete_class: str = "B25",
    rebar_class: str = "A500",
    load_duration: str = "short",
    orientation: RectangularBendingOrientation = ORIENTATION,
    As_prime: float = 0.0,
):
    return check_bending_rectangular(
        section=section,
        concrete=get_concrete(concrete_class),
        rebar=get_rebar(rebar_class),
        As=As,
        M=M,
        orientation=orientation,
        load_duration=load_duration,
        As_prime=As_prime,
    )


def _assert_public_result_is_fail_closed(result) -> None:
    assert result.Mult is None
    assert result.utilization is None
    assert result.status == "outside_applicability"
    assert result.capacity_applicable is False
    assert result.public_status == "outside_applicability"
    assert result.status_scope == "public"
    assert result.capacity_publication_allowed is False


def _assert_no_diagnostic_capacity(result) -> None:
    assert result.diagnostic_Mult is None
    assert result.diagnostic_utilization is None
    assert result.diagnostic_status == "outside_applicability"
    assert result.diagnostic_capacity_applicable is False


def test_bending_rectangular_draft_golden_case_pass():
    result = _check(golden_section(), As=942.48, M=150_000_000)

    assert result.x == pytest.approx(94.25, rel=1e-4)
    assert result.xi == pytest.approx(0.209, rel=3e-3)
    assert result.xi_R == pytest.approx(0.493, rel=2e-3)
    _assert_public_result_is_fail_closed(result)
    assert result.diagnostic_Mult == pytest.approx(165_170_000, rel=1e-3)
    assert result.diagnostic_utilization == pytest.approx(0.908, rel=2e-3)
    assert result.diagnostic_status == "pass"
    assert result.diagnostic_capacity_applicable is True
    assert any("clause 8.1.3 is not checked" in warning for warning in result.warnings)
    assert result.intermediate_values["h0"] == pytest.approx(450)
    assert result.intermediate_values["Rb_base"] == pytest.approx(14.5)
    assert result.intermediate_values["gamma_b1"] == pytest.approx(1.0)
    assert result.intermediate_values["Rb_effective"] == pytest.approx(14.5)
    assert result.intermediate_values["h0_source"] == "derived_from_declared_geometry"
    assert "Mult" not in result.intermediate_values
    assert "utilization" not in result.intermediate_values
    assert result.intermediate_values["diagnostic_Mult"] == pytest.approx(
        165_170_000,
        rel=1e-3,
    )
    assert result.intermediate_values["diagnostic_utilization"] == pytest.approx(
        0.908,
        rel=2e-3,
    )
    assert result.intermediate_values["cover_reference"] == (
        "concrete_face_to_outer_stirrup_surface"
    )
    assert result.clause_8_1_3_status == "not_checked"
    assert result.clause_8_1_3_decision_status == "OPEN_QUESTION"
    assert result.completeness_status == "incomplete"
    assert result.project_use is False
    assert result.layout_applicability_status == "not_checked_area_only"
    assert result.manual_applicability_confirmation_required is True
    assert result.requires_engineer_review is True


def test_bending_rectangular_draft_golden_case_fail_by_moment():
    result = _check(golden_section(), As=402.12, M=150_000_000)

    assert result.x == pytest.approx(40.21, rel=1e-4)
    _assert_public_result_is_fail_closed(result)
    assert result.diagnostic_Mult == pytest.approx(75_200_000, rel=1e-3)
    assert result.diagnostic_utilization == pytest.approx(1.995, rel=2e-3)
    assert result.diagnostic_status == "fail"
    assert result.diagnostic_capacity_applicable is True


def test_overreinforced_case_does_not_publish_capacity():
    section = RectangularSection(
        b=300,
        h=500,
        cover=29.5,
        stirrup_diameter=8,
        main_bar_diameter=25,
    )
    result = _check(section, As=5 * area_by_diameter(25), M=250_000_000)

    assert result.x == pytest.approx(245.436926062)
    assert result.xi == pytest.approx(0.545415391248)
    assert result.xi_R == pytest.approx(0.493392070485)
    assert result.intermediate_values["x_limit"] == pytest.approx(222.026431718)
    _assert_public_result_is_fail_closed(result)
    _assert_no_diagnostic_capacity(result)
    assert "Mult" not in result.intermediate_values
    assert "utilization" not in result.intermediate_values
    assert result.intermediate_values["applicability_reason"] == (
        "compression_zone_exceeds_limit"
    )


def test_compression_reinforcement_is_outside_v1_scope():
    result = _check(
        golden_section(),
        As=3 * area_by_diameter(20),
        As_prime=2 * area_by_diameter(16),
        M=150_000_000,
    )

    _assert_public_result_is_fail_closed(result)
    _assert_no_diagnostic_capacity(result)
    assert result.x is None
    assert result.xi is None
    assert result.intermediate_values["applicability_reason"] == (
        "compression_reinforcement_outside_v1_scope"
    )


def test_bending_rectangular_rejects_negative_As():
    with pytest.raises(ValueError, match="As must be non-negative"):
        _check(golden_section(), As=-1, M=150_000_000)


def test_bending_rectangular_rejects_negative_M():
    with pytest.raises(ValueError, match="M must be non-negative"):
        _check(golden_section(), As=942.48, M=-1)


def test_bending_rectangular_rejects_non_finite_input():
    with pytest.raises(ValueError, match="M must be finite"):
        _check(golden_section(), As=942.48, M=float("nan"))


def test_non_finite_derived_value_fails_closed_without_json_unsafe_numbers():
    result = _check(golden_section(), As=1e308, M=150_000_000)

    _assert_public_result_is_fail_closed(result)
    _assert_no_diagnostic_capacity(result)
    assert result.x is None
    assert result.xi is None
    assert result.intermediate_values["applicability_reason"] == (
        "non_finite_derived_compression_zone"
    )


def test_zero_reinforcement_is_outside_applicability_without_capacity():
    result = _check(golden_section(), As=0, M=100_000_000)

    assert result.x == 0
    _assert_public_result_is_fail_closed(result)
    _assert_no_diagnostic_capacity(result)


def test_bmr_01_assumption_regression_pass():
    section = RectangularSection(
        b=300,
        h=600,
        cover=30,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )
    result = _check(
        section,
        concrete_class="B30",
        rebar_class="A500",
        As=4 * area_by_diameter(20),
        M=250_000_000,
    )

    assert result.x == pytest.approx(107.183749358)
    assert result.xi == pytest.approx(0.194173458981)
    _assert_public_result_is_fail_closed(result)
    assert result.diagnostic_Mult == pytest.approx(272_448_383.07)
    assert result.diagnostic_utilization == pytest.approx(0.917605005334)
    assert result.diagnostic_status == "pass"
    assert result.diagnostic_capacity_applicable is True


def test_bmr_02_a400_catalog_correction_changes_status_to_fail():
    section = RectangularSection(
        b=250,
        h=500,
        cover=25,
        stirrup_diameter=8,
        main_bar_diameter=18,
    )
    result = _check(
        section,
        concrete_class="B25",
        rebar_class="A400",
        As=3 * area_by_diameter(18),
        M=111_000_000,
    )

    assert result.intermediate_values["Rs"] == pytest.approx(340)
    assert result.x == pytest.approx(71.6023131144)
    assert result.xi_R == pytest.approx(0.538461538462)
    _assert_public_result_is_fail_closed(result)
    assert result.diagnostic_Mult == pytest.approx(109_585_249.97)
    assert result.diagnostic_utilization == pytest.approx(1.01291004064)
    assert result.diagnostic_status == "fail"
    assert result.diagnostic_capacity_applicable is True


def test_bmr_03_long_combination_applies_gamma_b1_and_fails():
    result = _check(
        golden_section(),
        concrete_class="B25",
        rebar_class="A500",
        As=3 * area_by_diameter(20),
        M=164_000_000,
        load_duration="long",
    )

    assert result.intermediate_values["Rb_base"] == pytest.approx(14.5)
    assert result.intermediate_values["gamma_b1"] == pytest.approx(0.9)
    assert result.intermediate_values["Rb_effective"] == pytest.approx(13.05)
    assert result.intermediate_values["load_combination"] == "permanent_long"
    assert result.x == pytest.approx(104.71975512)
    _assert_public_result_is_fail_closed(result)
    assert result.diagnostic_Mult == pytest.approx(163_023_639.01)
    assert result.diagnostic_utilization == pytest.approx(1.00598907616)
    assert result.diagnostic_status == "fail"
    assert result.diagnostic_capacity_applicable is True


def test_exact_compression_zone_limit_is_diagnostic_only():
    section = golden_section()
    concrete = get_concrete("B25")
    rebar = get_rebar("A500")
    xi_R = 0.8 / (1.0 + (rebar.Rs / rebar.Es) / 0.0035)
    x_limit = xi_R * section.effective_depth()
    As_at_limit = concrete.Rb * section.b * x_limit / rebar.Rs

    at_limit = _check(section, As=As_at_limit, M=0)
    above_limit = _check(section, As=As_at_limit * (1 + 1e-10), M=0)

    _assert_public_result_is_fail_closed(at_limit)
    assert at_limit.diagnostic_capacity_applicable is True
    assert at_limit.diagnostic_Mult is not None
    assert at_limit.diagnostic_status == "pass"
    _assert_public_result_is_fail_closed(above_limit)
    _assert_no_diagnostic_capacity(above_limit)


def test_orientation_is_preserved_without_changing_symmetric_capacity():
    opposite = RectangularBendingOrientation(
        local_axes_id="test-section-local-axes",
        moment_axis="local_z",
        tension_face="local_y_max",
    )
    first = _check(golden_section(), As=942.48, M=150_000_000)
    second = _check(
        golden_section(),
        As=942.48,
        M=150_000_000,
        orientation=opposite,
    )

    _assert_public_result_is_fail_closed(first)
    _assert_public_result_is_fail_closed(second)
    assert first.diagnostic_Mult == pytest.approx(second.diagnostic_Mult)
    assert first.intermediate_values["tension_face"] == "local_y_min"
    assert second.intermediate_values["tension_face"] == "local_y_max"
    assert first.intermediate_values["compression_face"] == "local_y_max"
    assert second.intermediate_values["compression_face"] == "local_y_min"


def test_unsafe_override_is_absent_from_public_signature():
    parameters = signature(check_bending_rectangular).parameters

    assert "Rsc_override" not in parameters
    assert parameters["orientation"].default is parameters["orientation"].empty
    assert parameters["load_duration"].default is parameters["load_duration"].empty


def test_unsupported_longitudinal_material_fails_closed_without_profile_or_capacity():
    result = _check(
        golden_section(),
        As=942.48,
        M=150_000_000,
        rebar_class="A240",
    )

    _assert_public_result_is_fail_closed(result)
    _assert_no_diagnostic_capacity(result)
    assert result.x is None
    assert result.xi is None
    assert result.xi_R is None
    assert result.intermediate_values["applicability_reason"] == (
        "unsupported_material_profile"
    )
    assert result.intermediate_values["normative_profile_id"] is None


def test_custom_material_values_do_not_receive_official_profile():
    result = check_bending_rectangular(
        section=golden_section(),
        concrete=get_concrete("B25").model_copy(update={"Rb": 99.0}),
        rebar=get_rebar("A500").model_copy(update={"Rs": 100.0, "Rsc_short": 123.0}),
        As=942.48,
        M=150_000_000,
        orientation=ORIENTATION,
        load_duration="short",
    )

    _assert_public_result_is_fail_closed(result)
    _assert_no_diagnostic_capacity(result)
    assert result.intermediate_values["normative_profile_id"] is None
