import csv

import pytest

from sp63_core.dataset import (
    DATASET_COLUMNS,
    export_dataset_csv,
    export_dataset_splits,
    generate_dataset_cases,
    split_dataset_cases,
)


def test_generate_dataset_cases_matches_schema_and_uses_safe_design_results():
    cases = generate_dataset_cases(limit=5)

    assert len(cases) == 5
    assert cases[0].case_id == "case_000001"
    assert tuple(cases[0].as_row()) == DATASET_COLUMNS
    assert all(case.status == "pass" for case in cases)
    assert all(case.requires_engineer_review is True for case in cases)
    assert all(case.layout_feasible is True for case in cases)
    assert all(case.As_required == pytest.approx(case.As_provided) for case in cases)
    assert all(case.bending_utilization <= 1.0 for case in cases)
    assert all(case.shear_utilization <= 1.0 for case in cases)
    assert all(case.main_bar_count > 0 for case in cases)
    assert all(case.main_bar_diameter > 0 for case in cases)
    assert all(case.stirrup_diameter > 0 for case in cases)
    assert all(case.stirrup_spacing > 0 for case in cases)
    assert all(case.Asw > 0 for case in cases)


def test_generate_dataset_cases_respects_limit():
    cases = generate_dataset_cases(limit=3)

    assert [case.case_id for case in cases] == ["case_000001", "case_000002", "case_000003"]


def test_generate_dataset_cases_uses_selected_option_section_h0():
    case = generate_dataset_cases(limit=1)[0]

    assert case.h0 == pytest.approx(case.h - 32.0 - 8.0 - case.main_bar_diameter / 2.0)


def test_generate_dataset_cases_rejects_invalid_limit():
    with pytest.raises(ValueError, match="limit must be positive"):
        generate_dataset_cases(limit=0)


def test_split_dataset_cases_is_deterministic():
    cases = generate_dataset_cases(limit=20)
    splits = split_dataset_cases(cases)

    assert tuple(splits) == ("train", "validation", "test")
    assert len(splits["train"]) == 14
    assert len(splits["validation"]) == 3
    assert len(splits["test"]) == 3
    assert splits["train"][0].case_id == "case_000001"
    assert splits["validation"][0].case_id == "case_000015"
    assert splits["test"][0].case_id == "case_000018"


def test_split_dataset_cases_handles_empty_input():
    assert split_dataset_cases(()) == {"train": (), "validation": (), "test": ()}


def test_split_dataset_cases_rejects_invalid_ratios():
    cases = generate_dataset_cases(limit=3)

    with pytest.raises(ValueError, match="split ratios must sum to 1.0"):
        split_dataset_cases(cases, train_ratio=0.8, validation_ratio=0.15, test_ratio=0.15)

    with pytest.raises(ValueError, match="split ratios must be non-negative"):
        split_dataset_cases(cases, train_ratio=-0.1, validation_ratio=0.6, test_ratio=0.5)


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
    assert rows[0]["requires_engineer_review"] == "True"


def test_export_dataset_splits_creates_three_csv_files(tmp_path):
    cases = generate_dataset_cases(limit=20)
    paths = export_dataset_splits(cases, tmp_path / "splits")

    assert tuple(paths) == ("train", "validation", "test")
    assert all(path.exists() for path in paths.values())
    assert paths["train"].name == "train.csv"
    assert paths["validation"].name == "validation.csv"
    assert paths["test"].name == "test.csv"
