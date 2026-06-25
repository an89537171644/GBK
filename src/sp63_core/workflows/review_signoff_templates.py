"""Review signoff template generator with placeholder-only fields."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

REVIEW_SIGNOFF_WARNING = (
    "Review signoff templates contain placeholders only. They do not add "
    "personal data, approve project use, or certify calculations."
)

TEMPLATES: tuple[dict[str, str], ...] = (
    {
        "filename": "material_review_signoff_template.md",
        "title": "Material Review Signoff Template",
        "scope": "material catalog value verification",
    },
    {
        "filename": "external_validation_signoff_template.md",
        "title": "External Validation Signoff Template",
        "scope": "manual/Excel/SCAD/LIRA external validation evidence",
    },
    {
        "filename": "ml_advisory_signoff_template.md",
        "title": "ML Advisory Signoff Template",
        "scope": "ML advisory-only governance and deterministic verification",
    },
    {
        "filename": "release_review_signoff_template.md",
        "title": "Release Review Signoff Template",
        "scope": "v0.9 review build and known limitations",
    },
)


@dataclass(frozen=True)
class ReviewSignoffTemplatesResult:
    """Review signoff templates result."""

    status: str
    output_dir: str
    template_count: int
    generated_files: tuple[str, ...]
    manifest_path: str
    readme_path: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False
    project_use_allowed: bool = False


def build_review_signoff_templates(*, output_dir: Path) -> ReviewSignoffTemplatesResult:
    """Build placeholder-only review signoff templates."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for template in TEMPLATES:
        path = output_path / template["filename"]
        path.write_text(
            _render_template(title=template["title"], scope=template["scope"]),
            encoding="utf-8",
        )
        generated.append(path)

    manifest_path = output_path / "review_signoff_manifest.json"
    readme_path = output_path / "README_REVIEW_SIGNOFF_TEMPLATES.md"
    generated.extend([manifest_path, readme_path])
    result = ReviewSignoffTemplatesResult(
        status="pass",
        output_dir=str(output_path),
        template_count=len(TEMPLATES),
        generated_files=tuple(str(path) for path in generated),
        manifest_path=str(manifest_path),
        readme_path=str(readme_path),
        warnings=(REVIEW_SIGNOFF_WARNING,),
        errors=(),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
        project_use_allowed=False,
    )
    manifest_path.write_text(
        json.dumps({"report_type": "review_signoff_templates", **result.__dict__}, indent=2),
        encoding="utf-8",
    )
    readme_path.write_text(_render_readme(), encoding="utf-8")
    return result


def _render_template(*, title: str, scope: str) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            REVIEW_SIGNOFF_WARNING,
            "",
            "engineer_name_placeholder: `<engineer name>`",
            "review_date_placeholder: `<YYYY-MM-DD>`",
            "organization_placeholder: `<organization>`",
            f"scope: `{scope}`",
            "reviewed_artifacts:",
            "- `<artifact path>`",
            "status: `<engineer_verified | needs_review | rejected>`",
            "notes: `<review notes>`",
            "signature_placeholder: `<signature>`",
            "",
            "requires_engineer_review = true",
            "ml_is_advisory_only = true",
            "deterministic_checks_required = true",
            "ml_ready_for_project_use = false",
            "project_use_allowed = false",
        ]
    ) + "\n"


def _render_readme() -> str:
    return "\n".join(
        [
            "# README Review Signoff Templates",
            "",
            REVIEW_SIGNOFF_WARNING,
            "",
            "The templates intentionally contain placeholders only.",
            "Do not commit filled templates if they contain personal or private data.",
        ]
    ) + "\n"
