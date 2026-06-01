"""Synthetic ML benchmark orchestration for report-derived datasets."""

from __future__ import annotations

import json
import shutil
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sp63_core.dataset import (
    analyze_synthetic_dataset_balance,
    build_report_dataset_feature_set,
    export_dataset_from_report_archive,
    generate_guided_synthetic_inputs,
    run_report_dataset_quality_gate,
)
from sp63_core.ml.report_baseline import build_report_baseline_ml_result
from sp63_core.ml.report_neural_surrogate import build_report_neural_surrogate_result
from sp63_core.report import build_batch_design_reports, validate_batch_report_archive

SYNTHETIC_ML_BENCHMARK_REPORT_TYPE = "synthetic_ml_benchmark"
SYNTHETIC_ML_BENCHMARK_WARNING = (
    "Synthetic benchmark is not external validation. ML remains advisory-only. "
    "Deterministic SP63 verification and engineer review are mandatory."
)


@dataclass(frozen=True)
class SyntheticMLBenchmarkResult:
    """Result of the synthetic benchmark pipeline."""

    status: str
    benchmark_status: str
    output_dir: str
    target_distribution_goal: dict[str, int]
    final_distribution: dict[str, int]
    generated_count: int
    accepted_count: int
    rejected_count: int
    report_count: int
    dataset_row_count: int
    balance_status: str
    quality_status: str
    feature_status: str
    baseline_status: str
    neural_status: str
    baseline_metrics: dict[str, Any]
    neural_metrics: dict[str, Any]
    recommendations: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    synthetic_data_only: bool = True
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True


