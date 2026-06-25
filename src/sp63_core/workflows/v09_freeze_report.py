"""Final v0.9 freeze report for engineering review."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.workflows.clean_demo_verify import run_clean_demo_and_verify
from sp63_core.workflows.docs_audit import build_docs_audit_report
from sp63_core.workflows.protected_files_guard import run_protected_files_guard
from sp63_core.workflows.release_bundle import build_release_bundle
from sp63_core.workflows.release_manifest import build_release_artifact_manifest
from sp63_core.workflows.release_notes import build_release_notes_package
from sp63_core.workflows.traceability_matrix import build_traceability_matrix
from sp63_core.workflows.user_manual_index import build_user_manual_index
from sp63_core.workflows.v09_final_audit import build_v09_final_audit
from sp63_core.workflows.v10_gap_report import build_v10_gap_report

V09_FREEZE_WARNING = (
    "v0.9 freeze report is engineering review evidence only. It does not "
    "certify designs, approve project use, or make ML project-ready."
)


@dataclass(frozen=True)
class V09FreezeReportResult:
    """Final v0.9 freeze report result."""

    status: str
    freeze_status: str
    output_dir: str
    version: str
    freeze_items: tuple[dict[str, Any], ...]
    critical_failed_count: int
    review_required_count: int
    project_use_allowed: bool
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


def build_v09_freeze_report(
    *,
    output_dir: Path,
    version: str = "0.9.0-rc1",
) -> V09FreezeReportResult:
    """Build the final v0.9 freeze report."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    protected = run_protected_files_guard()
    docs = build_docs_audit_report()
    manual = build_user_manual_index(output_dir=output_path / "user_manual_index")
    release_notes = build_release_notes_package(
        output_dir=output_path / "release_notes",
        version=version,
    )
    release_manifest = build_release_artifact_manifest(
        output_dir=output_path / "release_manifest",
        version=version,
    )
    release_bundle = build_release_bundle(
        output_dir=output_path / "release_bundle",
        version=version,
    )
    clean_demo = run_clean_demo_and_verify(output_dir=output_path / "clean_demo_verify")
    traceability = build_traceability_matrix(output_dir=output_path / "traceability_matrix")
    v10_gap = build_v10_gap_report(output_dir=output_path / "v10_gap_report")
    v09_final = build_v09_final_audit(output_dir=output_path / "v09_final_audit")

    freeze_items = (
        _item("protected-files-check", protected.status, critical=True),
        _item("docs-audit", docs.status, critical=True),
        _item("user-manual-index", manual.status, critical=True),
        _item("release-notes", release_notes.status, critical=True),
        _item("release-manifest", release_manifest.status, critical=True),
        _item("release-bundle", release_bundle.status, critical=True),
        _item("clean-demo-verify", clean_demo.status, critical=True),
        _item("traceability-matrix", traceability.status, critical=True),
        _item("v10-gap-report", v10_gap.status, critical=False),
        _item("v09-final-audit", v09_final.status, critical=False),
    )
    critical_failed_count = sum(
        1 for item in freeze_items if item["critical"] and item["status"] == "fail"
    )
    review_required_count = sum(
        1 for item in freeze_items if item["status"] == "review_required"
    )
    status = _freeze_status(
        critical_failed_count=critical_failed_count,
        review_required_count=review_required_count,
    )
    errors = tuple(
        f"critical freeze item failed: {item['name']}"
        for item in freeze_items
        if item["critical"] and item["status"] == "fail"
    )

    json_path = output_path / "v09_freeze_report.json"
    markdown_path = output_path / "v09_freeze_report.md"
    readme_path = output_path / "README_V09_FREEZE.md"
    result = V09FreezeReportResult(
        status=status,
        freeze_status=status,
        output_dir=str(output_path),
        version=version,
        freeze_items=freeze_items,
        critical_failed_count=critical_failed_count,
        review_required_count=review_required_count,
        project_use_allowed=False,
        generated_files=(str(json_path), str(markdown_path), str(readme_path)),
        summary_json_path=str(json_path),
        summary_markdown_path=str(markdown_path),
        readme_path=str(readme_path),
        warnings=(V09_FREEZE_WARNING,),
        errors=errors,
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    json_path.write_text(
        json.dumps({"report_type": "v09_freeze_report", **result.__dict__}, indent=2),
        encoding="utf-8",
    )
    markdown = render_v09_freeze_report_markdown(result)
    markdown_path.write_text(markdown, encoding="utf-8")
    readme_path.write_text(_render_freeze_readme(result), encoding="utf-8")
    return result


def render_v09_freeze_report_markdown(result: V09FreezeReportResult) -> str:
    """Render v0.9 freeze report as Markdown."""
    lines = [
        "# v0.9 Freeze Report",
        "",
        V09_FREEZE_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Summary",
        "",
        f"- version: `{result.version}`",
        f"- freeze_status: `{result.freeze_status}`",
        f"- project_use_allowed: `{result.project_use_allowed}`",
        f"- critical_failed_count: `{result.critical_failed_count}`",
        f"- review_required_count: `{result.review_required_count}`",
        "",
        "## Freeze Items",
        "",
        "| item | status | critical |",
        "|---|---|---:|",
    ]
    for item in result.freeze_items:
        lines.append(f"| {item['name']} | `{item['status']}` | `{item['critical']}` |")
    lines.extend(
        [
            "",
            "## Errors",
            "",
            *_bullet_lines(result.errors),
            "",
            "## Known Limitations",
            "",
            "- Material verification remains separate from automatic catalog changes.",
            "- Real external validation remains mandatory before project use.",
            "- ML remains advisory-only and is not project-ready.",
            "- Freeze report output is not design certification.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_freeze_readme(result: V09FreezeReportResult) -> str:
    return "\n".join(
        [
            "# README V09 Freeze",
            "",
            V09_FREEZE_WARNING,
            "",
            f"version: `{result.version}`",
            f"freeze_status: `{result.freeze_status}`",
            "project_use_allowed: `false`",
            "requires_engineer_review: `true`",
            "ml_is_advisory_only: `true`",
            "deterministic_checks_required: `true`",
            "ml_ready_for_project_use: `false`",
            "",
            "Review `v09_freeze_report.json` and `v09_freeze_report.md` before any "
            "manual release-review decision.",
            "",
            "This folder may contain generated review evidence. Do not commit smoke "
            "output folders from local runs.",
        ]
    ) + "\n"


def _item(name: str, status: str, *, critical: bool) -> dict[str, Any]:
    return {"name": name, "status": status, "critical": critical}


def _freeze_status(*, critical_failed_count: int, review_required_count: int) -> str:
    if critical_failed_count:
        return "fail"
    if review_required_count:
        return "review_required"
    return "pass"


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values if value] if values else ["- none"]
