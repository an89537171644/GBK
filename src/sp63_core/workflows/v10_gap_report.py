"""v1.0 gap and risk report for post-v0.9 planning."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

V10_GAP_WARNING = (
    "v1.0 gap report is planning evidence only. It does not certify designs, "
    "approve project use, or make ML project-ready."
)

BLOCKERS: tuple[dict[str, Any], ...] = (
    {
        "area": "material verification",
        "status": "open",
        "description": "complete engineer-approved material catalog verification",
    },
    {
        "area": "external validation",
        "status": "open",
        "description": "complete real manual/Excel/SCAD/LIRA validation evidence",
    },
    {
        "area": "GUI/launcher",
        "status": "open",
        "description": "finish safe static launcher/viewer workflow without hiding warnings",
    },
    {
        "area": "packaging/installer",
        "status": "open",
        "description": "define reproducible installer or portable distribution process",
    },
    {
        "area": "ML production",
        "status": "open",
        "description": "keep ML advisory-only until external validation and governance mature",
    },
    {
        "area": "documentation",
        "status": "open",
        "description": "complete user-facing v1.0 review and limitations documentation",
    },
)

RISKS: tuple[dict[str, str], ...] = (
    {
        "risk": "material catalog values may remain draft",
        "mitigation": "require engineer verification CSV before project use",
    },
    {
        "risk": "synthetic validation may be mistaken for external validation",
        "mitigation": "keep external validation gate explicit and separate",
    },
    {
        "risk": "ML surrogate may be mistaken for a design checker",
        "mitigation": "keep deterministic verification mandatory and ML advisory-only",
    },
    {
        "risk": "portable package may be mistaken for certification",
        "mitigation": "show review-only warnings in package docs and manifests",
    },
)

RECOMMENDATIONS: tuple[str, ...] = (
    "complete real external validation before any v1.0 project-use claim",
    "complete engineer material verification before final material catalog approval",
    "keep static reports and deterministic statuses visually primary in any launcher",
    "keep ml_ready_for_project_use false until a separate engineering governance gate",
    "do not publish release artifacts as certification evidence",
)


@dataclass(frozen=True)
class V10GapReportResult:
    """v1.0 gap and risk report result."""

    status: str
    report_status: str
    output_dir: str
    ready_for_v09_internal_review: bool
    ready_for_v10: bool
    remaining_steps_estimate: int
    blockers: tuple[dict[str, Any], ...]
    risks: tuple[dict[str, str], ...]
    recommendations: tuple[str, ...]
    generated_files: tuple[str, ...]
    summary_json_path: str
    summary_markdown_path: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_v10_gap_report(*, output_dir: Path) -> V10GapReportResult:
    """Build the v1.0 gap and risk report."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / "v10_gap_report.json"
    markdown_path = output_path / "v10_gap_report.md"
    result = V10GapReportResult(
        status="review_required",
        report_status="review_required",
        output_dir=str(output_path),
        ready_for_v09_internal_review=True,
        ready_for_v10=False,
        remaining_steps_estimate=len(BLOCKERS),
        blockers=BLOCKERS,
        risks=RISKS,
        recommendations=RECOMMENDATIONS,
        generated_files=(str(json_path), str(markdown_path)),
        summary_json_path=str(json_path),
        summary_markdown_path=str(markdown_path),
        warnings=(V10_GAP_WARNING,),
        errors=(),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    json_path.write_text(
        json.dumps({"report_type": "v10_gap_report", **result.__dict__}, indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(render_v10_gap_report_markdown(result), encoding="utf-8")
    return result


def render_v10_gap_report_markdown(result: V10GapReportResult) -> str:
    """Render v1.0 gap report as Markdown."""
    lines = [
        "# v1.0 Gap And Risk Report",
        "",
        V10_GAP_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Summary",
        "",
        f"- ready_for_v09_internal_review: `{result.ready_for_v09_internal_review}`",
        f"- ready_for_v10: `{result.ready_for_v10}`",
        f"- remaining_steps_estimate: `{result.remaining_steps_estimate}`",
        "",
        "## Blockers",
        "",
        "| area | status | description |",
        "|---|---|---|",
    ]
    for blocker in result.blockers:
        lines.append(
            "| {area} | `{status}` | {description} |".format(
                area=blocker["area"],
                status=blocker["status"],
                description=blocker["description"],
            )
        )
    lines.extend(
        [
            "",
            "## Risks",
            "",
            "| risk | mitigation |",
            "|---|---|",
        ]
    )
    for risk in result.risks:
        lines.append(f"| {risk['risk']} | {risk['mitigation']} |")
    lines.extend(["", "## Recommendations", "", *_bullet_lines(result.recommendations)])
    return "\n".join(lines) + "\n"


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]