def run_synthetic_ml_benchmark(
    *,
    output_dir: Path,
    target_distribution_goal: Mapping[str, int],
    seed: int = 42,
    max_attempts: int = 5000,
    include_serviceability: bool = True,
    target: str = "overall_status",
    feature_mode: str = "input_only",
    create_reports: bool = True,
) -> SyntheticMLBenchmarkResult:
    """Run guided synthetic generation through the report-derived ML benchmark."""
    output = Path(output_dir)
    guided_dir = output / "guided_inputs"
    batch_dir = output / "batch_reports"
    dataset_dir = output / "dataset"
    jsonl_path = dataset_dir / "synthetic_dataset.jsonl"
    csv_path = dataset_dir / "synthetic_dataset.csv"

    _prepare_output_dir(output, create_reports=create_reports)

    warnings: list[str] = [
        SYNTHETIC_ML_BENCHMARK_WARNING,
        "synthetic benchmark metrics are not production evidence",
        "synthetic data only; material verification and external validation are separate",
    ]
    errors: list[str] = []
    recommendations: list[str] = []

    guided = generate_guided_synthetic_inputs(
        output_dir=guided_dir,
        target_distribution_goal=target_distribution_goal,
        seed=seed,
        max_attempts=max_attempts,
        include_serviceability=include_serviceability,
    )
    warnings.extend(guided.warnings)
    errors.extend(guided.errors)

    report_count = 0
    dataset_row_count = 0
    balance_status = "not_run"
    quality_status = "not_run"
    feature_status = "not_run"
    baseline_status = "not_run"
    neural_status = "not_run"
    baseline_metrics: dict[str, Any] = {}
    neural_metrics: dict[str, Any] = {}

    if not create_reports:
        warnings.append("report, dataset, baseline, and neural stages were skipped by --no-reports")
    else:
        input_paths = tuple(sorted(guided_dir.glob("case_*.json")))
        if not input_paths:
            errors.append("guided generation produced no input JSON cases")
        else:
            batch = build_batch_design_reports(
                input_paths=input_paths,
                output_dir=batch_dir,
                include_html=True,
            )
            report_count = batch.report_count
            warnings.extend(batch.warnings)

            archive_validation = validate_batch_report_archive(batch_dir)
            if archive_validation.status != "pass":
                errors.extend(archive_validation.errors)
                warnings.extend(archive_validation.warnings)

            dataset_dir.mkdir(parents=True, exist_ok=True)
            export_jsonl = export_dataset_from_report_archive(
                source_path=batch_dir,
                output_path=jsonl_path,
                output_format="jsonl",
            )
            warnings.extend(export_jsonl.warnings)
            errors.extend(export_jsonl.errors)
            dataset_row_count = export_jsonl.row_count
            if export_jsonl.status != "pass":
                errors.append("dataset export did not pass")
            if export_jsonl.status == "pass":
                export_csv = export_dataset_from_report_archive(
                    source_path=batch_dir,
                    output_path=csv_path,
                    output_format="csv",
                )
                warnings.extend(export_csv.warnings)
                errors.extend(export_csv.errors)

            if jsonl_path.exists() and not errors:
                (
                    balance_status,
                    quality_status,
                    feature_status,
                    baseline_status,
                    neural_status,
                    baseline_metrics,
                    neural_metrics,
                    stage_warnings,
                    stage_errors,
                    stage_recommendations,
                ) = _run_dataset_ml_stages(
                    dataset_path=jsonl_path,
                    target=target,
                    feature_mode=feature_mode,
                    seed=seed,
                )
                warnings.extend(stage_warnings)
                errors.extend(stage_errors)
                recommendations.extend(stage_recommendations)

    if guided.final_distribution != guided.target_distribution_goal:
        warnings.append("guided generation did not reach the requested target distribution")
    if dataset_row_count and dataset_row_count < 100:
        warnings.append("benchmark dataset row count is below 100")
    if _missing_required_classes(guided.final_distribution):
        errors.append("guided generation did not produce every required target class")
    if quality_status == "fail":
        errors.append("dataset quality gate failed")
    if feature_status == "fail":
        errors.append("feature set gate failed")
    if baseline_status == "fail":
        errors.append("baseline ML report failed")
    if neural_status == "fail":
        errors.append("neural surrogate report failed")

    benchmark_status = _resolve_benchmark_status(
        errors=errors,
        warnings=warnings,
        dataset_row_count=dataset_row_count,
        balance_status=balance_status,
        quality_status=quality_status,
        feature_status=feature_status,
        baseline_status=baseline_status,
        neural_status=neural_status,
        create_reports=create_reports,
    )
    result = SyntheticMLBenchmarkResult(
        status=benchmark_status,
        benchmark_status=benchmark_status,
        output_dir=str(output),
        target_distribution_goal=guided.target_distribution_goal,
        final_distribution=guided.final_distribution,
        generated_count=guided.generated_count,
        accepted_count=guided.accepted_count,
        rejected_count=guided.rejected_count,
        report_count=report_count,
        dataset_row_count=dataset_row_count,
        balance_status=balance_status,
        quality_status=quality_status,
        feature_status=feature_status,
        baseline_status=baseline_status,
        neural_status=neural_status,
        baseline_metrics=baseline_metrics,
        neural_metrics=neural_metrics,
        recommendations=tuple(dict.fromkeys(recommendations)),
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(dict.fromkeys(errors)),
    )
    _write_benchmark_outputs(result)
    return result


