"""Next release roadmap after v0.9 review build."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

NEXT_RELEASE_ROADMAP_WARNING = (
    "Next release roadmap is planning evidence only. It does not certify "
    "designs, approve project use, or make ML project-ready."
)

ROADMAP_SECTIONS: tuple[dict[str, Any], ...] = (
    {
        "section_id": "v09_internal_review",
        "title": "v0.9 internal review",
        "target_release": "v0.9",
        "status": "review_required",
        "milestones": (
            "review v09-review-build output",
            "review known limitations",
            "confirm no generated artifacts are committed",
        ),
    },
    {
        "section_id": "v09_user_trial",
        "title": "v0.9 user trial",
        "target_release": "v0.9",
        "status": "planned",
        "milestones": (
            "run clean-machine Windows smoke workflow",
            "collect engineer feedback on static launcher dashboard",
        ),
    },
    {
        "section_id": "v10_engineering_release",
        "title": "v1.0 engineering release",
        "target_release": "v1.0",
        "status": "blocked_by_review_gates",
        "milestones": (
            "complete material verification",
            "complete real external validation",
            "complete release acceptance signoff",
        ),
    },
    {
        "section_id": "gui_launcher",
        "title": "GUI/launcher milestone",
        "target_release": "future",
        "status": "planned",
        "milestones": (
            "keep static reports primary",
            "avoid web servers and JavaScript calculations until separately approved",
        ),
    },
    {
        "section_id": "material_verification",
        "title": "material verification milestone",
        "target_release": "v1.0",
        "status": "review_required",
        "milestones": (
            "complete engineer-filled material CSV",
            "keep catalog updates manual and separately reviewed",
        ),
    },
    {
        "section_id": "external_validation",
        "title": "external validation milestone",
        "target_release": "v1.0",
        "status": "review_required",
        "milestones": (
            "collect manual/Excel/SCAD/LIRA evidence",
            "run strict external validation gate",
        ),
    },
    {
        "section_id": "ml_advisory_maturity",
        "title": "ML advisory maturity milestone",
        "target_release": "future",
        "status": "advisory_only",
        "milestones": (
            "keep deterministic verification mandatory",
            "keep ml_ready_for_project_use false",
        ),
    },
    {
        "section_id": "installer_packaging",
        "title": "installer/packaging milestone",
        "target_release": "future",
        "status": "planned",
        "milestones": (
            "validate portable workflow first",
            "define installer only in a separate approved step",
        ),
    },
)


@dataclass(frozen=True)
class NextReleaseRoadmapResult:
    """Next release roadmap result."""

    status: str
    roadmap_status: str
    output_dir: str
    sections: tuple[dict[str, Any], ...]
    section_count: int
    review_required_count: int
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


def build_next_release_roadmap(*, output_dir: Path) -> NextReleaseRoadmapResult:
    """Build the next release roadmap artifacts."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    review_count = sum(
        1 for section in ROADMAP_SECTIONS if section["status"] == "review_required"
    )
    json_path = output_path / "next_release_roadmap.json"
    markdown_path = output_path / "next_release_roadmap.md"
    readme_path = output_path / "README_NEXT_RELEASE_ROADMAP.md"
    result = NextReleaseRoadmapResult(
        status="review_required",
        roadmap_status="review_required",
        output_dir=str(output_path),
        sections=ROADMAP_SECTIONS,
        section_count=len(ROADMAP_SECTIONS),
        review_required_count=review_count,
        generated_files=(str(json_path), str(markdown_path), str(readme_path)),
        summary_json_path=str(json_path),
        summary_markdown_path=str(markdown_path),
        readme_path=str(readme_path),
        warnings=(NEXT_RELEASE_ROADMAP_WARNING,),
        errors=(),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
        project_use_allowed=False,
    )
    json_path.write_text(
        json.dumps({"report_type": "next_release_roadmap", **result.__dict__}, indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(render_next_release_roadmap_markdown(result), encoding="utf-8")
    readme_path.write_text(_render_readme(result), encoding="utf-8")
    return result


def render_next_release_roadmap_markdown(result: NextReleaseRoadmapResult) -> str:
    """Render next release roadmap as Markdown."""
    lines = [
        "# Next Release Roadmap",
        "",
        NEXT_RELEASE_ROADMAP_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "project_use_allowed = false",
        "",
        "## Summary",
        "",
        f"- roadmap_status: `{result.roadmap_status}`",
        f"- section_count: `{result.section_count}`",
        f"- review_required_count: `{result.review_required_count}`",
        "",
    ]
    for section in result.sections:
        lines.extend(
            [
                f"## {section['title']}",
                "",
                f"- section_id: `{section['section_id']}`",
                f"- target_release: `{section['target_release']}`",
                f"- status: `{section['status']}`",
                "",
                "Milestones:",
                "",
                *[f"- {milestone}" for milestone in section["milestones"]],
                "",
            ]
        )
    return "\n".join(lines)


def _render_readme(result: NextReleaseRoadmapResult) -> str:
    return "\n".join(
        [
            "# README Next Release Roadmap",
            "",
            NEXT_RELEASE_ROADMAP_WARNING,
            "",
            f"roadmap_status: `{result.roadmap_status}`",
            "project_use_allowed: `false`",
            "ml_ready_for_project_use: `false`",
            "",
            "Use this roadmap for planning only. It is not release approval.",
        ]
    ) + "\n"
