import csv

import pytest

from sp63_core.dataset import DATASET_COLUMNS, export_dataset_csv, generate_dataset_cases


def test_generate_dataset_cases_matches_schema_and_uses_safe_results():
    cases = generate_dataset_cases(limit=5)

    assert len(cases) == 5
    assert cases[0].case_id == "case_000001"
    assert tuple(cases[0].as_row()) == DATASET_COLUMNS
    assert all(case.element_type == "beam" for case in cases)
    assert all(case.status == "pass" for case in cases)
    assert all(case.As_required == pytest.approx(case.As_provided) for case in cases)
    assert all(case.bending_utilization <= 1.0 for case in cases)
    assert all(case.shear_utilization <= 1.0 for case in cases)
    assert all(case.main_bar_count > 0 for case in cases)
    assert all(case.main_bar_diameter > 0 for case in cases)
    assert all(case.main_rebar_constructive_status == "pass" for case in cases)
    assert all(case.main_rebar_ratio_percent >= 0.1 for case in cases)
    assert all(case.main_rebar_layout_feasible is True for case in cases)
    assert all(case.stirrup_diameter > 0 for case in cases)
    assert all(case.stirrup_legs > 0 for case in cases)
    assert all(case.stirrup_spacing > 0 for case in cases)
    assert all(case.stirrup_Asw > 0 for case in cases)
    assert all(case.stirrup_steel_consumption > 0 for case in cases)
    assert all(case.stirrup_constructive_status in ("pass", "warning") for case in cases)
    assert all(case.stirrup_constructive_max_spacing > 0 for case in cases)
    assert all(case.stirrup_sw_max_by_shear_rule > 0 for case in cases)
    assert all(case.stirrup_qsw_rule_status == "pass" for case in cases)
    assert all(case.stirrup_transverse_reinforcement_countable is True for case in cases)


def test_generate_dataset_cases_respects_limit():
    cases = generate_dataset_cases(limit=3)

    assert [case.case_id for case in cases] == ["case_000001", "case_000002", "case_000003"]


def test_generate_dataset_cases_uses_selected_option_section_h0():
    case = generate_dataset_cases(limit=1)[0]
    selected_diameter = float(case.main_rebar_scheme.split("D", maxsplit=1)[1])

    assert case.h0 == pytest.approx(case.h - 32.0 - 8.0 - selected_diameter / 2.0)


def test_generate_dataset_cases_writes_load_duration():
    case = generate_dataset_cases(limit=1, load_duration="long")[0]

    assert case.load_duration == "long"
    assert case.as_row()["load_duration"] == "long"


def test_generate_dataset_cases_rejects_invalid_limit():
    with pytest.raises(ValueError, match="limit must be positive"):
        generate_dataset_cases(limit=0)


def test_generate_dataset_cases_rejects_unsupported_element_type():
    with pytest.raises(ValueError, match="only beam element_type is supported"):
        generate_dataset_cases(limit=1, element_types=("slab",))


def test_export_dataset_csv(tmp_path):
    cases = generate_dataset_cases(limit=2)
    output_path = export_dataset_csv(cases, tmp_path / "generated" / "dataset.csv")

    with output_path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    assert reader.fieldnames == list(DATASET_COLUMNS)
    assert len(rows) == 2
    assert rows[0]["case_id"] == "case_000001"
    assert rows[0]["status"] == "pass"
