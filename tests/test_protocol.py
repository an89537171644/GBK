import pytest

from sp63_core.checks import check_bending_rectangular, check_shear_rectangular
from sp63_core.materials import area_by_diameter, get_concrete, get_rebar
from sp63_core.report import build_calculation_protocol
from sp63_core.sections import RectangularBendingOrientation, RectangularSection

ORIENTATION = RectangularBendingOrientation(
    local_axes_id="protocol-test-local-axes",
    moment_axis="local_z",
    tension_face="local_y_min",
)


def _bending(section, concrete, rebar, **kwargs):
    return check_bending_rectangular(
        section,
        concrete,
        rebar,
        orientation=ORIENTATION,
        load_duration="short",
        **kwargs,
    )


def mvp_section() -> RectangularSection:
    return RectangularSection(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )


def base_protocol(**checks):
    return build_calculation_protocol(
        input_data={"M": 150_000_000, "Q": 80_000},
        materials={"concrete": "B25", "rebar": "A500", "stirrup_rebar": "A240"},
        geometry={"b": 300, "h": 500, "h0": 450},
        reinforcement={"main": "3D20", "stirrups": "2D8/200"},
        checks=checks,
    )


def test_build_calculation_protocol_for_passing_scheme():
    section = mvp_section()
    concrete = get_concrete("B25")
    rebar = get_rebar("A500")
    stirrup_rebar = get_rebar("A240")
    bending = _bending(section, concrete, rebar, As=942.48, M=150_000_000)
    shear = check_shear_rectangular(
        section,
        concrete,
        stirrup_rebar,
        Q=80_000,
        Asw=2 * area_by_diameter(8),
        sw=200,
    )

    protocol = build_calculation_protocol(
        input_data={"M": 150_000_000, "Q": 80_000},
        materials={"concrete": concrete.class_name, "rebar": rebar.class_name},
        geometry={"b": section.b, "h": section.h, "h0": section.effective_depth()},
        reinforcement={"main": "3D20", "stirrups": "2D8/200"},
        checks={"bending": bending, "shear": shear},
    )

    assert protocol.strength_status == "pass"
    assert protocol.serviceability_status == "not_checked"
    assert protocol.overall_status == "pass"
    assert protocol.status == "pass"
    assert protocol.warnings == ()
    assert protocol.checks["bending"]["status"] == "pass"
    assert protocol.checks["shear"]["status"] == "pass"
    protocol_dict = protocol.as_dict()
    assert protocol_dict["reinforcement"]["main"] == "3D20"
    assert protocol_dict["strength_status"] == "pass"
    assert protocol_dict["serviceability_status"] == "not_checked"
    assert protocol_dict["overall_status"] == "pass"
    assert protocol_dict["status"] == "pass"
    assert protocol.requires_engineer_review is True
    assert protocol.completeness_status == "incomplete"
    assert protocol.evidence_status == "needs_engineer_review"
    assert protocol.project_use is False


def test_build_calculation_protocol_collects_fail_warnings():
    section = mvp_section()
    concrete = get_concrete("B25")
    rebar = get_rebar("A500")
    stirrup_rebar = get_rebar("A240")
    bending = _bending(section, concrete, rebar, As=942.48, M=150_000_000)
    shear = check_shear_rectangular(
        section,
        concrete,
        stirrup_rebar,
        Q=600_000,
        Asw=2 * area_by_diameter(8),
        sw=200,
    )

    protocol = build_calculation_protocol(
        input_data={"M": 150_000_000, "Q": 600_000},
        materials={"concrete": "B25", "rebar": "A500", "stirrup_rebar": "A240"},
        geometry={"b": 300, "h": 500, "h0": 450},
        reinforcement={"main": "3D20", "stirrups": "2D8/200"},
        checks={"bending": bending, "shear": shear},
    )

    assert protocol.strength_status == "fail"
    assert protocol.serviceability_status == "not_checked"
    assert protocol.overall_status == "fail"
    assert protocol.status == "fail"
    assert "shear: shear force exceeds concrete strip capacity" in protocol.warnings
    assert "shear: shear force exceeds inclined section capacity" in protocol.warnings


