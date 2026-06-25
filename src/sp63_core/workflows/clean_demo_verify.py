"""Verification for clean demo generated artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.workflows.clean_demo_workflow import run_clean_demo_workflow

CLEAN_DEMO_VERIFY_WARNING = (
    "Clean demo verification checks generated review artifacts only. It does not "
    "certify designs, approve project use, or make ML project-ready."
)

EXPECTED_CLEAN_DEMO_ARTIFACTS: tuple[str, ...] = (
    "input_preflight_report.json",
    "input_preflight_report.md",
    "deterministic_report/report.md",
    "deterministic_report/report.json",
    "deterministic_report/report.html",
    "deterministic_report/manifest.json",
    "deterministic_report/README_REVIEW.md",
    "deterministic_report.zip",
    "workflow_summary.json",
    "workflow_summary.md",
    "README_WORKFLOW.md",
    "index.html",
)


@dataclass(frozen=True)
class CleanDemoVerificationResult:
    """Clean demo generated artifact verification result."""

    status: str
    verification_status: str
    workflow_dir: str
    checked_artifacts: tuple[str, ...]
    missing_artifacts: tuple[str, ...]
    ml_ready_true_files: tuple[str, ...]
    warning_artifacts_present: bool
    generated_files: tuple[str, ...]
    summary_json_path: str
    summary_markdown_path: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def verify_clean_demo_artifacts(
    *,
    workflow_dir: Path,
) -> CleanDemoVerificationResult:
    """Verify an existing clean demo workflow directory."""
    workflow_path = Path(workflow_dir)
    warnings = [CLEAN_DEMO_VERIFY_WARNING]
    errors: list[str] = []

    missing = tuple(
        relative_path
        for relative_path in EXPECTED_CLEAN_DEMO_ARTIFACTS
        if not (workflow_path / relative_path).exists()
    )
    errors.extend(f"clean demo artifact missing: {path}" for path in missing)

    ml_ready_true_files = tuple(
        str(path.relative_to(workflow_path))
        for path in workflow_path.rglob("*.json")
        if _json_has_ml_ready_true(path)
    )
    errors.extend(f"ml_ready_for_project_use true in {path}" for path in ml_ready_true_files)

    warning_artifacts_present = _warning_artifacts_present(workflow_path)
    if not warning_artifacts_present:
        errors.append("clean demo warning artifacts are missing")

    status = "fail" if errors else "pass"
    summary_json_path = workflow_path / "clean_demo_verification.json"
    summary_markdown_path = workflow_path / "clean_demo_verification.md"
    result = CleanDemoVerificationResult(
        status=status,
        verification_status=status,
        workflow_dir=str(workflow_path),
        checked_artifacts=EXPECTED_CLEAN_DEMO_ARTIFACTS,
        missing_artifacts=missing,
        ml_ready_true_files=ml_ready_true_files,
        warning_artifacts_present=warning_artifacts_present,
        generated_files=(str(summary_json_path), str(summary_markdown_path)),
        summary_json_path=str(summary_json_path),
        summary_markdown_path=str(summary_markdown_path),
        warnings=tuple(warnings),
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    workflow_path.mkdir(parents=True, exist_ok=True)
    summary_json_path.write_text(
        json.dumps({"report_type": "clean_demo_verification", **result.__dict__}, indent=2),
        encoding="utf-8",
    )
    summary_markdown_path.write_text(
        render_clean_demo_verification_markdown(result),
        encoding="utf-8",
    )
    return result


def run_clean_demo_and_verify(*, output_dir: Path) -> CleanDemoVerificationResult:
    """Run the clean demo workflow, then verify generated artifacts."""
    run_clean_demo_workflow(output_dir=Path(output_dir))
    return verify_clean_demo_artifacts(workflow_dir=Path(output_dir))


def render_clean_demo_verification_markdown(result: CleanDemoVerificationResult) -> str:
    """Render clean demo verification as Markdown."""
    lines = [
        "# Clean Demo Verification",
        "",
        CLEAN_DEMO_VERIFY_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Summary",
        "",
        f"- verification_status: `{result.verification_status}`",
        f"- workflow_dir: `{result.workflow_dir}`",
        f"- missing_artifacts: `{len(result.missing_artifacts)}`",
        f"- ml_ready_true_files: `{len(result.ml_ready_true_files)}`",
        f"- warning_artifacts_present: `{result.warning_artifacts_present}`",
        "",
        "## Missing Artifacts",
        "",
        *_bullet_lines(result.missing_artifacts),
        "",
        "## Errors",
        "",
        *_bullet_lines(result.errors),
    ]
    return "\n".join(lines) + "\n"


def _json_has_ml_ready_true(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return _contains_ml_ready_true(payload)


def _contains_ml_ready_true(value: Any) -> bool:
    if isinstance(value, dict):
        if value.get("ml_ready_for_project_use") is True:
            return True
        return any(_contains_ml_ready_true(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_ml_ready_true(item) for item in value)
    return False


def _warning_artifacts_present(workflow_path: Path) -> bool:
    workflow_readme = workflow_path / "README_WORKFLOW.md"
    review_readme = workflow_path / "deterministic_report" / "README_REVIEW.md"
    if not workflow_readme.exists() or not review_readme.exists():
        return False
    combined = (
        workflow_readme.read_text(encoding="utf-8")
        + "\n"
        + review_readme.read_text(encoding="utf-8")
    )
    required_phrases = (
        "Engineer review is mandatory",
        "Deterministic SP63 checks are mandatory",
        "ML is advisory-only",
    )
    return all(phrase in combined for phrase in required_phrases)


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]
