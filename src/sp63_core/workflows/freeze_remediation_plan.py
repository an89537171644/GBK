"""Remediation plan for v0.9 freeze and v1.0 gap review gates."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.workflows.v09_freeze_report import build_v09_freeze_report
from sp63_core.workflows.v10_gap_report import build_v10_gap_report

FREEZE_REMEDIATION_WARNING = (
    "Freeze remediation plan is review planning evidence only. It does not "
    "certify designs, approve project use, or close engineer review gates."
)


@dataclass(frozen=True)
class FreezeRemediationPlanResult:
    """Freeze remediation plan result."""

    status: str
    plan_status: str
    output_dir: str
    version: str
    remediation_items: tuple[dict[str, Any], ...]
    blocker_count: int
    acceptable_review_gate_count: int
    required_before_v09_count: int
    required_before_v10_count: int
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


def build_freeze_remediation_plan(
    *,
    output_dir: Path,
    version: str = "0.9.0-rc1",
) -> FreezeRemediationPlanResult:
    """Build a remediation plan for expected v0.9/v1.0 review gates."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    try:
        freeze = build_v09_freeze_report(
            output_dir=output_path / "source_v09_freeze_report",
            version=version,
        )
        v10_gap = build_v10_gap_report(output_dir=output_path / "source_v10_gap_report")
    except OSError as exc:
        freeze = None
        v10_gap = None
        errors.append(f"unable to build current readiness reports: {exc}")

    remediation_items = _build_remediation_items(
        freeze_status=freeze.status if freeze is not None else "unavailable",
        v10_status=v10_gap.status if v10_gap is not None else "unavailable",
    )
    blocker_count = sum(1 for item in remediation_items if item["classification"] == "blocker")
    acceptable_count = sum(
        1 for item in remediation_items if item["classification"] == "acceptable_review_gate"
    )
    before_v09_count = sum(1 for item in remediation_items if item["required_before"] == "v0.9")
    before_v10_count = sum(1 for item in remediation_items if item["required_before"] == "v1.0")
    status = "fail" if errors else "review_required" if remediation_items else "pass"

    json_path = output_path / "freeze_remediation_plan.json"
    markdown_path = output_path / "freeze_remediation_plan.md"
    readme_path = output_path / "README_FREEZE_REMEDIATION.md"
    result = FreezeRemediationPlanResult(
        status=status,
        plan_status=status,
        output_dir=str(output_path),
        version=version,
        remediation_items=remediation_items,
        blocker_count=blocker_count,
        acceptable_review_gate_count=acceptable_count,
        required_before_v09_count=before_v09_count,
        required_before_v10_count=before_v10_count,
        generated_files=(str(json_path), str(markdown_path), str(readme_path)),
        summary_json_path=str(json_path),
        summary_markdown_path=str(markdown_path),
        readme_path=str(readme_path),
        warnings=(FREEZE_REMEDIATION_WARNING,),
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
        project_use_allowed=False,
    )
    json_path.write_text(
        json.dumps({"report_type": "freeze_remediation_plan", **result.__dict__}, indent=2),
        encoding="utf-8",
    )
    markdown = render_freeze_remediation_plan_markdown(result)
    markdown_path.write_text(markdown, encoding="utf-8")
    readme_path.write_text(_render_readme(result), encoding="utf-8")
    return result


def render_freeze_remediation_plan_markdown(result: FreezeRemediationPlanResult) -> str:
    """Render freeze remediation plan as Markdown."""
    lines = [
        "# Freeze Remediation Plan",
        "",
        FREEZE_REMEDIATION_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "project_use_allowed = false",
        "",
        "## Summary",
        "",
        f"- version: `{result.version}`",
        f"- plan_status: `{result.plan_status}`",
        f"- blocker_count: `{result.blocker_count}`",
        f"- acceptable_review_gate_count: `{result.acceptable_review_gate_count}`",
        f"- required_before_v09_count: `{result.required_before_v09_count}`",
        f"- required_before_v10_count: `{result.required_before_v10_count}`",
        "",
        "## Remediation Items",
        "",
        "| item | classification | required_before | cannot_auto_close | action |",
        "|---|---|---|---:|---|",
    ]
    for item in result.remediation_items:
        lines.append(
            "| {item_id} | `{classification}` | `{required_before}` | "
            "`{cannot_auto_close}` | {action} |".format(**item)
        )
    lines.extend(["", "## Errors", "", *_bullet_lines(result.errors)])
    return "\n".join(lines) + "\n"


def _build_remediation_items(*, freeze_status: str, v10_status: str) -> tuple[dict[str, Any], ...]:
    return (
        _item(
            "material_audit_review_required",
            "acceptable_review_gate",
            "v0.9",
            "Material catalog values must be reviewed by an engineer; catalog values "
            "are not auto-updated.",
        ),
        _item(
            "external_validation_sample_only",
            "acceptable_review_gate",
            "v0.9",
            "Synthetic/sample validation is evidence plumbing only; real "
            "manual/Excel/SCAD/LIRA data remains separate.",
        ),
        _item(
            "ml_advisory_only",
            "acceptable_review_gate",
            "v0.9",
            "ML remains advisory-only and cannot approve designs.",
        ),
        _item(
            "project_use_false",
            "blocker",
            "v1.0",
            "Project use remains disallowed until external validation and engineer "
            "signoff are complete.",
        ),
        _item(
            "gui_installer_gap",
            "blocker",
            "v1.0",
            "Future GUI/launcher and installer workflows need separate review without "
            "hiding warnings.",
        ),
        _item(
            "windows_clean_machine_validation_gap",
            "blocker",
            "v1.0",
            "Clean Windows machine workflow must be run by a reviewer before broader distribution.",
        ),
        _item(
            "engineer_review_required",
            "acceptable_review_gate",
            "v0.9",
            "Engineer review remains mandatory for all review/freeze artifacts.",
        ),
        _item(
            "current_v09_freeze_status",
            "acceptable_review_gate" if freeze_status == "review_required" else "blocker",
            "v0.9",
            f"Current v09-freeze-report status is {freeze_status}. Do not force it "
            "to pass automatically.",
        ),
        _item(
            "current_v10_gap_status",
            "acceptable_review_gate" if v10_status == "review_required" else "blocker",
            "v1.0",
            f"Current v10-gap-report status is {v10_status}. Gaps require explicit future work.",
        ),
    )


def _item(
    item_id: str,
    classification: str,
    required_before: str,
    action: str,
) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "classification": classification,
        "required_before": required_before,
        "action": action,
        "cannot_auto_close": True,
    }


def _render_readme(result: FreezeRemediationPlanResult) -> str:
    return "\n".join(
        [
            "# README Freeze Remediation",
            "",
            FREEZE_REMEDIATION_WARNING,
            "",
            f"plan_status: `{result.plan_status}`",
            "project_use_allowed: `false`",
            "ml_ready_for_project_use: `false`",
            "",
            "Review `freeze_remediation_plan.json` and `freeze_remediation_plan.md`.",
            "Open review gates must be closed by engineering evidence, not by "
            "changing statuses automatically.",
        ]
    ) + "\n"


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]
