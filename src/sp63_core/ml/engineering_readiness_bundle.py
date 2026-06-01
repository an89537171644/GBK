"""Engineering ML readiness bundle for advisory-only ML review.

This module aggregates existing readiness reports. It does not train models,
does not approve ML for project use, and does not change deterministic
calculation logic.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sp63_core.dataset import run_report_dataset_quality_gate
from sp63_core.ml.external_readiness import evaluate_ml_external_validation_readiness
from sp63_core.ml.material_readiness import evaluate_ml_material_verification_readiness

BUNDLE_REPORT_TYPE = "engineering_ml_readiness_bundle"
PROJECT_USE_WARNING = (
    "engineering ML readiness bundle does not approve ML for project use; "
    "ML remains advisory-only and deterministic SP63 verification is mandatory"
)
SYNTHETIC_WARNING = "synthetic/report-derived data is not external validation"


@dataclass(frozen=True)
class EngineeringMLReadinessBundleResult:
    """Aggregated engineering readiness result for advisory ML evidence."""

    status: str
    readiness_status: str
    output_dir: str | None
    dataset_path: str
    row_count: int
    external_validation_present: bool
    external_validation_status: str
    external_case_count: int
    accepted_external_case_count: int
    failed_external_case_count: int
    external_match_rate: float | None
    material_verification_present: bool
    material_verification_complete: bool
    material_coverage_ratio: float | None
    material_ready_for_engineering_review: bool
    benchmark_evidence_present: bool
    benchmark_status: str
    benchmark_trend_status: str | None
    model_comparison_status: str | None
    proposal_evidence_present: bool
    proposal_status: str | None
    proposal_ready_for_review: bool
    ml_ready_for_research: bool
    ml_ready_for_engineering_review: bool
    ml_ready_for_project_use: bool
    readiness_matrix: tuple[dict[str, Any], ...]
    recommendations: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    markdown: str
    json_data: dict[str, Any]
    synthetic_data_only: bool = True
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True


def build_engineering_ml_readiness_bundle(
    *,
    dataset_path: Path,
    output_dir: Path | None = None,
    dataset_format: str | None = None,
    external_validation_csv: Path | None = None,
    material_verification_csv: Path | None = None,
    benchmark_report_path: Path | None = None,
    benchmark_trend_report_path: Path | None = None,
    model_comparison_report_path: Path | None = None,
    ml_proposal_package_json: Path | None = None,
) -> EngineeringMLReadinessBundleResult:
    """Build an advisory-only engineering ML readiness bundle."""
    dataset = Path(dataset_path)
    warnings: list[str] = [PROJECT_USE_WARNING, SYNTHETIC_WARNING]
    errors: list[str] = []
    recommendations: list[str] = []

    quality = None
    try:
        quality = run_report_dataset_quality_gate(
            dataset_path=dataset,
            dataset_format=dataset_format,
            min_rows=1,
            require_status_diversity=False,
        )
        warnings.extend(quality.warnings)
        errors.extend(quality.errors)
    except (FileNotFoundError, ValueError, OSError) as exc:
        errors.append(f"dataset quality gate cannot be run: {exc}")

    external_result = evaluate_ml_external_validation_readiness(
        dataset_path=dataset,
        external_validation_csv=external_validation_csv,
        material_verification_csv=material_verification_csv,
    )
    warnings.extend(external_result.warnings)
    errors.extend(external_result.errors)
    recommendations.extend(external_result.recommendations)

    material_result = None
    if material_verification_csv is not None:
        material_result = evaluate_ml_material_verification_readiness(
            dataset_path=dataset,
            material_verification_csv=material_verification_csv,
            dataset_format=dataset_format,
        )
        warnings.extend(material_result.warnings)
        errors.extend(material_result.errors)
    else:
        recommendations.append("provide engineer-filled material verification CSV")

    benchmark = _benchmark_evidence(
        benchmark_report_path=benchmark_report_path,
        benchmark_trend_report_path=benchmark_trend_report_path,
        model_comparison_report_path=model_comparison_report_path,
        warnings=warnings,
        errors=errors,
        recommendations=recommendations,
    )
    proposal = _proposal_evidence(
        ml_proposal_package_json=ml_proposal_package_json,
        warnings=warnings,
        errors=errors,
        recommendations=recommendations,
    )

    row_count = quality.row_count if quality is not None else external_result.row_count
    dataset_quality_status = "missing" if quality is None else quality.status
    material_present = (
        external_result.material_verification_present
        if material_result is None
        else material_result.material_verification_present
    )
    material_complete = (
        external_result.material_verification_complete
        if material_result is None
        else material_result.material_verification_complete
    )
    material_coverage_ratio = (
        external_result.material_coverage_ratio
        if material_result is None
        else material_result.material_coverage_ratio
    )
    material_ready = (
        external_result.material_ready_for_engineering_review
        if material_result is None
        else material_result.material_ready_for_engineering_review
    )

    benchmark_evidence_present = (
        benchmark["benchmark_report_present"]
        or benchmark["benchmark_trend_present"]
        or benchmark["model_comparison_present"]
    )
    proposal_evidence_present = proposal["proposal_evidence_present"]

    ml_ready_for_research = (
        quality is not None
        and dataset_quality_status != "fail"
        and row_count > 0
        and external_result.deterministic_checks_required
        and external_result.ml_is_advisory_only
        and external_result.requires_engineer_review
        and not _has_dataset_errors(errors)
    )
    ml_ready_for_engineering_review = (
        ml_ready_for_research
        and external_result.external_validation_present
        and external_result.accepted_external_case_count > 0
        and external_result.failed_external_case_count == 0
        and material_ready
        and not _has_evidence_failures(
            external_status=external_result.status,
            material_result_status=None if material_result is None else material_result.status,
            benchmark_status=benchmark["benchmark_status"],
            benchmark_trend_status=benchmark["benchmark_trend_status"],
            model_comparison_status=benchmark["model_comparison_status"],
            proposal_status=proposal["proposal_status"],
        )
    )
    ml_ready_for_project_use = False

    if not benchmark_evidence_present:
        warnings.append("benchmark/model-comparison evidence is not provided")
        recommendations.append("attach benchmark trend and model comparison reports")
    if not proposal_evidence_present:
        warnings.append("ML proposal package evidence is not provided")
        recommendations.append("attach an advisory ML proposal package before proposal review")
    if ml_ready_for_engineering_review:
        recommendations.append("continue with engineer review; project use remains prohibited")
    else:
        recommendations.append("complete external validation and material verification evidence")

    readiness_matrix = _build_readiness_matrix(
        dataset_quality_status=dataset_quality_status,
        external_result=external_result,
        material_present=material_present,
        material_complete=material_complete,
        material_ready=material_ready,
        benchmark=benchmark,
        proposal=proposal,
    )
    status = _bundle_status(
        errors=errors,
        dataset_quality_status=dataset_quality_status,
        external_status=external_result.status,
        material_status=None if material_result is None else material_result.status,
        warnings=warnings,
        ml_ready_for_engineering_review=ml_ready_for_engineering_review,
    )
    readiness_status = status
    unique_warnings = tuple(dict.fromkeys(warnings))
    unique_errors = tuple(dict.fromkeys(errors))
    unique_recommendations = tuple(dict.fromkeys(recommendations))

    json_data = _json_data(
        status=status,
        readiness_status=readiness_status,
        output_dir=None if output_dir is None else str(Path(output_dir)),
        dataset_path=str(dataset),
        row_count=row_count,
        dataset_quality_status=dataset_quality_status,
        external_result=external_result,
        material_present=material_present,
        material_complete=material_complete,
        material_coverage_ratio=material_coverage_ratio,
        material_ready=material_ready,
        benchmark=benchmark,
        proposal=proposal,
        ml_ready_for_research=ml_ready_for_research,
        ml_ready_for_engineering_review=ml_ready_for_engineering_review,
        ml_ready_for_project_use=ml_ready_for_project_use,
        readiness_matrix=readiness_matrix,
        recommendations=unique_recommendations,
        warnings=unique_warnings,
        errors=unique_errors,
    )
    markdown = _render_markdown(json_data)
    result = EngineeringMLReadinessBundleResult(
        status=status,
        readiness_status=readiness_status,
        output_dir=None if output_dir is None else str(Path(output_dir)),
        dataset_path=str(dataset),
        row_count=row_count,
        external_validation_present=external_result.external_validation_present,
        external_validation_status=external_result.status,
        external_case_count=external_result.external_case_count,
        accepted_external_case_count=external_result.accepted_external_case_count,
        failed_external_case_count=external_result.failed_external_case_count,
        external_match_rate=external_result.external_match_rate,
        material_verification_present=material_present,
        material_verification_complete=material_complete,
        material_coverage_ratio=material_coverage_ratio,
        material_ready_for_engineering_review=material_ready,
        benchmark_evidence_present=benchmark_evidence_present,
        benchmark_status=benchmark["benchmark_status"],
        benchmark_trend_status=benchmark["benchmark_trend_status"],
        model_comparison_status=benchmark["model_comparison_status"],
        proposal_evidence_present=proposal_evidence_present,
        proposal_status=proposal["proposal_status"],
        proposal_ready_for_review=proposal["proposal_ready_for_review"],
        ml_ready_for_research=ml_ready_for_research,
        ml_ready_for_engineering_review=ml_ready_for_engineering_review,
        ml_ready_for_project_use=ml_ready_for_project_use,
        readiness_matrix=readiness_matrix,
        recommendations=unique_recommendations,
        warnings=unique_warnings,
        errors=unique_errors,
        markdown=markdown,
        json_data=json_data,
        synthetic_data_only=True,
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
    )
    if output_dir is not None:
        _write_output_files(result, Path(output_dir))
    return result


def render_readiness_matrix_csv(matrix: tuple[dict[str, Any], ...]) -> str:
    """Render readiness matrix rows as CSV text."""
    fieldnames = (
        "check",
        "status",
        "ready_for_research",
        "ready_for_engineering_review",
        "ready_for_project_use",
        "notes",
    )
    lines: list[str] = []
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in matrix:
        writer.writerow({key: row.get(key, "") for key in fieldnames})
    lines.append(buffer.getvalue())
    return "".join(lines)


def _benchmark_evidence(
    *,
    benchmark_report_path: Path | None,
    benchmark_trend_report_path: Path | None,
    model_comparison_report_path: Path | None,
    warnings: list[str],
    errors: list[str],
    recommendations: list[str],
) -> dict[str, Any]:
    benchmark = _load_json_report(benchmark_report_path, errors, "benchmark report")
    trend = _load_json_report(benchmark_trend_report_path, errors, "benchmark trend report")
    comparison = _load_json_report(
        model_comparison_report_path,
        errors,
        "model comparison report",
    )
    for report, name in (
        (benchmark, "benchmark"),
        (trend, "benchmark trend"),
        (comparison, "model comparison"),
    ):
        if report:
            warnings.extend(_string_tuple(report.get("warnings")))
            errors.extend(
                f"{name} evidence reports error: {error}"
                for error in _string_tuple(report.get("errors"))
            )
            recommendations.extend(_string_tuple(report.get("recommendations")))

    return {
        "benchmark_report_present": benchmark is not None,
        "benchmark_trend_present": trend is not None,
        "model_comparison_present": comparison is not None,
        "benchmark_status": _report_status(
            benchmark,
            preferred_keys=("benchmark_status", "status"),
        ),
        "benchmark_trend_status": _report_status(
            trend,
            preferred_keys=("trend_status", "status"),
        ),
        "model_comparison_status": _report_status(
            comparison,
            preferred_keys=("comparison_status", "status"),
        ),
    }


def _proposal_evidence(
    *,
    ml_proposal_package_json: Path | None,
    warnings: list[str],
    errors: list[str],
    recommendations: list[str],
) -> dict[str, Any]:
    proposal = _load_json_report(
        ml_proposal_package_json,
        errors,
        "ML proposal package",
    )
    if proposal:
        warnings.extend(_string_tuple(proposal.get("warnings")))
        errors.extend(
            f"ML proposal package reports error: {error}"
            for error in _string_tuple(proposal.get("errors"))
        )
        recommendations.extend(_string_tuple(proposal.get("recommendations")))

    proposal_status = _report_status(proposal, preferred_keys=("proposal_status", "status"))
    proposal_ready_for_review = bool(
        proposal
        and proposal.get("requires_engineer_review") is True
        and proposal.get("ml_is_advisory_only") is True
        and proposal.get("deterministic_checks_required") is True
        and proposal_status not in {"fail", "rejected"}
    )
    return {
        "proposal_evidence_present": proposal is not None,
        "proposal_status": proposal_status,
        "proposal_ready_for_review": proposal_ready_for_review,
    }


def _load_json_report(
    path: Path | None,
    errors: list[str],
    label: str,
) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        errors.append(f"{label} cannot be read: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label} must contain a JSON object")
        return None
    return value


def _build_readiness_matrix(
    *,
    dataset_quality_status: str,
    external_result,
    material_present: bool,
    material_complete: bool,
    material_ready: bool,
    benchmark: dict[str, Any],
    proposal: dict[str, Any],
) -> tuple[dict[str, Any], ...]:
    return (
        _matrix_row(
            check="dataset_quality",
            status=dataset_quality_status,
            ready_for_research=dataset_quality_status != "fail",
            ready_for_engineering_review=dataset_quality_status != "fail",
            ready_for_project_use=False,
            notes="report-derived dataset is readable and advisory flags are checked",
        ),
        _matrix_row(
            check="external_validation",
            status=external_result.status,
            ready_for_research=True,
            ready_for_engineering_review=(
                external_result.external_validation_present
                and external_result.accepted_external_case_count > 0
                and external_result.failed_external_case_count == 0
            ),
            ready_for_project_use=False,
            notes="engineer-filled external validation CSV evidence is required",
        ),
        _matrix_row(
            check="material_verification",
            status="review_required"
            if not material_present or not material_complete
            else "review_required",
            ready_for_research=True,
            ready_for_engineering_review=material_ready,
            ready_for_project_use=False,
            notes="engineer-filled material verification CSV coverage is required",
        ),
        _matrix_row(
            check="benchmark_evidence",
            status=benchmark["benchmark_status"],
            ready_for_research=benchmark["benchmark_report_present"],
            ready_for_engineering_review=benchmark["benchmark_report_present"],
            ready_for_project_use=False,
            notes="synthetic benchmark evidence is optional and not production evidence",
        ),
        _matrix_row(
            check="benchmark_trend",
            status=benchmark["benchmark_trend_status"] or "missing",
            ready_for_research=benchmark["benchmark_trend_present"],
            ready_for_engineering_review=benchmark["benchmark_trend_present"],
            ready_for_project_use=False,
            notes="trend evidence supports review only when supplied",
        ),
        _matrix_row(
            check="model_comparison",
            status=benchmark["model_comparison_status"] or "missing",
            ready_for_research=benchmark["model_comparison_present"],
            ready_for_engineering_review=benchmark["model_comparison_present"],
            ready_for_project_use=False,
            notes="model comparison metrics are synthetic-only evidence",
        ),
        _matrix_row(
            check="ml_proposal_package",
            status=proposal["proposal_status"] or "missing",
            ready_for_research=proposal["proposal_evidence_present"],
            ready_for_engineering_review=proposal["proposal_ready_for_review"],
            ready_for_project_use=False,
            notes="proposal packages must remain advisory and deterministic-verified",
        ),
    )


def _matrix_row(
    *,
    check: str,
    status: str | None,
    ready_for_research: bool,
    ready_for_engineering_review: bool,
    ready_for_project_use: bool,
    notes: str,
) -> dict[str, Any]:
    return {
        "check": check,
        "status": status or "missing",
        "ready_for_research": ready_for_research,
        "ready_for_engineering_review": ready_for_engineering_review,
        "ready_for_project_use": ready_for_project_use,
        "notes": notes,
    }


def _json_data(
    *,
    status: str,
    readiness_status: str,
    output_dir: str | None,
    dataset_path: str,
    row_count: int,
    dataset_quality_status: str,
    external_result,
    material_present: bool,
    material_complete: bool,
    material_coverage_ratio: float | None,
    material_ready: bool,
    benchmark: dict[str, Any],
    proposal: dict[str, Any],
    ml_ready_for_research: bool,
    ml_ready_for_engineering_review: bool,
    ml_ready_for_project_use: bool,
    readiness_matrix: tuple[dict[str, Any], ...],
    recommendations: tuple[str, ...],
    warnings: tuple[str, ...],
    errors: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "report_type": BUNDLE_REPORT_TYPE,
        "status": status,
        "readiness_status": readiness_status,
        "output_dir": output_dir,
        "dataset_path": dataset_path,
        "row_count": row_count,
        "dataset_quality_status": dataset_quality_status,
        "external_validation_present": external_result.external_validation_present,
        "external_validation_status": external_result.status,
        "external_case_count": external_result.external_case_count,
        "accepted_external_case_count": external_result.accepted_external_case_count,
        "failed_external_case_count": external_result.failed_external_case_count,
        "external_match_rate": external_result.external_match_rate,
        "material_verification_present": material_present,
        "material_verification_complete": material_complete,
        "material_coverage_ratio": material_coverage_ratio,
        "material_ready_for_engineering_review": material_ready,
        "benchmark_evidence_present": (
            benchmark["benchmark_report_present"]
            or benchmark["benchmark_trend_present"]
            or benchmark["model_comparison_present"]
        ),
        "benchmark_status": benchmark["benchmark_status"],
        "benchmark_trend_status": benchmark["benchmark_trend_status"],
        "model_comparison_status": benchmark["model_comparison_status"],
        "proposal_evidence_present": proposal["proposal_evidence_present"],
        "proposal_status": proposal["proposal_status"],
        "proposal_ready_for_review": proposal["proposal_ready_for_review"],
        "ml_ready_for_research": ml_ready_for_research,
        "ml_ready_for_engineering_review": ml_ready_for_engineering_review,
        "ml_ready_for_project_use": ml_ready_for_project_use,
        "readiness_matrix": list(readiness_matrix),
        "recommendations": list(recommendations),
        "warnings": list(warnings),
        "errors": list(errors),
        "synthetic_data_only": True,
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
    }


def _render_markdown(data: dict[str, Any]) -> str:
    matrix = data["readiness_matrix"]
    lines = [
        "# Engineering ML Readiness Bundle - Advisory Only",
        "",
        "This bundle does not approve ML for project use. ML remains advisory-only. "
        "Deterministic SP63 verification and engineer review are mandatory.",
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        f"ml_ready_for_project_use = {str(data['ml_ready_for_project_use']).lower()}",
        "",
        "## Dataset Summary",
        "",
        f"- dataset_path: {data['dataset_path']}",
        f"- row_count: {data['row_count']}",
        f"- dataset_quality_status: {data['dataset_quality_status']}",
        "",
        "## External Validation Readiness",
        "",
        f"- external_validation_present: {data['external_validation_present']}",
        f"- external_validation_status: {data['external_validation_status']}",
        f"- external_case_count: {data['external_case_count']}",
        f"- accepted_external_case_count: {data['accepted_external_case_count']}",
        f"- failed_external_case_count: {data['failed_external_case_count']}",
        f"- external_match_rate: {_format_optional_float(data['external_match_rate'])}",
        "",
        "## Material Verification Readiness",
        "",
        f"- material_verification_present: {data['material_verification_present']}",
        f"- material_verification_complete: {data['material_verification_complete']}",
        f"- material_coverage_ratio: {_format_optional_float(data['material_coverage_ratio'])}",
        "- material_ready_for_engineering_review: "
        f"{data['material_ready_for_engineering_review']}",
        "",
        "## Benchmark Evidence",
        "",
        f"- benchmark_evidence_present: {data['benchmark_evidence_present']}",
        f"- benchmark_status: {data['benchmark_status']}",
        f"- benchmark_trend_status: {data['benchmark_trend_status'] or '-'}",
        f"- model_comparison_status: {data['model_comparison_status'] or '-'}",
        "",
        "## ML Proposal Evidence",
        "",
        f"- proposal_evidence_present: {data['proposal_evidence_present']}",
        f"- proposal_status: {data['proposal_status'] or '-'}",
        f"- proposal_ready_for_review: {data['proposal_ready_for_review']}",
        "",
        "## Readiness Matrix",
        "",
        "| check | status | research | engineering review | project use | notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        "| {check} | {status} | {ready_for_research} | "
        "{ready_for_engineering_review} | {ready_for_project_use} | {notes} |".format(
            **row
        )
        for row in matrix
    )
    lines.extend(
        [
            "",
            "## Final Readiness Decision",
            "",
            f"- readiness_status: {data['readiness_status']}",
            f"- ml_ready_for_research: {data['ml_ready_for_research']}",
            "- ml_ready_for_engineering_review: "
            f"{data['ml_ready_for_engineering_review']}",
            f"- ml_ready_for_project_use: {data['ml_ready_for_project_use']}",
            "",
            "## Recommendations",
            "",
        ]
    )
    lines.extend(_bullet_lines(data["recommendations"]))
    lines.extend(["", "## Warnings", ""])
    lines.extend(_bullet_lines(data["warnings"]))
    lines.extend(["", "## Errors", ""])
    lines.extend(_bullet_lines(data["errors"]))
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- Synthetic benchmark data is not external validation.",
            "- Material verification does not certify ML output.",
            "- Benchmark metrics are not production evidence.",
            "- Advisory ML proposal packages are not design calculations.",
            "- Project-use readiness remains false in K60.",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_output_files(
    result: EngineeringMLReadinessBundleResult,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "engineering_ml_readiness.md").write_text(
        result.markdown,
        encoding="utf-8",
    )
    (output_dir / "engineering_ml_readiness.json").write_text(
        json.dumps(result.json_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "engineering_ml_readiness_matrix.csv").write_text(
        render_readiness_matrix_csv(result.readiness_matrix),
        encoding="utf-8",
    )
    (output_dir / "README_REVIEW.md").write_text(
        _review_readme(result),
        encoding="utf-8",
    )


def _review_readme(result: EngineeringMLReadinessBundleResult) -> str:
    return "\n".join(
        [
            "# Engineering ML Readiness Review Package",
            "",
            "This package is for engineer review only. It does not approve ML for "
            "project use and does not replace deterministic SP63 verification.",
            "",
            "## Included Files",
            "",
            "- `engineering_ml_readiness.md` - human-readable readiness report.",
            "- `engineering_ml_readiness.json` - machine-readable readiness summary.",
            "- `engineering_ml_readiness_matrix.csv` - readiness matrix.",
            "- `README_REVIEW.md` - this review guide.",
            "",
            "## How To Review",
            "",
            "1. Check dataset quality and provenance.",
            "2. Check external validation evidence and accepted/failed counts.",
            "3. Check material verification coverage.",
            "4. Treat benchmark and proposal evidence as advisory-only.",
            "5. Confirm deterministic SP63 verification remains mandatory.",
            "",
            "## Current Decision",
            "",
            f"- status: {result.status}",
            f"- ml_ready_for_research: {result.ml_ready_for_research}",
            "- ml_ready_for_engineering_review: "
            f"{result.ml_ready_for_engineering_review}",
            f"- ml_ready_for_project_use: {result.ml_ready_for_project_use}",
            f"- requires_engineer_review: {result.requires_engineer_review}",
            f"- ml_is_advisory_only: {result.ml_is_advisory_only}",
            "- deterministic_checks_required: "
            f"{result.deterministic_checks_required}",
            "",
            "## Required Warnings",
            "",
            "- ML remains advisory-only.",
            "- Deterministic SP63 checks are mandatory.",
            "- Engineer review is required.",
            "- Material verification and external validation are separate gates.",
            "- Synthetic evidence is not production evidence.",
            "",
        ]
    )


def _bundle_status(
    *,
    errors: list[str],
    dataset_quality_status: str,
    external_status: str,
    material_status: str | None,
    warnings: list[str],
    ml_ready_for_engineering_review: bool,
) -> str:
    if (
        errors
        or dataset_quality_status == "fail"
        or external_status == "fail"
        or material_status == "fail"
    ):
        return "fail"
    if ml_ready_for_engineering_review and not warnings:
        return "pass"
    return "review_required"


def _has_dataset_errors(errors: list[str]) -> bool:
    return any(
        "dataset" in error
        or "quality gate" in error
        or "archive_validation_status" in error
        for error in errors
    )


def _has_evidence_failures(
    *,
    external_status: str,
    material_result_status: str | None,
    benchmark_status: str,
    benchmark_trend_status: str | None,
    model_comparison_status: str | None,
    proposal_status: str | None,
) -> bool:
    statuses = (
        external_status,
        material_result_status,
        benchmark_status,
        benchmark_trend_status,
        model_comparison_status,
        proposal_status,
    )
    return any(status in {"fail", "rejected"} for status in statuses if status is not None)


def _report_status(report: dict[str, Any] | None, *, preferred_keys: tuple[str, ...]) -> str:
    if report is None:
        return "missing"
    for key in preferred_keys:
        value = report.get(key)
        if value:
            return str(value)
    return "review_required"


def _string_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item))
    if isinstance(value, str) and value:
        return (value,)
    return ()


def _bullet_lines(values: list[str] | tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]


def _format_optional_float(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.6g}"


def as_payload(result: EngineeringMLReadinessBundleResult) -> dict[str, Any]:
    """Return a dataclass payload without duplicating nested JSON fields by reference."""
    return asdict(result)
