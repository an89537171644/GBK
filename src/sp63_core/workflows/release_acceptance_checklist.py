"""Machine-readable v0.9 release acceptance checklist."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RELEASE_ACCEPTANCE_WARNING = (
    "Release acceptance checklist is review evidence only. Manual signoff gates "
    "remain open and project use is not approved."
)

CHECKLIST_ITEMS: tuple[dict[str, Any], ...] = (
    {
        "item_id": "validate_golden",
        "title": "validate --golden passes",
        "required_for_v09": True,
        "required_for_v10": True,
        "current_status": "pass",
        "manual_signoff_required": False,
        "evidence_command": "python -m sp63_core validate --golden",
        "evidence_doc": "docs/validation_report.md",
    },
    {
        "item_id": "manual_cases",
        "title": "manual verification cases pass",
        "required_for_v09": True,
        "required_for_v10": True,
        "current_status": "pass",
        "manual_signoff_required": False,
        "evidence_command": "python -m sp63_core manual-cases --json",
        "evidence_doc": "docs/validation/manual_sp63_cases.md",
    },
    {
        "item_id": "external_validation_sample",
        "title": "external validation sample passes",
        "required_for_v09": True,
        "required_for_v10": True,
        "current_status": "pass",
        "manual_signoff_required": False,
        "evidence_command": "python -m sp63_core external-validation --sample --json",
        "evidence_doc": "docs/validation/external_validation_workflow.md",
    },
    {
        "item_id": "materials_engineer_review",
        "title": "material catalog reviewed by engineer",
        "required_for_v09": True,
        "required_for_v10": True,
        "current_status": "review_required",
        "manual_signoff_required": True,
        "evidence_command": "python -m sp63_core materials-audit --json",
        "evidence_doc": "docs/materials_audit.md",
    },
    {
        "item_id": "protected_files_guard",
        "title": "protected files guard passes",
        "required_for_v09": True,
        "required_for_v10": True,
        "current_status": "pass",
        "manual_signoff_required": False,
        "evidence_command": "python -m sp63_core protected-files-check --json",
        "evidence_doc": "docs/engineering_audit.md",
    },
    {
        "item_id": "docs_audit",
        "title": "documentation audit passes",
        "required_for_v09": True,
        "required_for_v10": True,
        "current_status": "pass",
        "manual_signoff_required": False,
        "evidence_command": "python -m sp63_core docs-audit --json",
        "evidence_doc": "docs/engineering_audit.md",
    },
    {
        "item_id": "clean_demo",
        "title": "clean demo workflow passes",
        "required_for_v09": True,
        "required_for_v10": True,
        "current_status": "pass",
        "manual_signoff_required": False,
        "evidence_command": (
            "python -m sp63_core clean-demo-verify --run "
            "--output-dir reports/clean_demo_verify --json"
        ),
        "evidence_doc": "docs/clean_demo_verification.md",
    },
    {
        "item_id": "release_bundle",
        "title": "release bundle generated",
        "required_for_v09": True,
        "required_for_v10": True,
        "current_status": "pass",
        "manual_signoff_required": False,
        "evidence_command": (
            "python -m sp63_core release-bundle --output-dir reports/release_bundle "
            "--version 0.9.0-rc1 --json"
        ),
        "evidence_doc": "docs/release_bundle.md",
    },
    {
        "item_id": "user_manual",
        "title": "user manual exists",
        "required_for_v09": True,
        "required_for_v10": True,
        "current_status": "pass",
        "manual_signoff_required": False,
        "evidence_command": "python -m sp63_core user-manual-index --json",
        "evidence_doc": "docs/user_manual/quickstart.md",
    },
    {
        "item_id": "known_limitations_reviewed",
        "title": "known limitations reviewed",
        "required_for_v09": True,
        "required_for_v10": True,
        "current_status": "review_required",
        "manual_signoff_required": True,
        "evidence_command": "",
        "evidence_doc": "docs/known_limitations_v0_9.md",
    },
    {
        "item_id": "ml_ready_false",
        "title": "ml_ready_for_project_use remains false",
        "required_for_v09": True,
        "required_for_v10": True,
        "current_status": "pass",
        "manual_signoff_required": False,
        "evidence_command": "python -m sp63_core ml-proposal-verify --json",
        "evidence_doc": "docs/engineering_audit.md",
    },
    {
        "item_id": "engineer_signed_review",
        "title": "engineer signed review",
        "required_for_v09": True,
        "required_for_v10": True,
        "current_status": "review_required",
        "manual_signoff_required": True,
        "evidence_command": "",
        "evidence_doc": "docs/user_manual/acceptance_checklist.md",
    },
)


@dataclass(frozen=True)
class ReleaseAcceptanceChecklistResult:
    """Release acceptance checklist result."""

    status: str
    checklist_status: str
    output_dir: str
    items: tuple[dict[str, Any], ...]
    item_count: int
    machine_pass_count: int
    manual_signoff_required_count: int
    review_required_count: int
    failed_count: int
    generated_files: tuple[str, ...]
    summary_json_path: str
    summary_markdown_path: str
    readme_path: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False
    project_use_allowed: bool = False


def build_release_acceptance_checklist(*, output_dir: Path) -> ReleaseAcceptanceChecklistResult:
    """Build v0.9 release acceptance checklist artifacts."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    items = CHECKLIST_ITEMS
    failed_count = sum(1 for item in items if item["current_status"] == "fail")
    review_required_count = sum(1 for item in items if item["current_status"] == "review_required")
    manual_count = sum(1 for item in items if item["manual_signoff_required"])
    machine_pass_count = sum(
        1
        for item in items
        if item["current_status"] == "pass" and not item["manual_signoff_required"]
    )
    status = "fail" if failed_count else "review_required" if review_required_count else "pass"

    json_path = output_path / "release_acceptance_checklist.json"
    markdown_path = output_path / "release_acceptance_checklist.md"
    readme_path = output_path / "README_RELEASE_ACCEPTANCE.md"
    result = ReleaseAcceptanceChecklistResult(
        status=status,
        checklist_status=status,
        output_dir=str(output_path),
        items=items,
        item_count=len(items),
        machine_pass_count=machine_pass_count,
        manual_signoff_required_count=manual_count,
        review_required_count=review_required_count,
        failed_count=failed_count,
        generated_files=(str(json_path), str(markdown_path), str(readme_path)),
        summary_json_path=str(json_path),
        summary_markdown_path=str(markdown_path),
        readme_path=str(readme_path),
        warnings=(RELEASE_ACCEPTANCE_WARNING,),
        errors=tuple(
            f"acceptance item failed: {item['item_id']}"
            for item in items
            if item["current_status"] == "fail"
        ),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
        project_use_allowed=False,
    )
    json_path.write_text(
        json.dumps({"report_type": "release_acceptance_checklist", **result.__dict__}, indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(render_release_acceptance_checklist_markdown(result), encoding="utf-8")
    readme_path.write_text(_render_readme(result), encoding="utf-8")
    return result


def render_release_acceptance_checklist_markdown(
    result: ReleaseAcceptanceChecklistResult,
) -> str:
    """Render release acceptance checklist as Markdown."""
    lines = [
        "# Release Acceptance Checklist",
        "",
        RELEASE_ACCEPTANCE_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "project_use_allowed = false",
        "",
        "## Summary",
        "",
        f"- checklist_status: `{result.checklist_status}`",
        f"- item_count: `{result.item_count}`",
        f"- machine_pass_count: `{result.machine_pass_count}`",
        f"- manual_signoff_required_count: `{result.manual_signoff_required_count}`",
        f"- review_required_count: `{result.review_required_count}`",
        f"- failed_count: `{result.failed_count}`",
        "",
        "## Items",
        "",
        "| item_id | current_status | manual_signoff_required | evidence_command |",
        "|---|---|---:|---|",
    ]
    for item in result.items:
        lines.append(
            "| {item_id} | `{current_status}` | `{manual_signoff_required}` | "
            "`{evidence_command}` |".format(**item)
        )
    return "\n".join(lines) + "\n"


def _render_readme(result: ReleaseAcceptanceChecklistResult) -> str:
    return "\n".join(
        [
            "# README Release Acceptance",
            "",
            RELEASE_ACCEPTANCE_WARNING,
            "",
            f"checklist_status: `{result.checklist_status}`",
            "project_use_allowed: `false`",
            "ml_ready_for_project_use: `false`",
            "",
            "Manual signoff rows must be reviewed by an engineer.",
        ]
    ) + "\n"
