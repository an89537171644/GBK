"""Release candidate report for the draft engineering workflow package."""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

from sp63_core.materials import build_material_audit_rows
from sp63_core.validation import (
    build_external_validation_summary,
    load_external_validation_csv,
    run_bending_golden_cases,
    run_crack_formation_golden_cases,
    run_crack_width_golden_cases,
    run_deflection_golden_cases,
    run_design_golden_cases,
    run_manual_verification_cases,
    run_shear_golden_cases,
)
from sp63_core.workflows.engineering_workflow import run_engineering_workflow
from sp63_core.workflows.input_form_schema import build_input_form_schema
from sp63_core.workflows.input_preflight import run_input_preflight
from sp63_core.workflows.protected_files_guard import run_protected_files_guard
from sp63_core.workflows.self_check import run_engineering_workflow_self_check
from sp63_core.workflows.user_manual_index import build_user_manual_index

EXAMPLE_INPUT_JSON = Path("docs/reports/examples/rectangular_design_input_example.json")
EXTERNAL_SAMPLE_CSV = Path("docs/validation/samples/external_validation_filled_sample.csv")
RELEASE_CANDIDATE_WARNING = (
    "Release candidate report is review evidence only. It does not publish a "
    "release, certify designs, or approve project use."
)
KNOWN_LIMITATIONS = (
    "not certified",
    "engineer review required",
    "material audit review_required",
    "external validation sample is limited",
    "ML advisory-only",
    "no project use approval",
    "no full GUI yet",
)
RECOMMENDATIONS = (
    "complete engineer material verification before engineering use",
    "complete real external validation with manual/Excel/SCAD/LIRA evidence",
    "review protected-files guard result before merge",
    "keep ML advisory-only and verify every proposal deterministically",
)


