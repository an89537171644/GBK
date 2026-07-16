"""User acceptance smoke suite for v0.9 readiness review."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
from sp63_core.workflows.docs_audit import build_docs_audit_report
from sp63_core.workflows.engineering_workflow_batch import run_engineering_workflow_batch
from sp63_core.workflows.project_template import build_project_template_package
from sp63_core.workflows.protected_files_guard import run_protected_files_guard
from sp63_core.workflows.release_manifest import build_release_artifact_manifest

USER_ACCEPTANCE_SMOKE_WARNING = (
    "User acceptance smoke suite is review evidence only. It does not certify "
    "designs, approve project use, or make ML project-ready."
)

EXTERNAL_SAMPLE_CSV = Path("docs/validation/samples/external_validation_filled_sample.csv")
BATCH_VALID_INPUT_DIR = Path("docs/reports/examples/batch_valid")


@dataclass(frozen=True)
class UserAcceptanceSmokeResult:
    """User acceptance smoke result."""

    status: str
    user_acceptance_status: str
    output_dir: str
    smoke_count: int
    passed_count: int
    review_required_count: int
    failed_count: int
    smoke_results: tuple[dict[str, Any], ...]
    generated_files: tuple[str, ...]
    summary_json_path: str
    summary_markdown_path: str
    recommendations: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def run_user_acceptance_smoke(
    *,
    output_dir: Path,
    version: str = "0.9.0-rc1",
) -> UserAcceptanceSmokeResult:
    """Run lightweight user acceptance smoke checks without approving project use."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    smoke_results = (
        _smoke("validate --golden", _golden_status()),
        _smoke("manual-cases --json", _manual_cases_status()),
        _smoke("external-validation --sample --json", _external_validation_status()),
        _smoke("materials-audit --json", _materials_audit_status()),
        _smoke("protected-files-check --json", run_protected_files_guard().status),
        _smoke("docs-audit --json", build_docs_audit_report().status),
        _smoke(
            "project-template --json",
            build_project_template_package(output_dir=output_path / "project_template").status,
        ),
        _smoke(
            "engineering-workflow-batch batch_valid --json",
            run_engineering_workflow_batch(
                input_dir=BATCH_VALID_INPUT_DIR,
                output_dir=output_path / "batch_valid",
                with_preflight=True,
                with_index=True,
            ).status,
        ),
        _smoke(
            "release-manifest --json",
            build_release_artifact_manifest(
                output_dir=output_path / "release_manifest",
                version=version,
            ).status,
        ),
    )
    passed_count = sum(1 for result in smoke_results if result["status"] == "pass")
    review_required_count = sum(
        1 for result in smoke_results if result["status"] == "review_required"
    )
    failed_count = sum(1 for result in smoke_results if result["status"] == "fail")
    status = _suite_status(failed_count=failed_count, review_required_count=review_required_count)
    errors = tuple(
        f"smoke failed: {result['name']}"
        for result in smoke_results
        if result["status"] == "fail"
    )
    recommendations = _recommendations(
        failed_count=failed_count,
        review_required_count=review_required_count,
    )

    summary_json_path = output_path / "user_acceptance_smoke.json"
    summary_markdown_path = output_path / "user_acceptance_smoke.md"
    result = UserAcceptanceSmokeResult(
        status=status,
        user_acceptance_status=status,
        output_dir=str(output_path),
        smoke_count=len(smoke_results),
        passed_count=passed_count,
        review_required_count=review_required_count,
        failed_count=failed_count,
        smoke_results=smoke_results,
        generated_files=(str(summary_json_path), str(summary_markdown_path)),
        summary_json_path=str(summary_json_path),
        summary_markdown_path=str(summary_markdown_path),
        recommendations=recommendations,
        warnings=(USER_ACCEPTANCE_SMOKE_WARNING,),
        errors=errors,
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    summary_json_path.write_text(
        json.dumps({"report_type": "user_acceptance_smoke", **result.__dict__}, indent=2),
        encoding="utf-8",
    )
    summary_markdown_path.write_text(_render_user_acceptance_markdown(result), encoding="utf-8")
    return result


def _smoke(name: str, status: str) -> dict[str, Any]:
    return {"name": name, "status": status}


def _golden_status() -> str:
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
    cases = run_manual_verification_cases()
    return "pass" if all(case.passed for case in cases) else "fail"


def _external_validation_status() -> str:
    if not EXTERNAL_SAMPLE_CSV.exists():
        return "review_required"
    rows = load_external_validation_csv(EXTERNAL_SAMPLE_CSV)
    return build_external_validation_summary(rows).status


def _materials_audit_status() -> str:
    rows = build_material_audit_rows()
    if not rows:
        return "fail"
    if any(row.requires_engineer_review for row in rows):
        return "review_required"
    return "pass"


def _suite_status(*, failed_count: int, review_required_count: int) -> str:
    if failed_count:
        return "fail"
    if review_required_count:
        return "review_required"
    return "pass"


def _recommendations(*, failed_count: int, review_required_count: int) -> tuple[str, ...]:
    recommendations: list[str] = []
    if failed_count:
        recommendations.append("fix failed smoke checks before release-candidate review")
    if review_required_count:
        recommendations.append("complete engineer review gates before project use")
    recommendations.append("keep ML advisory-only and verify all proposals deterministically")
    recommendations.append("do not treat smoke success as design certification")
    return tuple(recommendations)


def _render_user_acceptance_markdown(result: UserAcceptanceSmokeResult) -> str:
    lines = [
        "# User Acceptance Smoke Suite",
        "",
        USER_ACCEPTANCE_SMOKE_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Summary",
        "",
        f"- user_acceptance_status: `{result.user_acceptance_status}`",
        f"- smoke_count: `{result.smoke_count}`",
        f"- passed_count: `{result.passed_count}`",
        f"- review_required_count: `{result.review_required_count}`",
        f"- failed_count: `{result.failed_count}`",
        "",
        "## Smoke Results",
        "",
        "| check | status |",
        "|---|---|",
    ]
    for smoke_result in result.smoke_results:
        lines.append(f"| {smoke_result['name']} | `{smoke_result['status']}` |")
    lines.extend(
        [
            "",
            "## Recommendations",
            "",
            *_bullet_lines(result.recommendations),
            "",
            "## Errors",
            "",
            *_bullet_lines(result.errors),
        ]
    )
    return "\n".join(lines) + "\n"


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]
