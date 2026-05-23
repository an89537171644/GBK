"""Dataset quality report helpers."""

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from sp63_core.dataset.generator import DATASET_VERSION, DatasetCase
from sp63_core.dataset.split import DatasetSplit


def build_dataset_report(
    cases: Sequence[DatasetCase],
    split: DatasetSplit | None = None,
) -> dict[str, Any]:
    """Build a lightweight report for generated deterministic dataset rows."""
    report: dict[str, Any] = {
        "dataset_version": DATASET_VERSION,
        "total_rows": len(cases),
        "counts_by_element_type": _counts(cases, "element_type"),
        "counts_by_concrete_class": _counts(cases, "concrete_class"),
        "counts_by_rebar_class": _counts(cases, "rebar_class"),
        "counts_by_stirrup_class": _counts(cases, "stirrup_class"),
        "unsafe_rows_count": _unsafe_rows_count(cases),
    }
    for field in (
        "b",
        "h",
        "h0",
        "M",
        "Q",
        "bending_utilization",
        "shear_utilization",
    ):
        field_range = _min_max(cases, field)
        report[f"min_{field}"] = field_range["min"]
        report[f"max_{field}"] = field_range["max"]

    if split is not None:
        report["split_sizes"] = {
            "train": len(split.train),
            "validation": len(split.validation),
            "test": len(split.test),
        }

    return report


def export_dataset_report_json(report: Mapping[str, Any], path: str | Path) -> Path:
    """Write a dataset report JSON file."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(dict(report), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def _counts(cases: Sequence[DatasetCase], field: str) -> dict[str, int]:
    return dict(Counter(str(getattr(case, field)) for case in cases))


def _min_max(cases: Sequence[DatasetCase], field: str) -> dict[str, float | None]:
    if not cases:
        return {"min": None, "max": None}
    values = [float(getattr(case, field)) for case in cases]
    return {"min": min(values), "max": max(values)}


def _unsafe_rows_count(cases: Sequence[DatasetCase]) -> int:
    return sum(1 for case in cases if _is_unsafe(case))


def _is_unsafe(case: DatasetCase) -> bool:
    return (
        case.status != "pass"
        or case.bending_utilization > 1.0
        or case.shear_utilization > 1.0
        or case.main_rebar_constructive_status != "pass"
        or case.stirrup_constructive_status not in ("pass", "warning")
        or case.stirrup_transverse_reinforcement_countable is not True
    )
