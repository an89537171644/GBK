"""Batch validation checks for generated dataset rows."""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from sp63_core.dataset import DatasetCase, DatasetSplit
from sp63_core.dataset.report import build_dataset_report


@dataclass(frozen=True)
class DatasetValidationResult:
    """Summary of dataset validation checks."""

    total_rows: int
    unsafe_rows_count: int
    geometry_stirrup_mismatch_count: int
    duplicate_case_id_count: int
    group_leakage_count: int
    status: str
    warnings: tuple[str, ...]


def validate_dataset_cases(
    cases: Sequence[DatasetCase],
    split: DatasetSplit | None = None,
) -> DatasetValidationResult:
    """Validate generated dataset rows before ML preparation."""
    report = build_dataset_report(cases, split)
    warnings: list[str] = []
    group_leakage_count = _group_leakage_count(split) if split is not None else 0

    total_rows = len(cases)
    unsafe_rows_count = int(report["unsafe_rows_count"])
    geometry_stirrup_mismatch_count = int(report["geometry_stirrup_mismatch_count"])
    duplicate_case_id_count = int(report["duplicate_case_id_count"])

    if total_rows <= 0:
        warnings.append("dataset must contain at least one row")
    if unsafe_rows_count != 0:
        warnings.append("dataset contains unsafe rows")
    if geometry_stirrup_mismatch_count != 0:
        warnings.append("dataset contains geometry stirrup diameter mismatches")
    if duplicate_case_id_count != 0:
        warnings.append("dataset contains duplicate case_id values")
    if group_leakage_count != 0:
        warnings.append("dataset split contains group_key leakage")

    status = "pass" if not warnings else "fail"
    return DatasetValidationResult(
        total_rows=total_rows,
        unsafe_rows_count=unsafe_rows_count,
        geometry_stirrup_mismatch_count=geometry_stirrup_mismatch_count,
        duplicate_case_id_count=duplicate_case_id_count,
        group_leakage_count=group_leakage_count,
        status=status,
        warnings=tuple(warnings),
    )


def _group_leakage_count(split: DatasetSplit) -> int:
    train_groups = _group_counts(split.train)
    validation_groups = _group_counts(split.validation)
    test_groups = _group_counts(split.test)
    leaked_groups = (
        (set(train_groups) & set(validation_groups))
        | (set(train_groups) & set(test_groups))
        | (set(validation_groups) & set(test_groups))
    )
    return len(leaked_groups)


def _group_counts(cases: Sequence[DatasetCase]) -> Counter[str]:
    return Counter(case.group_key for case in cases)