def _run_dataset_ml_stages(
    *,
    dataset_path: Path,
    target: str,
    feature_mode: str,
    seed: int,
) -> tuple[
    str,
    str,
    str,
    str,
    str,
    dict[str, Any],
    dict[str, Any],
    list[str],
    list[str],
    list[str],
]:
    warnings: list[str] = []
    errors: list[str] = []
    recommendations: list[str] = []

    balance = analyze_synthetic_dataset_balance(
        dataset_path=dataset_path,
        target=target,
        min_rows=100,
        min_class_count=20,
        random_state=seed,
    )
    warnings.extend(balance.warnings)
    errors.extend(balance.errors)
    recommendations.extend(balance.recommendations)

    quality = run_report_dataset_quality_gate(
        dataset_path=dataset_path,
        min_rows=100,
        require_status_diversity=target == "overall_status",
    )
    warnings.extend(quality.warnings)
    errors.extend(quality.errors)

    feature = build_report_dataset_feature_set(
        dataset_path=dataset_path,
        target=target,
        feature_mode=feature_mode,
        random_state=seed,
    )
    warnings.extend(feature.warnings)
    errors.extend(feature.errors)
    if set(feature.feature_columns).intersection(feature.excluded_leakage_columns):
        errors.append("leakage columns are included in selected feature columns")

    baseline = build_report_baseline_ml_result(
        dataset_path=dataset_path,
        target=target,
        feature_mode=feature_mode,
        random_state=seed,
    )
    warnings.extend(baseline.warnings)
    errors.extend(baseline.errors)

    neural = build_report_neural_surrogate_result(
        dataset_path=dataset_path,
        target=target,
        feature_mode=feature_mode,
        random_state=seed,
    )
    warnings.extend(neural.warnings)
    errors.extend(neural.errors)

    return (
        balance.status,
        quality.status,
        feature.status,
        baseline.status,
        neural.status,
        _baseline_summary(baseline),
        _neural_summary(neural),
        warnings,
        errors,
        recommendations,
    )


def _baseline_summary(result: Any) -> dict[str, Any]:
    return {
        "status": result.status,
        "model_name": result.model_name,
        "metrics": result.metrics,
        "confusion_matrix": result.confusion_matrix,
        "target_distribution": result.target_distribution,
        "feature_mode": result.feature_mode,
        "feature_columns": list(result.feature_columns),
        "excluded_leakage_columns": list(result.excluded_leakage_columns),
    }


def _neural_summary(result: Any) -> dict[str, Any]:
    return {
        "status": result.status,
        "model_name": result.model_name,
        "neural_network_used": result.neural_network_used,
        "metrics": result.metrics,
        "confusion_matrix": result.confusion_matrix,
        "target_distribution": result.target_distribution,
        "feature_mode": result.feature_mode,
        "feature_columns": list(result.feature_columns),
        "excluded_leakage_columns": list(result.excluded_leakage_columns),
    }


def _resolve_benchmark_status(
    *,
    errors: list[str],
    warnings: list[str],
    dataset_row_count: int,
    balance_status: str,
    quality_status: str,
    feature_status: str,
    baseline_status: str,
    neural_status: str,
    create_reports: bool,
) -> str:
    if errors:
        return "fail"
    if not create_reports:
        return "review_required"
    if dataset_row_count < 100:
        return "review_required"
    if any(
        status == "review_required"
        for status in (
            balance_status,
            quality_status,
            feature_status,
            baseline_status,
            neural_status,
        )
    ):
        return "review_required"
    return "review_required" if warnings else "pass"


def _missing_required_classes(distribution: Mapping[str, int]) -> tuple[str, ...]:
    return tuple(
        class_name
        for class_name in ("pass", "fail", "review_or_fail")
        if int(distribution.get(class_name, 0)) <= 0
    )


