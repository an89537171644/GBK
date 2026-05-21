import pytest

from sp63_core.checks import check_bending_rectangular, check_shear_rectangular
from sp63_core.materials import area_by_diameter, get_concrete, get_rebar
from sp63_core.report import build_calculation_protocol
from sp63_core.sections import RectangularSection


def mvp_section() -> RectangularSection:
    return RectangularSection(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )


def test_build_calculation_protocol_for_passing_scheme():
    section = mvp_section()
    concrete = get_concrete("B25")
    rebar = get_rebar("A500")
    stirrup_rebar = get_rebar("A240")
    bending = check_bending_rectangular(section, concrete, rebar, As=942.48, M=150_000_000)
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

    assert protocol.status == "pass"
    assert protocol.warnings == ()
    assert protocol.checks["bending"]["status"] == "pass"
    assert protocol.checks["shear"]["status"] == "pass"
    assert protocol.as_dict()["reinforcement"]["main"] == "3D20"
    assert protocol.requires_engineer_review is True


def test_build_calculation_protocol_collects_fail_warnings():
    section = mvp_section()
    concrete = get_concrete("B25")
    rebar = get_rebar("A500")
    stirrup_rebar = get_rebar("A240")
    bending = check_bending_rectangular(section, concrete, rebar, As=942.48, M=150_000_000)
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

    assert protocol.status == "fail"
    assert "shear: shear force exceeds concrete strip capacity" in protocol.warnings
    assert "shear: shear force exceeds inclined section capacity" in protocol.warnings


def test_build_calculation_protocol_review_has_priority_over_fail():
    protocol = build_calculation_protocol(
        input_data={"M": 100_000_000},
        materials={"concrete": "B25", "rebar": "A500"},
        geometry={"b": 300, "h": 500, "h0": 450},
        reinforcement={"main": "8D25"},
        checks={
            "bending": {
                "status": "review_or_fail",
                "warnings": ("manual engineering review required",),
            },
            "shear": {"status": "fail", "warnings": ("not enough stirrups",)},
        },
    )

    assert protocol.status == "review_or_fail"
    assert protocol.warnings == (
        "bending: manual engineering review required",
        "shear: not enough stirrups",
    )


def test_build_calculation_protocol_rejects_empty_checks():
    with pytest.raises(ValueError, match="checks must not be empty"):
        build_calculation_protocol(
            input_data={},
            materials={},
            geometry={},
            reinforcement={},
            checks={},
        )
