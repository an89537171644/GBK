"""Model comparison export for synthetic benchmark reports."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

COMPARISON_REPORT_TYPE = "benchmark_model_comparison"
COMPARISON_METRICS = (
    "accuracy",
    "macro_f1",
    "weighted_f1",
    "precision_macro",
    "recall_macro",
)
COMPARISON_WARNING = (
    "Synthetic benchmark metrics are not production evidence. ML remains advisory-only. "
    "Deterministic SP63 verification and engineer review are mandatory."
)


@dataclass(frozen=True)
class BenchmarkModelComparisonResult:
    """Comparison report for baseline and neural synthetic benchmark metrics."""

    status: str
    comparison_status: str
    benchmark_report_path: str
    output_dir: str | None
    baseline_metrics: dict[str, Any]
    neural_metrics: dict[str, Any]
    metric_winners: dict[str, str]
    baseline_status: str
    neural_status: str
    dataset_row_count: int
    final_distribution: dict[str, int]
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


def build_benchmark_model_comparison(
    *,
    benchmark_report_path: Path,
    output_dir: Path | None = None,
) -> BenchmarkModelComparisonResult:
    """Build and optionally write model comparison reports from a K55 benchmark JSON."""
    report_path = Path(benchmark_report_path)
    warnings: list[str] = [COMPARISON_WARNING]
    errors: list[str] = []
    benchmark = _load_benchmark_report(report_path, errors)

    baseline_metrics: dict[str, Any] = {}
    neural_metrics: dict[str, Any] = {}
    metric_winners: dict[str, str] = {}
    baseline_status = "missing"
    neural_status = "missing"
    dataset_row_count = 0
    final_distribution: dict[str, int] = {}
    recommendations: tuple[str, ...] = ()
    synthetic_data_only = True
    benchmark_status = "missing"

    if benchmark:
        missing_fields = _missing_critical_fields(benchmark)
        if missing_fields:
            errors.append(
                "benchmark report is missing critical fields: "
                + ", ".join(missing_fields)
            )
        benchmark_status = str(benchmark.get("benchmark_status") or benchmark.get("status") or "")
        baseline_status = str(benchmark.get("baseline_status") or "missing")
        neural_status = str(benchmark.get("neural_status") or "missing")
        dataset_row_count = _as_int(benchmark.get("dataset_row_count"))
        final_distribution = _int_mapping(benchmark.get("final_distribution"))
        recommendations = tuple(str(value) for value in benchmark.get("recommendations", ()))
        synthetic_data_only = _as_bool(benchmark.get("synthetic_data_only"), default=True)
        baseline_metrics = _extract_metrics(benchmark.get("baseline_metrics"))
        neural_metrics = _extract_metrics(benchmark.get("neural_metrics"))
        metric_winners = _compare_metrics(
            baseline_metrics=baseline_metrics,
            neural_metrics=neural_metrics,
            warnings=warnings,
        )
        if benchmark_status == "fail":
            errors.append("benchmark_status is fail")
        if not baseline_metrics and not neural_metrics:
            errors.append("both baseline and neural metrics are missing")
        if dataset_row_count < 100:
            warnings.append("benchmark dataset row count is below 100")
        if synthetic_data_only:
            warnings.append("comparison report is based on synthetic benchmark data only")
        if benchmark_status == "review_required":
            warnings.append("source benchmark_status is review_required")
        for warning in benchmark.get("warnings", ()):
            if isinstance(warning, str) and warning:
                warnings.append(warning)

    comparison_status = _resolve_status(errors=errors, warnings=warnings)
    csv_rows = _build_csv_rows(
        baseline_metrics=baseline_metrics,
        neural_metrics=neural_metrics,
        metric_winners=metric_winners,
    )
    markdown = _render_markdown(
        comparison_status=comparison_status,
        dataset_row_count=dataset_row_count,
        final_distribution=final_distribution,
        baseline_metrics=baseline_metrics,
        neural_metrics=neural_metrics,
        metric_winners=metric_winners,
        recommendations=recommendations,
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(dict.fromkeys(errors)),
        synthetic_data_only=synthetic_data_only,
    )
    json_data = {
        "report_type": COMPARISON_REPORT_TYPE,
        "status": comparison_status,
        "comparison_status": comparison_status,
        "benchmark_report_path": str(report_path),
        "output_dir": None if output_dir is None else str(output_dir),
        "dataset_row_count": dataset_row_count,
        "final_distribution": final_distribution,
        "baseline_metrics": baseline_metrics,
        "neural_metrics": neural_metrics,
        "metric_winners": metric_winners,
        "baseline_status": baseline_status,
        "neural_status": neural_status,
        "recommendations": list(recommendations),
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "synthetic_data_only": synthetic_data_only,
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
    }
    result = BenchmarkModelComparisonResult(
        status=comparison_status,
        comparison_status=comparison_status,
        benchmark_report_path=str(report_path),
        output_dir=None if output_dir is None else str(output_dir),
        baseline_metrics=baseline_metrics,
        neural_metrics=neural_metrics,
        metric_winners=metric_winners,
        baseline_status=baseline_status,
        neural_status=neural_status,
        dataset_row_count=dataset_row_count,
        final_distribution=final_distribution,
        recommendations=recommendations,
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(dict.fromkeys(errors)),
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


def _load_benchmark_report(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"benchmark report does not exist: {path}")
        return None
    except json.JSONDecodeError as exc:
        errors.append(f"benchmark report is not valid JSON: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append("benchmark report JSON must contain an object")
        return None
    return payload


def _missing_critical_fields(payload: dict[str, Any]) -> tuple[str, ...]:
    required = (
        "baseline_metrics",
        "neural_metrics",
        "baseline_status",
        "neural_status",
        "dataset_row_count",
        "final_distribution",
        "recommendations",
        "warnings",
    )
    return tuple(field for field in required if field not in payload)


def _extract_metrics(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    metrics = value.get("metrics", value)
    if not isinstance(metrics, dict):
        return {}
    return {
        metric: metrics[metric]
        for metric in COMPARISON_METRICS
        if metric in metrics and _is_number(metrics[metric])
    }


def _compare_metrics(
    *,
    baseline_metrics: dict[str, Any],
    neural_metrics: dict[str, Any],
    warnings: list[str],
) -> dict[str, str]:
    winners: dict[str, str] = {}
    for metric in COMPARISON_METRICS:
        baseline_value = baseline_metrics.get(metric)
        neural_value = neural_metrics.get(metric)
        if baseline_value is None or neural_value is None:
            winners[metric] = "missing"
            warnings.append(f"metric is missing for model comparison: {metric}")
            continue
        baseline_float = float(baseline_value)
        neural_float = float(neural_value)
        if baseline_float > neural_float:
            winners[metric] = "baseline"
        elif neural_float > baseline_float:
            winners[metric] = "neural"
        else:
            winners[metric] = "tie"
    return winners


def _build_csv_rows(
    *,
    baseline_metrics: dict[str, Any],
    neural_metrics: dict[str, Any],
    metric_winners: dict[str, str],
) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "metric": metric,
            "baseline": baseline_metrics.get(metric, ""),
            "neural": neural_metrics.get(metric, ""),
            "winner": metric_winners.get(metric, "missing"),
        }
        for metric in COMPARISON_METRICS
    )


def _render_markdown(
    *,
    comparison_status: str,
    dataset_row_count: int,
    final_distribution: dict[str, int],
    baseline_metrics: dict[str, Any],
    neural_metrics: dict[str, Any],
    metric_winners: dict[str, str],
    recommendations: tuple[str, ...],
    warnings: tuple[str, ...],
    errors: tuple[str, ...],
    synthetic_data_only: bool,
) -> str:
    lines = [
        "# Synthetic Benchmark Model Comparison - Advisory Only",
        "",
        COMPARISON_WARNING,
        "",
        "## Dataset Summary",
        "",
        f"- comparison_status: `{comparison_status}`",
        f"- dataset_row_count: `{dataset_row_count}`",
        f"- synthetic_data_only: `{synthetic_data_only}`",
        "- final_distribution:",
        *_markdown_dict(final_distribution),
        "",
        "## Baseline ML Metrics",
        "",
        *_markdown_dict(baseline_metrics, fallback="No baseline metrics."),
        "",
        "## Neural Surrogate Metrics",
        "",
        *_markdown_dict(neural_metrics, fallback="No neural metrics."),
        "",
        "## Metric Winners",
        "",
        "| metric | baseline | neural | winner |",
        "|---|---:|---:|---|",
    ]
    for metric in COMPARISON_METRICS:
        lines.append(
            f"| {metric} | {baseline_metrics.get(metric, 'n/a')} | "
            f"{neural_metrics.get(metric, 'n/a')} | "
            f"{metric_winners.get(metric, 'missing')} |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(_markdown_list(recommendations, fallback="No recommendations."))
    lines.extend(["", "## Warnings", ""])
    lines.extend(_markdown_list(warnings, fallback="No warnings."))
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(_markdown_list(errors))
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- synthetic benchmark only",
            "- not external validation",
            "- material verification is separate",
            "- external validation is separate",
            "- ML is not a design checker",
            "- deterministic SP63 verification remains mandatory",
            "- engineer review is required",
            "",
        ]
    )
    return "\n".join(lines)


def _write_outputs(result: BenchmarkModelComparisonResult, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "model_comparison.md").write_text(result.markdown, encoding="utf-8")
    (output_dir / "model_comparison.json").write_text(
        json.dumps(result.json_data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (output_dir / "model_comparison.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=("metric", "baseline", "neural", "winner"))
        writer.writeheader()
        writer.writerows(result.csv_rows)


def _resolve_status(*, errors: list[str], warnings: list[str]) -> str:
    if errors:
        return "fail"
    if warnings:
        return "review_required"
    return "pass"


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


def _int_mapping(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {str(key): _as_int(item) for key, item in value.items()}


def _is_number(value: Any) -> bool:
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def _markdown_dict(
    values: dict[str, Any],
    *,
    fallback: str | None = None,
) -> list[str]:
    if not values and fallback is not None:
        return [f"- {fallback}"]
    return [f"- {key}: `{value}`" for key, value in sorted(values.items())]


def _markdown_list(values: tuple[str, ...], fallback: str | None = None) -> list[str]:
    if not values and fallback is not None:
        return [f"- {fallback}"]
    return [f"- {value}" for value in values]
