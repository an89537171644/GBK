import json
from pathlib import Path

import pytest

from sp63_core.checks import check_bending_rectangular, check_shear_rectangular
from sp63_core.materials import get_concrete, get_rebar
from sp63_core.sections import RectangularSection

GOLDEN_CASES_DIR = Path(__file__).parent / "golden_cases"


def load_case(file_name: str) -> dict:
    return json.loads((GOLDEN_CASES_DIR / file_name).read_text(encoding="utf-8"))


def iter_case_records(payload: dict | list[dict]) -> list[dict]:
    if isinstance(payload, list):
        return payload
    return [payload]


def test_all_golden_case_files_are_draft_and_unapproved():
    for path in GOLDEN_CASES_DIR.glob("*.json"):
        for case in iter_case_records(json.loads(path.read_text(encoding="utf-8"))):
            assert case["approved_by_engineer"] is False, path.name
            assert case["requires_engineer_review"] is True, path.name


@pytest.mark.parametrize(
    "file_name",
    ["bending_rectangular_pass.json", "bending_rectangular_fail.json"],
)
def test_bending_golden_cases(file_name):
    case = load_case(file_name)

    assert case["approved_by_engineer"] is False
    assert case["requires_engineer_review"] is True

    inputs = case["input"]
    section = RectangularSection(
        b=inputs["b"],
        h=inputs["h"],
        cover=inputs["cover"],
        stirrup_diameter=inputs["stirrup_diameter"],
        main_bar_diameter=inputs["main_bar_diameter"],
    )
    result = check_bending_rectangular(
        section=section,
        concrete=get_concrete(inputs["concrete_class"]),
        rebar=get_rebar(inputs["rebar_class"]),
        As=inputs["As"],
        As_prime=inputs.get("As_prime", 0),
        M=inputs["M"],
    )

    expected = case["expected"]
    assert result.x == pytest.approx(expected["x"], rel=1e-3)
    if "xi" in expected:
        assert result.xi == pytest.approx(expected["xi"], rel=5e-3)
    if "xi_R" in expected:
        assert result.xi_R == pytest.approx(expected["xi_R"], rel=5e-3)
    assert result.Mult == pytest.approx(expected["Mult"], rel=1e-3)
    assert result.utilization == pytest.approx(expected["utilization"], rel=5e-3)
    assert result.status == expected["status"]
    assert result.requires_engineer_review is True


def test_shear_golden_case_pass():
    case = load_case("shear_rectangular_pass.json")

    assert case["approved_by_engineer"] is False
    assert case["requires_engineer_review"] is True

    inputs = case["input"]
    section = RectangularSection(
        b=inputs["b"],
        h=inputs["h"],
        cover=inputs["cover"],
        stirrup_diameter=inputs["stirrup_diameter"],
        main_bar_diameter=inputs["main_bar_diameter"],
    )
    result = check_shear_rectangular(
        section=section,
        concrete=get_concrete(inputs["concrete_class"]),
        stirrup_rebar=get_rebar(inputs["stirrup_rebar_class"]),
        Asw=inputs["Asw"],
        sw=inputs["sw"],
        Q=inputs["Q"],
    )

    expected = case["expected"]
    assert result.qsw == pytest.approx(expected["qsw"], rel=1e-3)
    assert result.Q_strip == pytest.approx(expected["Q_strip"], rel=1e-6)
    assert result.intermediate_values["C"] == pytest.approx(expected["C"])
    assert result.Qb == pytest.approx(expected["Qb"], rel=1e-3)
    assert result.Qsw == pytest.approx(expected["Qsw"], rel=1e-3)
    assert result.Qult == pytest.approx(expected["Qult"], rel=1e-3)
    assert result.status == expected["status"]
    assert result.requires_engineer_review is True
