"""Index and completeness check for user manual documentation package."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

USER_MANUAL_WARNING = (
    "User manual is guidance only. It does not certify designs or approve "
    "project use."
)

REQUIRED_USER_MANUAL_FILES: tuple[str, ...] = (
    "README.md",
    "quickstart.md",
    "input_data.md",
    "preflight_validation.md",
    "workflow_run.md",
    "report_index.md",
    "batch_workflow.md",
    "ml_advisory_limits.md",
    "evidence_templates.md",
    "troubleshooting.md",
    "acceptance_checklist.md",
)


@dataclass(frozen=True)
class UserManualIndexResult:
    """User manual package index result."""

    status: str
    manual_status: str
    manual_dir: str
    required_files: tuple[str, ...]
    existing_files: tuple[str, ...]
    missing_files: tuple[str, ...]
    output_dir: str | None
    json_data: dict[str, Any]
    markdown: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_user_manual_index(
    *,
    manual_dir: Path = Path("docs/user_manual"),
    output_dir: Path | None = None,
) -> UserManualIndexResult:
    """Build an index for the user manual package."""
    manual_path = Path(manual_dir)
    existing_files = tuple(
        file_name for file_name in REQUIRED_USER_MANUAL_FILES if (manual_path / file_name).exists()
    )
    missing_files = tuple(
        file_name
        for file_name in REQUIRED_USER_MANUAL_FILES
        if not (manual_path / file_name).exists()
    )
    errors = tuple(f"user manual file missing: {file_name}" for file_name in missing_files)
    status = "fail" if missing_files else "pass"
    json_data = {
        "report_type": "user_manual_index",
        "status": status,
        "manual_status": status,
        "manual_dir": str(manual_path),
        "required_files": list(REQUIRED_USER_MANUAL_FILES),
        "existing_files": list(existing_files),
        "missing_files": list(missing_files),
        "warnings": [USER_MANUAL_WARNING],
        "errors": list(errors),
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "ml_ready_for_project_use": False,
    }
    markdown = _render_user_manual_index_markdown(json_data)
    result = UserManualIndexResult(
        status=status,
        manual_status=status,
        manual_dir=str(manual_path),
        required_files=REQUIRED_USER_MANUAL_FILES,
        existing_files=existing_files,
        missing_files=missing_files,
        output_dir=str(output_dir) if output_dir is not None else None,
        json_data=json_data,
        markdown=markdown,
        warnings=(USER_MANUAL_WARNING,),
        errors=errors,
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    if output_dir is not None:
        _write_user_manual_index(Path(output_dir), result)
    return result


def _render_user_manual_index_markdown(json_data: dict[str, Any]) -> str:
    lines = [
        "# User Manual Index",
        "",
        USER_MANUAL_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Summary",
        "",
        f"- manual_status: `{json_data['manual_status']}`",
        f"- manual_dir: `{json_data['manual_dir']}`",
        f"- required_files: `{len(json_data['required_files'])}`",
        f"- existing_files: `{len(json_data['existing_files'])}`",
        f"- missing_files: `{len(json_data['missing_files'])}`",
        "",
        "## Files",
        "",
    ]
    for file_name in json_data["required_files"]:
        marker = "present" if file_name in json_data["existing_files"] else "missing"
        lines.append(f"- `{file_name}`: {marker}")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- The manual is documentation only.",
            "- Deterministic SP63 checks remain mandatory.",
            "- Engineer review remains mandatory.",
            "- ML remains advisory-only.",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_user_manual_index(output_dir: Path, result: UserManualIndexResult) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "user_manual_index.json").write_text(
        json.dumps(result.json_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "user_manual_index.md").write_text(result.markdown, encoding="utf-8")