def _write_benchmark_outputs(result: SyntheticMLBenchmarkResult) -> None:
    output = Path(result.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    payload = {
        "report_type": SYNTHETIC_ML_BENCHMARK_REPORT_TYPE,
        **asdict(result),
    }
    (output / "benchmark_report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown = _render_benchmark_markdown(result)
    (output / "benchmark_report.md").write_text(markdown, encoding="utf-8")
    (output / "README_BENCHMARK.md").write_text(markdown, encoding="utf-8")


def _render_benchmark_markdown(result: SyntheticMLBenchmarkResult) -> str:
    baseline_metrics = result.baseline_metrics.get("metrics", {})
    neural_metrics = result.neural_metrics.get("metrics", {})
    lines = [
        "# Synthetic ML Benchmark - Advisory Only",
        "",
        SYNTHETIC_ML_BENCHMARK_WARNING,
        "",
        "## Purpose",
        "",
        "This benchmark connects guided synthetic inputs, deterministic design reports, "
        "report-derived dataset export, dataset gates, baseline ML, and neural surrogate "
        "smoke checks for synthetic ML experiments.",
        "",
        "## Target Distribution Goal",
        "",
        _markdown_dict(result.target_distribution_goal),
        "",
        "## Final Distribution",
        "",
        _markdown_dict(result.final_distribution),
        "",
        "## Dataset Quality Summary",
        "",
        f"- benchmark_status: `{result.benchmark_status}`",
        f"- generated_count: `{result.generated_count}`",
        f"- accepted_count: `{result.accepted_count}`",
        f"- rejected_count: `{result.rejected_count}`",
        f"- report_count: `{result.report_count}`",
        f"- dataset_row_count: `{result.dataset_row_count}`",
        f"- balance_status: `{result.balance_status}`",
        f"- quality_status: `{result.quality_status}`",
        f"- feature_status: `{result.feature_status}`",
        "",
        "## Baseline ML Summary",
        "",
        f"- baseline_status: `{result.baseline_status}`",
        f"- model_name: `{result.baseline_metrics.get('model_name', 'not_run')}`",
        f"- accuracy: `{baseline_metrics.get('accuracy', 'not_available')}`",
        f"- macro_f1: `{baseline_metrics.get('macro_f1', 'not_available')}`",
        f"- weighted_f1: `{baseline_metrics.get('weighted_f1', 'not_available')}`",
        "",
        "## Neural Surrogate Summary",
        "",
        f"- neural_status: `{result.neural_status}`",
        f"- model_name: `{result.neural_metrics.get('model_name', 'not_run')}`",
        f"- neural_network_used: `{result.neural_metrics.get('neural_network_used', False)}`",
        f"- accuracy: `{neural_metrics.get('accuracy', 'not_available')}`",
        f"- macro_f1: `{neural_metrics.get('macro_f1', 'not_available')}`",
        f"- weighted_f1: `{neural_metrics.get('weighted_f1', 'not_available')}`",
        "",
        "## Metrics Comparison",
        "",
        "| metric | baseline | neural |",
        "|---|---:|---:|",
        f"| accuracy | {baseline_metrics.get('accuracy', 'n/a')} | "
        f"{neural_metrics.get('accuracy', 'n/a')} |",
        f"| macro_f1 | {baseline_metrics.get('macro_f1', 'n/a')} | "
        f"{neural_metrics.get('macro_f1', 'n/a')} |",
        f"| weighted_f1 | {baseline_metrics.get('weighted_f1', 'n/a')} | "
        f"{neural_metrics.get('weighted_f1', 'n/a')} |",
        "",
        "## Recommendations",
        "",
    ]
    lines.extend(_markdown_list(result.recommendations, fallback="No recommendations."))
    lines.extend(
        [
            "",
            "## Warnings",
            "",
        ]
    )
    lines.extend(_markdown_list(result.warnings, fallback="No warnings."))
    if result.errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(_markdown_list(result.errors))
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
            "- deterministic SP63 checks remain mandatory",
            "- engineer review is required",
            "",
        ]
    )
    return "\n".join(lines)


def _markdown_dict(values: Mapping[str, Any]) -> str:
    return "\n".join(f"- {key}: `{value}`" for key, value in sorted(values.items()))


def _markdown_list(values: tuple[str, ...], fallback: str | None = None) -> list[str]:
    if not values and fallback is not None:
        return [f"- {fallback}"]
    return [f"- {value}" for value in values]


def _prepare_output_dir(output_dir: Path, *, create_reports: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "guided_inputs",
        "dataset",
        "benchmark_report.json",
        "benchmark_report.md",
        "README_BENCHMARK.md",
    ):
        _remove_generated_path(output_dir / name)
    if create_reports:
        _remove_generated_path(output_dir / "batch_reports")


def _remove_generated_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
