"""Trend report export for multiple synthetic benchmark reports."""

from __future__ import annotations

import csv
import json
import math
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TREND_REPORT_TYPE = "benchmark_trend_report"
TREND_METRICS = (
    "accuracy",
    "macro_f1",
    "weighted_f1",
    "precision_macro",
    "recall_macro",
)
TREND_CLASSES = ("pass", "fail", "review_or_fail")
TREND_WARNING = (
    "Synthetic benchmark trends are not external validation and are not production "
    "evidence. ML remains advisory-only. Deterministic SP63 verification and "
    "engineer review are mandatory."
)


@dataclass(frozen=True)
class BenchmarkTrendReportResult:
    """Aggregated trend report for several synthetic benchmark runs."""

    status: str
    trend_status: str
    benchmark_count: int
    benchmark_report_paths: tuple[str, ...]
    output_dir: str | None
    dataset_row_count_summary: dict[str, Any]
    distribution_summary: dict[str, Any]
    baseline_metric_summary: dict[str, Any]
    neural_metric_summary: dict[str, Any]
    winner_summary: dict[str, Any]
    recommendations: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    markdown: str
    json_data: dict[str, Any]
    csv_rows: tuple[dict[str, Any], ...]
    synthetic_data_only: bool = True
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True


def discover_benchmark_reports(root_dir: Path) -> tuple[Path, ...]:
    """Discover K55 benchmark report JSON files under a root directory."""
    root = Path(root_dir)
    if not root.exists():
        return ()
    return tuple(sorted(path for path in root.rglob("benchmark_report.json") if path.is_file()))


def build_benchmark_trend_report(
    *,
    benchmark_report_paths: Iterable[Path],
    output_dir: Path | None = None,
) -> BenchmarkTrendReportResult:
    """Build and optionally write an aggregated benchmark trend report."""
    input_paths = tuple(dict.fromkeys(Path(path) for path in benchmark_report_paths))
    warnings: list[str] = [TREND_WARNING]
    errors: list[str] = []
    valid_reports: list[dict[str, Any]] = []
    valid_paths: list[str] = []
    recommendations: list[str] = []
    synthetic_data_only = True

    if not input_paths:
        errors.append("no benchmark report paths were provided")

    for path in input_paths:
        report, report_warnings = _load_valid_benchmark_report(path)
        warnings.extend(report_warnings)
        if report is None:
            continue
        valid_reports.append(report)
        valid_paths.append(str(path))
        recommendations.extend(_string_list(report.get("recommendations")))
        synthetic_data_only = synthetic_data_only and _as_bool(
            report.get("synthetic_data_only"),
            default=True,
        )
        warnings.extend(_string_list(report.get("warnings")))

    if not valid_reports:
        errors.append("no valid benchmark reports were found")

    dataset_row_count_summary = _dataset_row_count_summary(valid_reports)
    distribution_summary, distribution_warnings = _distribution_summary(
        valid_reports=valid_reports,
        valid_paths=valid_paths,
    )
    warnings.extend(distribution_warnings)
    baseline_metric_summary, baseline_warnings = _metric_summary(
        valid_reports=valid_reports,
        metric_source="baseline_metrics",
        model_name="baseline",
    )
    neural_metric_summary, neural_warnings = _metric_summary(
        valid_reports=valid_reports,
        metric_source="neural_metrics",
        model_name="neural",
    )
    warnings.extend(baseline_warnings)
    warnings.extend(neural_warnings)
    winner_summary = _winner_summary(valid_reports)
    if valid_reports and not _metric_summary_has_values(baseline_metric_summary):
        errors.append("baseline metric summary could not be formed")
    if valid_reports and not _metric_summary_has_values(neural_metric_summary):
        errors.append("neural metric summary could not be formed")

    total_dataset_rows = int(dataset_row_count_summary.get("total", 0))
    if len(valid_reports) < 3:
        warnings.append("benchmark_count is below 3")
    if total_dataset_rows < 300:
        warnings.append("total dataset_row_count is below 300")
    if synthetic_data_only:
        warnings.append("trend report is based on synthetic benchmark data only")
    for report, path in zip(valid_reports, valid_paths, strict=True):
        if str(report.get("benchmark_status") or report.get("status")) == "fail":
            warnings.append(f"source benchmark_status is fail: {path}")
        elif str(report.get("benchmark_status") or report.get("status")) == "review_required":
            warnings.append(f"source benchmark_status is review_required: {path}")

    trend_status = _resolve_trend_status(
        errors=errors,
        warnings=warnings,
        benchmark_count=len(valid_reports),
        total_dataset_rows=total_dataset_rows,
    )
    deduped_warnings = tuple(dict.fromkeys(warnings))
    deduped_errors = tuple(dict.fromkeys(errors))
    deduped_recommendations = tuple(dict.fromkeys(recommendations))
    csv_rows = _build_metric_csv_rows(
        baseline_metric_summary=baseline_metric_summary,
        neural_metric_summary=neural_metric_summary,
    )
    markdown = _render_markdown(
        trend_status=trend_status,
        benchmark_report_paths=tuple(valid_paths),
        dataset_row_count_summary=dataset_row_count_summary,
        distribution_summary=distribution_summary,
        baseline_metric_summary=baseline_metric_summary,
        neural_metric_summary=neural_metric_summary,
        winner_summary=winner_summary,
        recommendations=deduped_recommendations,
        warnings=deduped_warnings,
        errors=deduped_errors,
        synthetic_data_only=synthetic_data_only,
    )
    json_data = {
        "report_type": TREND_REPORT_TYPE,
        "status": trend_status,
        "trend_status": trend_status,
        "benchmark_count": len(valid_reports),
        "benchmark_report_paths": valid_paths,
        "output_dir": None if output_dir is None else str(output_dir),
        "dataset_row_count_summary": dataset_row_count_summary,
        "distribution_summary": distribution_summary,
        "baseline_metric_summary": baseline_metric_summary,
        "neural_metric_summary": neural_metric_summary,
        "winner_summary": winner_summary,
        "recommendations": list(deduped_recommendations),
        "warnings": list(deduped_warnings),
        "errors": list(deduped_errors),
        "synthetic_data_only": synthetic_data_only,
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
    }
    result = BenchmarkTrendReportResult(
        status=trend_status,
        trend_status=trend_status,
        benchmark_count=len(valid_reports),
        benchmark_report_paths=tuple(valid_paths),
        output_dir=None if output_dir is None else str(output_dir),
        dataset_row_count_summary=dataset_row_count_summary,
        distribution_summary=distribution_summary,
        baseline_metric_summary=baseline_metric_summary,
        neural_metric_summary=neural_metric_summary,
        winner_summary=winner_summary,
        recommendations=deduped_recommendations,
        warnings=deduped_warnings,
        errors=deduped_errors,
        markdown=markdown,
        json_data=json_data,
        csv_rows=csv_rows,
        synthetic_data_only=synthetic_data_only,
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
    )
    if output_dir is not None:
        _write_outputs(result, Path(output_dir))
    return result


