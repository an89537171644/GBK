"""Release notes package for v0.9 engineering review."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

RELEASE_NOTES_WARNING = (
    "Release notes package is documentation for engineering review only. It does "
    "not publish a release, certify designs, approve project use, or make ML "
    "project-ready."
)

SPRINT_SUMMARY: tuple[str, ...] = (
    "K83 material verification closure workflow",
    "K84 clean deterministic demo workflow",
    "K85 engineering handoff package",
    "K86 launcher scripts package",
    "K87 external validation evidence package",
    "K88 v0.9 final audit",
    "K89 agent sprint guard",
    "K90 release notes package",
)

KNOWN_LIMITATIONS: tuple[str, ...] = (
    "deterministic SP63 core remains draft-MVP and requires engineer review",
    "material catalog values require separate engineer verification before project use",
    "real external validation with manual/Excel/SCAD/LIRA values remains mandatory",
    "ML and neural surrogate outputs are advisory-only",
    "ml_ready_for_project_use remains false",
    "workflow/self-check/index/schema/preflight reports do not approve project use",
    "no full GUI or web application is implemented",
)


@dataclass(frozen=True)
class ReleaseNotesPackageResult:
    """Generated release notes package result."""

    status: str
    package_status: str
    output_dir: str
    version: str
    generated_files: tuple[str, ...]
    release_notes_json_path: str
    release_notes_markdown_path: str
    release_checklist_path: str
    known_limitations_path: str
    sprint_summary: tuple[str, ...]
    known_limitations: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_release_notes_package(
    *,
    output_dir: Path,
    version: str = "0.9.0-rc1",
) -> ReleaseNotesPackageResult:
    """Build release notes package artifacts without publishing a release."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / "release_notes_v0_9.json"
    markdown_path = output_path / "release_notes_v0_9.md"
    checklist_path = output_path / "v09_release_checklist.md"
    limitations_path = output_path / "known_limitations_v0_9.md"
    generated_files = (json_path, markdown_path, checklist_path, limitations_path)
    result = ReleaseNotesPackageResult(
        status="pass",
        package_status="pass",
        output_dir=str(output_path),
        version=version,
        generated_files=tuple(str(path) for path in generated_files),
        release_notes_json_path=str(json_path),
        release_notes_markdown_path=str(markdown_path),
        release_checklist_path=str(checklist_path),
        known_limitations_path=str(limitations_path),
        sprint_summary=SPRINT_SUMMARY,
        known_limitations=KNOWN_LIMITATIONS,
        warnings=(RELEASE_NOTES_WARNING,),
        errors=(),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    json_path.write_text(
        json.dumps({"report_type": "release_notes_v0_9", **result.__dict__}, indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(_render_release_notes(result), encoding="utf-8")
    checklist_path.write_text(_render_release_checklist(result), encoding="utf-8")
    limitations_path.write_text(_render_known_limitations(result), encoding="utf-8")
    return result


def _render_release_notes(result: ReleaseNotesPackageResult) -> str:
    lines = [
        "# v0.9 Engineering Release Notes",
        "",
        RELEASE_NOTES_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Version",
        "",
        f"`{result.version}`",
        "",
        "## Sprint Summary",
        "",
        *_bullet_lines(result.sprint_summary),
        "",
        "## Safety",
        "",
        "- deterministic SP63 checks remain mandatory;",
        "- engineer review remains mandatory;",
        "- ML remains advisory-only;",
        "- no release publication or project approval is implied.",
    ]
    return "\n".join(lines) + "\n"


def _render_release_checklist(result: ReleaseNotesPackageResult) -> str:
    lines = [
        "# v0.9 Release Checklist",
        "",
        f"version: `{result.version}`",
        "",
        "- [ ] Review final audit report.",
        "- [ ] Review protected-files guard result.",
        "- [ ] Review material verification closure evidence.",
        "- [ ] Review real external validation evidence.",
        "- [ ] Review clean deterministic demo output.",
        "- [ ] Confirm generated smoke artifacts are not committed.",
        "- [ ] Confirm no full SP 63 text was added.",
        "- [ ] Confirm no personal, grant, private, SCAD, or LIRA files were added.",
        "- [ ] Confirm ML remains advisory-only.",
        "- [ ] Confirm `ml_ready_for_project_use = false`.",
        "- [ ] Confirm engineer review remains mandatory.",
    ]
    return "\n".join(lines) + "\n"


def _render_known_limitations(result: ReleaseNotesPackageResult) -> str:
    lines = [
        "# v0.9 Known Limitations",
        "",
        f"version: `{result.version}`",
        "",
        *_bullet_lines(result.known_limitations),
    ]
    return "\n".join(lines) + "\n"


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]