@dataclass(frozen=True)
class ReleaseCandidateReportResult:
    """Release candidate report result."""

    status: str
    release_candidate_status: str
    output_dir: str
    version: str
    validation_status: str
    manual_cases_status: str
    materials_audit_status: str
    external_validation_status: str
    workflow_self_check_status: str
    input_form_schema_status: str
    input_preflight_status: str
    report_index_status: str
    protected_files_guard_status: str
    user_manual_status: str
    known_limitations: tuple[str, ...]
    recommendations: tuple[str, ...]
    generated_files: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_release_candidate_report(
    *,
    output_dir: Path,
    version: str = "0.9.0-rc1",
) -> ReleaseCandidateReportResult:
    """Build a draft release candidate report without publishing a release."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = [RELEASE_CANDIDATE_WARNING]
    errors: list[str] = []

    validation_status = _golden_validation_status()
    manual_cases_status = _manual_cases_status()
    materials_audit_status = _materials_audit_status()
    external_validation_status = _external_validation_status()
    workflow_self_check_status = _workflow_self_check_status()
    input_form_schema_status = build_input_form_schema().status
    input_preflight_status = run_input_preflight(EXAMPLE_INPUT_JSON).status
    report_index_status = _report_index_status()
    protected_files_guard = run_protected_files_guard()
    protected_files_guard_status = protected_files_guard.status
    user_manual_status = build_user_manual_index().status
    warnings.extend(protected_files_guard.warnings)
    errors.extend(protected_files_guard.errors)

    release_status = _release_candidate_status(
        validation_status=validation_status,
        manual_cases_status=manual_cases_status,
        materials_audit_status=materials_audit_status,
        external_validation_status=external_validation_status,
        workflow_self_check_status=workflow_self_check_status,
        input_form_schema_status=input_form_schema_status,
        input_preflight_status=input_preflight_status,
        report_index_status=report_index_status,
        protected_files_guard_status=protected_files_guard_status,
        user_manual_status=user_manual_status,
        errors=errors,
    )

    report_json_path = output_path / "release_candidate_report.json"
    report_markdown_path = output_path / "release_candidate_report.md"
    readme_path = output_path / "README_RELEASE_CANDIDATE.md"
    generated_files = (report_json_path, report_markdown_path, readme_path)
    result = ReleaseCandidateReportResult(
        status=release_status,
        release_candidate_status=release_status,
        output_dir=str(output_path),
        version=version,
        validation_status=validation_status,
        manual_cases_status=manual_cases_status,
        materials_audit_status=materials_audit_status,
        external_validation_status=external_validation_status,
        workflow_self_check_status=workflow_self_check_status,
        input_form_schema_status=input_form_schema_status,
        input_preflight_status=input_preflight_status,
        report_index_status=report_index_status,
        protected_files_guard_status=protected_files_guard_status,
        user_manual_status=user_manual_status,
        known_limitations=KNOWN_LIMITATIONS,
        recommendations=RECOMMENDATIONS,
        generated_files=tuple(str(path) for path in generated_files),
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(dict.fromkeys(errors)),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    report_json_path.write_text(
        json.dumps(_release_candidate_payload(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report_markdown_path.write_text(_render_release_candidate_markdown(result), encoding="utf-8")
    readme_path.write_text(_render_release_candidate_readme(result), encoding="utf-8")
    return result


def _golden_validation_status() -> str:
    results = (
        *run_bending_golden_cases(),
        *run_shear_golden_cases(),
        *run_crack_formation_golden_cases(),
        *run_crack_width_golden_cases(),
        *run_deflection_golden_cases(),
        *run_design_golden_cases(),
    )
    return "pass" if all(result.status == "pass" for result in results) else "fail"


def _manual_cases_status() -> str:
    results = run_manual_verification_cases()
    return "pass" if all(result.passed for result in results) else "fail"


def _materials_audit_status() -> str:
    rows = build_material_audit_rows()
    if not rows:
        return "fail"
    if any(row.requires_engineer_review for row in rows):
        return "review_required"
    return "pass"


def _external_validation_status() -> str:
    if not EXTERNAL_SAMPLE_CSV.exists():
        return "review_required"
    rows = load_external_validation_csv(EXTERNAL_SAMPLE_CSV)
    summary = build_external_validation_summary(rows)
    return summary.status


def _workflow_self_check_status() -> str:
    with tempfile.TemporaryDirectory() as tmp_dir:
        result = run_engineering_workflow_self_check(
            output_dir=Path(tmp_dir) / "workflow_self_check",
            cleanup=True,
        )
    return result.status


def _report_index_status() -> str:
    with tempfile.TemporaryDirectory() as tmp_dir:
        result = run_engineering_workflow(
            input_json_path=EXAMPLE_INPUT_JSON,
            output_dir=Path(tmp_dir) / "workflow",
            with_preflight=True,
            with_index=True,
        )
    return result.index_status or "not_run"


def _release_candidate_status(
    *,
    validation_status: str,
    manual_cases_status: str,
    materials_audit_status: str,
    external_validation_status: str,
    workflow_self_check_status: str,
    input_form_schema_status: str,
    input_preflight_status: str,
    report_index_status: str,
    protected_files_guard_status: str,
    user_manual_status: str,
    errors: list[str],
) -> str:
    critical_statuses = (
        validation_status,
        manual_cases_status,
        external_validation_status,
        workflow_self_check_status,
        input_form_schema_status,
        input_preflight_status,
        report_index_status,
        protected_files_guard_status,
        user_manual_status,
    )
    if errors or any(status == "fail" for status in critical_statuses):
        return "fail"
    if materials_audit_status == "review_required":
        return "review_required"
    if any(status == "review_required" for status in critical_statuses):
        return "review_required"
    return "pass"


def _release_candidate_payload(result: ReleaseCandidateReportResult) -> dict[str, object]:
    return {
        "report_type": "release_candidate_report",
        **result.__dict__,
    }


def _render_release_candidate_markdown(result: ReleaseCandidateReportResult) -> str:
    lines = [
        "# Release Candidate Report",
        "",
        RELEASE_CANDIDATE_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Summary",
        "",
        f"- version: `{result.version}`",
        f"- release_candidate_status: `{result.release_candidate_status}`",
        f"- validation_status: `{result.validation_status}`",
        f"- manual_cases_status: `{result.manual_cases_status}`",
        f"- materials_audit_status: `{result.materials_audit_status}`",
        f"- external_validation_status: `{result.external_validation_status}`",
        f"- workflow_self_check_status: `{result.workflow_self_check_status}`",
        f"- input_form_schema_status: `{result.input_form_schema_status}`",
        f"- input_preflight_status: `{result.input_preflight_status}`",
        f"- report_index_status: `{result.report_index_status}`",
        f"- protected_files_guard_status: `{result.protected_files_guard_status}`",
        f"- user_manual_status: `{result.user_manual_status}`",
        "",
        "## Known Limitations",
        "",
        *_bullet_lines(result.known_limitations),
        "",
        "## Recommendations",
        "",
        *_bullet_lines(result.recommendations),
        "",
        "## Warnings",
        "",
        *_bullet_lines(result.warnings),
        "",
        "## Errors",
        "",
        *_bullet_lines(result.errors),
    ]
    return "\n".join(lines) + "\n"


def _render_release_candidate_readme(result: ReleaseCandidateReportResult) -> str:
    lines = [
        "# Release Candidate Review",
        "",
        "This folder contains a draft release candidate report.",
        "It does not publish a release and does not approve project use.",
        "",
        "## Files",
        "",
        "- `release_candidate_report.json`",
        "- `release_candidate_report.md`",
        "- `README_RELEASE_CANDIDATE.md`",
        "",
        "## Status",
        "",
        f"- release_candidate_status: `{result.release_candidate_status}`",
        f"- version: `{result.version}`",
        "",
        "## Safety",
        "",
        "- Engineer review remains mandatory.",
        "- Deterministic SP63 checks remain mandatory.",
        "- Material verification remains a separate engineer gate.",
        "- External validation sample is limited.",
        "- ML remains advisory-only.",
        "- `ml_ready_for_project_use = false`.",
    ]
    return "\n".join(lines) + "\n"


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]