def _load_valid_benchmark_report(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    warnings: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [f"benchmark report input_error: {path} does not exist"]
    except json.JSONDecodeError as exc:
        return None, [f"benchmark report input_error: {path} is not valid JSON: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"benchmark report input_error: {path} JSON must contain an object"]
    missing_fields = _missing_critical_fields(payload)
    if missing_fields:
        warnings.append(
            f"benchmark report input_error: {path} missing critical fields: "
            + ", ".join(missing_fields)
        )
        return None, warnings
    return payload, warnings


def _missing_critical_fields(payload: dict[str, Any]) -> tuple[str, ...]:
    required = (
        "benchmark_status",
        "target_distribution_goal",
        "final_distribution",
        "dataset_row_count",
        "balance_status",
        "quality_status",
        "feature_status",
        "baseline_status",
        "neural_status",
        "baseline_metrics",
        "neural_metrics",
        "recommendations",
        "warnings",
        "synthetic_data_only",
        "requires_engineer_review",
        "ml_is_advisory_only",
        "deterministic_checks_required",
    )
    return tuple(field for field in required if field not in payload)


def _dataset_row_count_summary(valid_reports: list[dict[str, Any]]) -> dict[str, Any]:
    counts = [_as_int(report.get("dataset_row_count")) for report in valid_reports]
    if not counts:
        return {
            "count": 0,
            "total": 0,
            "mean": 0.0,
            "min": 0,
            "max": 0,
            "missing_count": 0,
        }
    return {
        "count": len(counts),
        "total": sum(counts),
        "mean": sum(counts) / len(counts),
        "min": min(counts),
        "max": max(counts),
        "missing_count": sum(1 for value in counts if value == 0),
    }


def _distribution_summary(
    *,
    valid_reports: list[dict[str, Any]],
    valid_paths: list[str],
) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    values_by_class: dict[str, list[int]] = {class_name: [] for class_name in TREND_CLASSES}
    missing_class_reports: dict[str, list[str]] = {class_name: [] for class_name in TREND_CLASSES}
    for report, path in zip(valid_reports, valid_paths, strict=True):
        distribution = _int_mapping(report.get("final_distribution"))
        missing_for_report = [
            class_name
            for class_name in TREND_CLASSES
            if distribution.get(class_name, 0) <= 0
        ]
        if missing_for_report:
            warnings.append(
                f"benchmark report does not contain all required classes: {path}"
            )
        for class_name in TREND_CLASSES:
            value = distribution.get(class_name, 0)
            values_by_class[class_name].append(value)
            if value <= 0:
                missing_class_reports[class_name].append(path)
    total = {
        class_name: sum(values)
        for class_name, values in values_by_class.items()
    }
    mean_per_benchmark = {
        class_name: _mean(values)
        for class_name, values in values_by_class.items()
    }
    min_per_benchmark = {
        class_name: min(values) if values else 0
        for class_name, values in values_by_class.items()
    }
    max_per_benchmark = {
        class_name: max(values) if values else 0
        for class_name, values in values_by_class.items()
    }
    return (
        {
            "total": total,
            "mean_per_benchmark": mean_per_benchmark,
            "min_per_benchmark": min_per_benchmark,
            "max_per_benchmark": max_per_benchmark,
            "missing_class_reports": missing_class_reports,
        },
        warnings,
    )


def _metric_summary(
    *,
    valid_reports: list[dict[str, Any]],
    metric_source: str,
    model_name: str,
) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    summary: dict[str, Any] = {}
    for metric in TREND_METRICS:
        values: list[float] = []
        missing_count = 0
        for report in valid_reports:
            metrics = _extract_metrics(report.get(metric_source))
            value = metrics.get(metric)
            if value is None:
                missing_count += 1
                continue
            values.append(float(value))
        if missing_count:
            warnings.append(
                f"{model_name} metric is missing in {missing_count} benchmark reports: {metric}"
            )
        summary[metric] = {
            "count": len(values),
            "mean": _mean(values),
            "min": min(values) if values else None,
            "max": max(values) if values else None,
            "std": _std(values),
            "missing_count": missing_count,
        }
    return summary, warnings


def _winner_summary(valid_reports: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for metric in TREND_METRICS:
        baseline_win_count = 0
        neural_win_count = 0
        tie_count = 0
        missing_count = 0
        for report in valid_reports:
            baseline_metrics = _extract_metrics(report.get("baseline_metrics"))
            neural_metrics = _extract_metrics(report.get("neural_metrics"))
            baseline_value = baseline_metrics.get(metric)
            neural_value = neural_metrics.get(metric)
            if baseline_value is None or neural_value is None:
                missing_count += 1
            elif float(baseline_value) > float(neural_value):
                baseline_win_count += 1
            elif float(neural_value) > float(baseline_value):
                neural_win_count += 1
            else:
                tie_count += 1
        summary[metric] = {
            "baseline_win_count": baseline_win_count,
            "neural_win_count": neural_win_count,
            "tie_count": tie_count,
            "missing_count": missing_count,
        }
    return summary


def _build_metric_csv_rows(
    *,
    baseline_metric_summary: dict[str, Any],
    neural_metric_summary: dict[str, Any],
) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    for model_name, summary in (
        ("baseline", baseline_metric_summary),
        ("neural", neural_metric_summary),
    ):
        for metric in TREND_METRICS:
            metric_summary = summary.get(metric, {})
            rows.append(
                {
                    "model": model_name,
                    "metric": metric,
                    "count": metric_summary.get("count", 0),
                    "mean": metric_summary.get("mean", 0.0),
                    "min": metric_summary.get("min", ""),
                    "max": metric_summary.get("max", ""),
                    "std": metric_summary.get("std", 0.0),
                    "missing_count": metric_summary.get("missing_count", 0),
                }
            )
    return tuple(rows)


def _render_markdown(
    *,
    trend_status: str,
    benchmark_report_paths: tuple[str, ...],
    dataset_row_count_summary: dict[str, Any],
    distribution_summary: dict[str, Any],
    baseline_metric_summary: dict[str, Any],
    neural_metric_summary: dict[str, Any],
    winner_summary: dict[str, Any],
    recommendations: tuple[str, ...],
    warnings: tuple[str, ...],
    errors: tuple[str, ...],
    synthetic_data_only: bool,
) -> str:
    lines = [
        "# Synthetic Benchmark Trend Report - Advisory Only",
        "",
        TREND_WARNING,
        "",
        "## Benchmark Inputs",
        "",
        f"- trend_status: `{trend_status}`",
        f"- benchmark_count: `{len(benchmark_report_paths)}`",
        f"- synthetic_data_only: `{synthetic_data_only}`",
        "- report paths:",
        *_markdown_list(benchmark_report_paths, fallback="No valid benchmark reports."),
        "",
        "## Dataset Row Count Summary",
        "",
        *_markdown_dict(dataset_row_count_summary),
        "",
        "## Distribution Summary",
        "",
        *_markdown_nested_dict(distribution_summary),
        "",
        "## Baseline Metric Trends",
        "",
        *_metric_markdown_table(baseline_metric_summary),
        "",
        "## Neural Metric Trends",
        "",
        *_metric_markdown_table(neural_metric_summary),
        "",
        "## Winner Summary",
        "",
        *_winner_markdown_table(winner_summary),
        "",
        "## Recommendations",
        "",
        *_markdown_list(recommendations, fallback="No recommendations."),
        "",
        "## Warnings",
        "",
        *_markdown_list(warnings, fallback="No warnings."),
    ]
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(_markdown_list(errors))
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- synthetic data only",
            "- not external validation",
            "- material verification is separate",
            "- external validation is separate",
            "- no certification",
            "- ML is not a design checker",
            "- deterministic SP63 verification remains mandatory",
            "- engineer review is required",
            "",
        ]
    )
    return "\n".join(lines)


def _write_outputs(result: BenchmarkTrendReportResult, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "benchmark_trend_report.md").write_text(
        result.markdown,
        encoding="utf-8",
    )
    (output_dir / "benchmark_trend_report.json").write_text(
        json.dumps(result.json_data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (output_dir / "benchmark_trend_metrics.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=("model", "metric", "count", "mean", "min", "max", "std", "missing_count"),
        )
        writer.writeheader()
        writer.writerows(result.csv_rows)
    with (output_dir / "benchmark_trend_winners.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=(
                "metric",
                "baseline_win_count",
                "neural_win_count",
                "tie_count",
                "missing_count",
            ),
        )
        writer.writeheader()
        for metric, row in result.winner_summary.items():
            writer.writerow({"metric": metric, **row})


def _resolve_trend_status(
    *,
    errors: list[str],
    warnings: list[str],
    benchmark_count: int,
    total_dataset_rows: int,
) -> str:
    if errors or benchmark_count == 0:
        return "fail"
    if benchmark_count < 3 or total_dataset_rows < 300 or warnings:
        return "review_required"
    return "pass"


def _metric_summary_has_values(summary: dict[str, Any]) -> bool:
    return any(metric.get("count", 0) > 0 for metric in summary.values())


def _extract_metrics(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    metrics = value.get("metrics", value)
    if not isinstance(metrics, dict):
        return {}
    return {
        metric: float(metrics[metric])
        for metric in TREND_METRICS
        if metric in metrics and _is_number(metrics[metric])
    }


def _int_mapping(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {str(key): _as_int(item) for key, item in value.items()}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item) for item in value if str(item)]


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _as_bool(value: Any, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def _is_number(value: Any) -> bool:
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def _mean(values: list[int] | list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def _markdown_dict(values: dict[str, Any]) -> list[str]:
    return [f"- {key}: `{value}`" for key, value in sorted(values.items())]


def _markdown_nested_dict(values: dict[str, Any]) -> list[str]:
    if not values:
        return ["- No distribution summary."]
    lines: list[str] = []
    for key, value in sorted(values.items()):
        lines.append(f"- {key}: `{value}`")
    return lines


def _metric_markdown_table(summary: dict[str, Any]) -> list[str]:
    lines = [
        "| metric | count | mean | min | max | std | missing_count |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for metric in TREND_METRICS:
        row = summary.get(metric, {})
        lines.append(
            f"| {metric} | {row.get('count', 0)} | {row.get('mean', 0.0)} | "
            f"{row.get('min', 'n/a')} | {row.get('max', 'n/a')} | "
            f"{row.get('std', 0.0)} | {row.get('missing_count', 0)} |"
        )
    return lines


def _winner_markdown_table(summary: dict[str, Any]) -> list[str]:
    lines = [
        "| metric | baseline wins | neural wins | ties | missing |",
        "|---|---:|---:|---:|---:|",
    ]
    for metric in TREND_METRICS:
        row = summary.get(metric, {})
        lines.append(
            f"| {metric} | {row.get('baseline_win_count', 0)} | "
            f"{row.get('neural_win_count', 0)} | {row.get('tie_count', 0)} | "
            f"{row.get('missing_count', 0)} |"
        )
    return lines


def _markdown_list(values: tuple[str, ...], fallback: str | None = None) -> list[str]:
    if not values and fallback is not None:
        return [f"- {fallback}"]
    return [f"- {value}" for value in values]
