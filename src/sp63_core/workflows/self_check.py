"""Self-check helpers for the engineering workflow runner."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from sp63_core.workflows.engineering_workflow import (
    ML_DATASET_MISSING_WARNING,
    run_engineering_workflow,
)

EXAMPLE_INPUT_JSON = Path("docs/reports/examples/rectangular_design_input_example.json")
SELF_CHECK_WARNING = (
    "This self-check does not certify the design. Deterministic SP63 "
    "verification and engineer review are mandatory."
)


@dataclass(frozen=True)
class EngineeringWorkflowSelfCheckResult:
    """Summary of the engineering workflow self-check."""

    status: str
    self_check_status: str
    output_dir: str | None
    checked_commands: tuple[str, ...]
    passed_checks: int
    failed_checks: int
    skipped_checks: int
    deterministic_workflow_status: str
    deterministic_archive_status: str
    deterministic_zip_status: str
    ml_workflow_status: str | None
    ml_ready_for_research: bool | None
    ml_ready_for_engineering_review: bool | None
    ml_ready_for_project_use: bool | None
    files_created: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True


def run_engineering_workflow_self_check(
    *,
    output_dir: Path,
    include_ml_readiness: bool = False,
    dataset_path: Path | None = None,
    external_validation_csv: Path | None = None,
    material_verification_csv: Path | None = None,
    cleanup: bool = False,
) -> EngineeringWorkflowSelfCheckResult:
    """Run a smoke self-check for the engineering workflow command."""
    root_output = Path(output_dir)
    root_output.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = [SELF_CHECK_WARNING]
    errors: list[str] = []
    files_created: list[str] = []
    passed_checks = 0
    failed_checks = 0
    skipped_checks = 0

    checked_commands = ["engineering-workflow", "report-archive-validate", "report-archive-zip"]
    deterministic_workflow_status = "not_run"
    deterministic_archive_status = "not_run"
    deterministic_zip_status = "not_run"
    ml_workflow_status: str | None = None
    ml_ready_for_research: bool | None = None
    ml_ready_for_engineering_review: bool | None = None
    ml_ready_for_project_use: bool | None = False

    if EXAMPLE_INPUT_JSON.exists():
        passed_checks += 1
    else:
        failed_checks += 1
        errors.append(f"example input JSON is missing: {EXAMPLE_INPUT_JSON}")

    deterministic_output = root_output / "deterministic_workflow"
    deterministic_result = None
    if not errors:
        deterministic_result = run_engineering_workflow(
            input_json_path=EXAMPLE_INPUT_JSON,
            output_dir=deterministic_output,
        )
        deterministic_workflow_status = deterministic_result.workflow_status
        deterministic_archive_status = deterministic_result.archive_validation_status
        deterministic_zip_status = deterministic_result.zip_status
        warnings.extend(deterministic_result.warnings)
        errors.extend(deterministic_result.errors)
        files_created.extend(deterministic_result.files_created)

        if deterministic_result.errors:
            failed_checks += 1
        else:
            passed_checks += 1

        passed, failed, missing = _check_expected_deterministic_files(deterministic_output)
        passed_checks += passed
        failed_checks += failed
        errors.extend(f"missing deterministic workflow file: {path}" for path in missing)

        if deterministic_result.archive_validation_status == "pass":
            passed_checks += 1
        else:
            failed_checks += 1
            errors.append(
                "deterministic archive validation did not pass: "
                f"{deterministic_result.archive_validation_status}"
            )

        if deterministic_result.zip_status == "pass":
            passed_checks += 1
        else:
            failed_checks += 1
            errors.append(f"deterministic ZIP did not pass: {deterministic_result.zip_status}")

    if include_ml_readiness:
        checked_commands.append("engineering-ml-readiness")
        if dataset_path is None:
            ml_workflow_status = "not_run"
            skipped_checks += 1
            warnings.append(ML_DATASET_MISSING_WARNING)
        else:
            ml_output = root_output / "ml_workflow"
            ml_result = run_engineering_workflow(
                input_json_path=EXAMPLE_INPUT_JSON,
                output_dir=ml_output,
                include_ml_readiness=True,
                dataset_path=dataset_path,
                external_validation_csv=external_validation_csv,
                material_verification_csv=material_verification_csv,
            )
            ml_workflow_status = ml_result.workflow_status
            ml_ready_for_research = ml_result.ml_ready_for_research
            ml_ready_for_engineering_review = ml_result.ml_ready_for_engineering_review
            ml_ready_for_project_use = ml_result.ml_ready_for_project_use
            warnings.extend(ml_result.warnings)
            errors.extend(ml_result.errors)
            files_created.extend(ml_result.files_created)
            if ml_result.errors or ml_result.ml_ready_for_project_use is not False:
                failed_checks += 1
                errors.append("ML readiness workflow did not preserve project-use hard stop")
            else:
                passed_checks += 1
    else:
        skipped_checks += 1

    self_check_status = _self_check_status(
        errors=errors,
        deterministic_archive_status=deterministic_archive_status,
        deterministic_zip_status=deterministic_zip_status,
        include_ml_readiness=include_ml_readiness,
        dataset_path=dataset_path,
        ml_workflow_status=ml_workflow_status,
    )

    report_path = root_output / "workflow_self_check.md"
    json_path = root_output / "workflow_self_check.json"
    files_created.extend(str(path) for path in (report_path, json_path))

    result = EngineeringWorkflowSelfCheckResult(
        status=self_check_status,
        self_check_status=self_check_status,
        output_dir=str(root_output),
        checked_commands=tuple(checked_commands),
        passed_checks=passed_checks,
        failed_checks=failed_checks,
        skipped_checks=skipped_checks,
        deterministic_workflow_status=deterministic_workflow_status,
        deterministic_archive_status=deterministic_archive_status,
        deterministic_zip_status=deterministic_zip_status,
        ml_workflow_status=ml_workflow_status,
        ml_ready_for_research=ml_ready_for_research,
        ml_ready_for_engineering_review=ml_ready_for_engineering_review,
        ml_ready_for_project_use=ml_ready_for_project_use,
        files_created=tuple(dict.fromkeys(files_created)),
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(dict.fromkeys(errors)),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
    )

    report_path.write_text(render_self_check_markdown(result), encoding="utf-8")
    json_path.write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if cleanup:
        _cleanup_workflow_outputs(root_output)

    return result


def render_self_check_markdown(result: EngineeringWorkflowSelfCheckResult) -> str:
    """Render the self-check summary as Markdown."""
    lines = [
        "# Engineering Workflow Self-Check",
        "",
        SELF_CHECK_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "",
        "## Checked Commands",
        "",
        *_bullet_lines(result.checked_commands),
        "",
        "## Deterministic Workflow Result",
        "",
        f"- self_check_status: `{result.self_check_status}`",
        f"- deterministic_workflow_status: `{result.deterministic_workflow_status}`",
        f"- deterministic_archive_status: `{result.deterministic_archive_status}`",
        f"- deterministic_zip_status: `{result.deterministic_zip_status}`",
        "",
        "## Optional ML Readiness Result",
        "",
        f"- ml_workflow_status: `{result.ml_workflow_status}`",
        f"- ml_ready_for_research: `{result.ml_ready_for_research}`",
        f"- ml_ready_for_engineering_review: `{result.ml_ready_for_engineering_review}`",
        f"- ml_ready_for_project_use: `{result.ml_ready_for_project_use}`",
        "",
        "## Check Counts",
        "",
        f"- passed_checks: `{result.passed_checks}`",
        f"- failed_checks: `{result.failed_checks}`",
        f"- skipped_checks: `{result.skipped_checks}`",
        "",
        "## Files Created",
        "",
        *_bullet_lines(result.files_created),
        "",
        "## Warnings",
        "",
        *_bullet_lines(result.warnings),
        "",
        "## Errors",
        "",
        *_bullet_lines(result.errors),
        "",
        "## Limitations",
        "",
        "- Self-check verifies that the workflow technically runs.",
        "- Self-check does not certify the design.",
        "- Material verification remains a separate engineer gate.",
        "- External validation remains a separate engineer gate.",
        "- ML readiness is optional and advisory-only.",
        "- `ml_ready_for_project_use` must remain false.",
    ]
    return "\n".join(lines) + "\n"


def _check_expected_deterministic_files(output_dir: Path) -> tuple[int, int, tuple[str, ...]]:
    expected_paths = (
        output_dir / "deterministic_report" / "report.md",
        output_dir / "deterministic_report" / "report.json",
        output_dir / "deterministic_report" / "report.html",
        output_dir / "deterministic_report" / "manifest.json",
        output_dir / "deterministic_report" / "README_REVIEW.md",
        output_dir / "deterministic_report.zip",
        output_dir / "workflow_summary.json",
        output_dir / "workflow_summary.md",
        output_dir / "README_WORKFLOW.md",
    )
    missing = tuple(str(path) for path in expected_paths if not path.exists())
    return len(expected_paths) - len(missing), len(missing), missing


def _self_check_status(
    *,
    errors: list[str],
    deterministic_archive_status: str,
    deterministic_zip_status: str,
    include_ml_readiness: bool,
    dataset_path: Path | None,
    ml_workflow_status: str | None,
) -> str:
    if errors or deterministic_archive_status == "fail" or deterministic_zip_status == "fail":
        return "fail"
    if include_ml_readiness and dataset_path is None:
        return "review_required"
    if include_ml_readiness and ml_workflow_status in {"fail", "review_required", "not_run"}:
        return "review_required"
    return "pass"


def _cleanup_workflow_outputs(output_dir: Path) -> None:
    for name in ("deterministic_workflow", "ml_workflow"):
        path = output_dir / name
        if path.exists():
            shutil.rmtree(path)


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]
