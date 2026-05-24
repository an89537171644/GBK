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
        "unique_group_count": len({case.group_key for case in cases}),
        "counts_by_main_rebar_scheme": _counts(cases, "main_rebar_scheme"),
        "counts_by_stirrup_scheme": _counts(cases, "stirrup_scheme"),
        "counts_by_strength_status": _counts(cases, "strength_status"),
        "counts_by_serviceability_status": _counts(cases, "serviceability_status"),
        "counts_by_overall_status": _counts(cases, "overall_status"),
        "geometry_stirrup_mismatch_count": _geometry_stirrup_mismatch_count(cases),
        "duplicate_case_id_count": _duplicate_case_id_count(cases),
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
        "moment_service_nmm",
        "span_mm",
        "mcrc_nmm",
        "crack_width_mm",
        "deflection_mm",
        "warnings_count",
        "main_rebar_ratio_percent",
        "stirrup_steel_consumption",
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


def _geometry_stirrup_mismatch_count(cases: Sequence[DatasetCase]) -> int:
    return sum(
        1
        for case in cases
        if case.geometry_stirrup_diameter != case.stirrup_diameter
    )


def _duplicate_case_id_count(cases: Sequence[DatasetCase]) -> int:
    case_id_counts = Counter(case.case_id for case in cases)
    return sum(count - 1 for count in case_id_counts.values() if count > 1)


def _is_unsafe(case: DatasetCase) -> bool:
    return (
        case.unsafe_row
        or case.status != "pass"
        or case.strength_status != "pass"
        or case.serviceability_status != "pass"
        or case.overall_status != "pass"
        or case.bending_utilization > 1.0
        or case.shear_utilization > 1.0
        or case.main_rebar_constructive_status != "pass"
        or case.stirrup_constructive_status not in ("pass", "warning")
        or case.stirrup_transverse_reinforcement_countable is not True
    )
