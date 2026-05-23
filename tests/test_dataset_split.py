import csv

import pytest

from sp63_core.dataset import (
    export_dataset_split_csv,
    generate_dataset_cases,
    split_dataset_cases,
)


def test_split_dataset_cases_is_reproducible():
    cases = generate_dataset_cases(limit=10)

    split_a = split_dataset_cases(cases, seed=42)
    split_b = split_dataset_cases(cases, seed=42)

    assert [case.case_id for case in split_a.train] == [case.case_id for case in split_b.train]
    assert [case.case_id for case in split_a.validation] == [
        case.case_id for case in split_b.validation
    ]
    assert [case.case_id for case in split_a.test] == [case.case_id for case in split_b.test]


def test_split_dataset_cases_sizes():
    cases = generate_dataset_cases(limit=10)
    split = split_dataset_cases(cases)

    assert len(split.train) == 7
    assert len(split.validation) == 1
    assert len(split.test) == 2


def test_export_dataset_split_csv_creates_three_files(tmp_path):
    cases = generate_dataset_cases(limit=10)
    split = split_dataset_cases(cases)

    paths = export_dataset_split_csv(split, tmp_path, prefix="dataset_test")

    assert set(paths) == {"train", "validation", "test"}
    for path in paths.values():
        assert path.exists()
        with path.open(encoding="utf-8", newline="") as csv_file:
            assert list(csv.DictReader(csv_file))


def test_split_dataset_cases_rejects_empty_cases():
    with pytest.raises(ValueError, match="cases must not be empty"):
        split_dataset_cases(())


def test_split_dataset_cases_rejects_invalid_ratio_sum():
    cases = generate_dataset_cases(limit=3)

    with pytest.raises(ValueError, match="must sum to 1.0"):
        split_dataset_cases(cases, train_ratio=0.5, validation_ratio=0.2, test_ratio=0.2)
