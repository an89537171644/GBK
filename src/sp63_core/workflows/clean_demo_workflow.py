"""Clean deterministic demo workflow wrapper."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from sp63_core.workflows.engineering_workflow import (
    EngineeringWorkflowResult,
    run_engineering_workflow,
)

CLEAN_DEMO_INPUT = Path("docs/reports/examples/clean_demo/rectangular_clean_demo_input.json")
CLEAN_DEMO_WARNING = (
    "clean demo workflow is a deterministic smoke example only. It does not "
    "certify designs, approve project use, or make ML project-ready."
)


@dataclass(frozen=True)
class CleanDemoWorkflowResult:
    """Clean deterministic demo workflow result."""

    status: str
    demo_status: str
    input_json_path: str
    output_dir: str
    workflow_status: str
    preflight_status: str | None
    deterministic_report_status: str
    archive_validation_status: str
    zip_status: str
    index_status: str | None
    index_path: str | None
    files_created: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def run_clean_demo_workflow(*, output_dir: Path) -> CleanDemoWorkflowResult:
    """Run the clean deterministic demo workflow."""
    workflow = run_engineering_workflow(
        input_json_path=CLEAN_DEMO_INPUT,
        output_dir=Path(output_dir),
        include_ml_readiness=False,
        create_zip=True,
        with_index=True,
        with_preflight=True,
    )
    status = _clean_demo_status(workflow)
    result = CleanDemoWorkflowResult(
        status=status,
        demo_status=status,
        input_json_path=str(CLEAN_DEMO_INPUT),
        output_dir=workflow.output_dir,
        workflow_status=workflow.workflow_status,
        preflight_status=workflow.preflight_status,
        deterministic_report_status=workflow.deterministic_report_status,
        archive_validation_status=workflow.archive_validation_status,
        zip_status=workflow.zip_status,
        index_status=workflow.index_status,
        index_path=workflow.index_path,
        files_created=workflow.files_created,
        warnings=tuple(dict.fromkeys((CLEAN_DEMO_WARNING, *workflow.warnings))),
        errors=workflow.errors,
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    _write_clean_demo_summary(result)
    return result


def _clean_demo_status(workflow: EngineeringWorkflowResult) -> str:
    if workflow.errors:
        return "fail"
    required_pass_statuses = (
        workflow.preflight_status,
        workflow.deterministic_report_status,
        workflow.archive_validation_status,
        workflow.zip_status,
        workflow.index_status,
    )
    if all(status == "pass" for status in required_pass_statuses):
        return "pass"
    return "review_required"


def _write_clean_demo_summary(result: CleanDemoWorkflowResult) -> None:
    output_dir = Path(result.output_dir)
    json_path = output_dir / "clean_demo_workflow.json"
    markdown_path = output_dir / "clean_demo_workflow.md"
    json_path.write_text(
        json.dumps(
            {"report_type": "clean_demo_workflow", **asdict(result)},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    markdown_path.write_text(_render_clean_demo_markdown(result), encoding="utf-8")


def _render_clean_demo_markdown(result: CleanDemoWorkflowResult) -> str:
    lines = [
        "# Clean Deterministic Demo Workflow",
        "",
        CLEAN_DEMO_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Summary",
        "",
        f"- demo_status: `{result.demo_status}`",
        f"- workflow_status: `{result.workflow_status}`",
        f"- preflight_status: `{result.preflight_status}`",
        f"- deterministic_report_status: `{result.deterministic_report_status}`",
        f"- archive_validation_status: `{result.archive_validation_status}`",
        f"- zip_status: `{result.zip_status}`",
        f"- index_status: `{result.index_status}`",
        f"- index_path: `{result.index_path}`",
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


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]