def test_protocol_strength_only_pass_has_serviceability_not_checked():
    protocol = base_protocol(
        bending={"status": "pass", "warnings": ()},
        shear={"status": "pass", "warnings": ()},
    )

    assert protocol.strength_status == "pass"
    assert protocol.serviceability_status == "not_checked"
    assert protocol.overall_status == "pass"
    assert protocol.status == "pass"


def test_protocol_strength_fail_sets_overall_fail():
    protocol = base_protocol(
        bending={"status": "pass", "warnings": ()},
        shear={"status": "fail", "warnings": ("not enough stirrups",)},
    )

    assert protocol.strength_status == "fail"
    assert protocol.overall_status == "fail"
    assert protocol.status == "fail"
    assert protocol.warnings == ("shear: not enough stirrups",)


def test_protocol_preserves_outside_applicability_status():
    protocol = base_protocol(
        bending={"status": "outside_applicability", "warnings": ("outside",)},
        shear={"status": "pass", "warnings": ()},
    )

    assert protocol.checks["bending"]["status"] == "outside_applicability"
    assert protocol.strength_status == "outside_applicability"
    assert protocol.overall_status == "outside_applicability"
    assert protocol.status == "outside_applicability"


def test_protocol_contains_no_numeric_capacity_for_actual_overreinforced_result():
    section = RectangularSection(
        b=300,
        h=500,
        cover=29.5,
        stirrup_diameter=8,
        main_bar_diameter=25,
    )
    bending = _bending(
        section,
        get_concrete("B25"),
        get_rebar("A500"),
        As=5 * area_by_diameter(25),
        M=250_000_000,
    )
    protocol = base_protocol(bending=bending)

    assert protocol.checks["bending"]["status"] == "outside_applicability"
    assert protocol.checks["bending"]["Mult"] is None
    assert protocol.checks["bending"]["utilization"] is None
    assert "Mult" not in protocol.checks["bending"]["intermediate_values"]


def test_protocol_crack_formation_without_crack_width_needs_review():
    protocol = base_protocol(
        bending={"status": "pass", "warnings": ()},
        shear={"status": "pass", "warnings": ()},
        crack_formation={"status": "crack", "warnings": ()},
    )

    assert protocol.strength_status == "pass"
    assert protocol.serviceability_status == "review_or_fail"
    assert protocol.overall_status == "review_or_fail"
    assert protocol.status == "review_or_fail"


def test_protocol_crack_width_fail_sets_serviceability_fail():
    protocol = base_protocol(
        bending={"status": "pass", "warnings": ()},
        shear={"status": "pass", "warnings": ()},
        crack_formation={"status": "crack", "warnings": ()},
        crack_width={"status": "fail", "warnings": ("acrc exceeds limit",)},
    )

    assert protocol.strength_status == "pass"
    assert protocol.serviceability_status == "fail"
    assert protocol.overall_status == "fail"
    assert protocol.status == "fail"


def test_protocol_deflection_fail_sets_serviceability_fail():
    protocol = base_protocol(
        bending={"status": "pass", "warnings": ()},
        shear={"status": "pass", "warnings": ()},
        deflection={"status": "fail", "warnings": ("deflection exceeds limit",)},
    )

    assert protocol.strength_status == "pass"
    assert protocol.serviceability_status == "fail"
    assert protocol.overall_status == "fail"
    assert protocol.status == "fail"


def test_protocol_all_check_groups_pass():
    protocol = base_protocol(
        bending={"status": "pass", "warnings": ()},
        shear={"status": "pass", "warnings": ()},
        crack_formation={"status": "crack", "warnings": ()},
        crack_width={"status": "pass", "warnings": ()},
        deflection={"status": "pass", "warnings": ()},
    )

    assert protocol.strength_status == "pass"
    assert protocol.serviceability_status == "pass"
    assert protocol.overall_status == "pass"
    assert protocol.status == "pass"


def test_build_calculation_protocol_rejects_empty_checks():
    with pytest.raises(ValueError, match="checks must not be empty"):
        build_calculation_protocol(
            input_data={},
            materials={},
            geometry={},
            reinforcement={},
            checks={},
        )
