"""v0.9 review build orchestrator."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.workflows.clean_demo_verify import verify_clean_demo_artifacts
from sp63_core.workflows.clean_demo_workflow import run_clean_demo_workflow
from sp63_core.workflows.engineer_review_packet import build_engineer_review_packet
from sp63_core.workflows.freeze_remediation_plan import build_freeze_remediation_plan
from sp63_core.workflows.portable_package import build_portable_package
from sp63_core.workflows.release_acceptance_checklist import (
    build_release_acceptance_checklist,
)
from sp63_core.workflows.release_bundle import build_release_bundle
from sp63_core.workflows.review_signoff_templates import build_review_signoff_templates
from sp63_core.workflows.static_launcher_dashboard import build_static_launcher_dashboard
from sp63_core.workflows.traceability_matrix import build_traceability_matrix
from sp63_core.workflows.v09_freeze_report import build_v09_freeze_report
from sp63_core.workflows.v10_gap_report import build_v10_gap_report

V09_REVIEW_BUILD_WARNING = (
    "v0.9 review build is a review package only. It does not certify designs, "
    "approve project use, or close manual engineer signoff gates."
)


@dataclass(frozen=True)
class V09ReviewBuildResult:
    """v0.9 review build result."""

    status: str
    review_build_status: str
    output_dir: str
    version: str
    artifact_items: tuple[dict[str, Any], ...]
    artifact_count: int
    critical_failed_count: int
    review_required_count: int
    generated_files: tuple[str, ...]
    readme_path: str
    summary_json_path: str
    summary_markdown_path: str
    manifest_path: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False
    project_use_allowed: bool = False


def build_v09_review_build(
    *,
    output_dir: Path,
    version: str = "0.9.0-rc1",
) -> V09ReviewBuildResult:
    """Build all v0.9 review artifacts under one output directory."""
    output_path = Path(output_dir)
    artifacts_path = output_path / "artifacts"
    artifacts_path.mkdir(parents=True, exist_ok=True)

    clean_demo = run_clean_demo_workflow(output_dir=artifacts_path / "clean_demo_workflow")
    clean_demo_verify = verify_clean_demo_artifacts(workflow_dir=Path(clean_demo.output_dir))
    portable = build_portable_package(output_dir=artifacts_path / "portable_package")
    release_bundle = build_release_bundle(
        output_dir=artifacts_path / "release_bundle",
        version=version,
    )
    traceability = build_traceability_matrix(output_dir=artifacts_path / "traceability_matrix")
    v10_gap = build_v10_gap_report(output_dir=artifacts_path / "v10_gap_report")
    v09_freeze = build_v09_freeze_report(
        output_dir=artifacts_path / "v09_freeze_report",
        version=version,
    )
    remediation = build_freeze_remediation_plan(
        output_dir=artifacts_path / "freeze_remediation_plan",
        version=version,
    )
    review_packet = build_engineer_review_packet(
        output_dir=artifacts_path / "engineer_review_packet"
    )
    static_launcher = build_static_launcher_dashboard(
        output_dir=artifacts_path / "static_launcher_dashboard"
    )
    acceptance = build_release_acceptance_checklist(
        output_dir=artifacts_path / "release_acceptance_checklist"
    )
    signoff = build_review_signoff_templates(
        output_dir=artifacts_path / "review_signoff_templates"
    )

    artifact_items = (
        _artifact("clean-demo-workflow", clean_demo.status, True, clean_demo.output_dir),
        _artifact(
            "clean-demo-verify",
            clean_demo_verify.status,
            True,
            clean_demo_verify.summary_markdown_path,
        ),
        _artifact("portable-package", portable.status, True, portable.manifest_path),
        _artifact("release-bundle", release_bundle.status, True, release_bundle.manifest_path),
        _artifact("traceability-matrix", traceability.status, True, _path_at(traceability, 1)),
        _artifact("v10-gap-report", v10_gap.status, False, v10_gap.summary_markdown_path),
        _artifact("v09-freeze-report", v09_freeze.status, False, v09_freeze.summary_markdown_path),
        _artifact(
            "freeze-remediation-plan",
            remediation.status,
            False,
            remediation.summary_markdown_path,
        ),
        _artifact(
            "engineer-review-packet",
            review_packet.status,
            False,
            review_packet.packet_markdown_path,
        ),
        _artifact(
            "static-launcher-dashboard",
            static_launcher.status,
            True,
            static_launcher.dashboard_html_path,
        ),
        _artifact(
            "release-acceptance-checklist",
            acceptance.status,
            False,
            acceptance.summary_markdown_path,
        ),
        _artifact("review-signoff-templates", signoff.status, False, signoff.manifest_path),
    )
    critical_failed_count = sum(
        1 for item in artifact_items if item["critical"] and item["status"] == "fail"
    )
    review_required_count = sum(
        1 for item in artifact_items if item["status"] == "review_required"
    )
    status = (
        "fail"
        if critical_failed_count
        else "review_required"
        if review_required_count
        else "pass"
    )

    readme_path = output_path / "README_V09_REVIEW_BUILD.md"
    summary_json_path = output_path / "v09_review_build.json"
    summary_markdown_path = output_path / "v09_review_build.md"
    manifest_path = output_path / "manifest.json"
    result = V09ReviewBuildResult(
        status=status,
        review_build_status=status,
        output_dir=str(output_path),
        version=version,
        artifact_items=artifact_items,
        artifact_count=len(artifact_items),
        critical_failed_count=critical_failed_count,
        review_required_count=review_required_count,
        generated_files=(
            str(readme_path),
            str(summary_json_path),
            str(summary_markdown_path),
            str(manifest_path),
        ),
        readme_path=str(readme_path),
        summary_json_path=str(summary_json_path),
        summary_markdown_path=str(summary_markdown_path),
        manifest_path=str(manifest_path),
        warnings=(V09_REVIEW_BUILD_WARNING,),
        errors=tuple(
            f"critical review build artifact failed: {item['name']}"
            for item in artifact_items
            if item["critical"] and item["status"] == "fail"
        ),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
        project_use_allowed=False,
    )
    summary_json_path.write_text(
        json.dumps({"report_type": "v09_review_build", **result.__dict__}, indent=2),
        encoding="utf-8",
    )
    summary_markdown_path.write_text(render_v09_review_build_markdown(result), encoding="utf-8")
    readme_path.write_text(_render_readme(result), encoding="utf-8")
    manifest_path.write_text(json.dumps(_manifest(result), indent=2), encoding="utf-8")
    return result


def render_v09_review_build_markdown(result: V09ReviewBuildResult) -> str:
    """Render v0.9 review build as Markdown."""
    lines = [
        "# v0.9 Review Build",
        "",
        V09_REVIEW_BUILD_WARNING,
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
        f"- review_build_status: `{result.review_build_status}`",
        f"- artifact_count: `{result.artifact_count}`",
        f"- critical_failed_count: `{result.critical_failed_count}`",
        f"- review_required_count: `{result.review_required_count}`",
        "",
        "## Artifacts",
        "",
        "| name | status | critical | path |",
        "|---|---|---:|---|",
    ]
    for item in result.artifact_items:
        lines.append(
            f"| {item['name']} | `{item['status']}` | "
            f"`{item['critical']}` | `{item['path']}` |"
        )
    return "\n".join(lines) + "\n"


def _artifact(name: str, status: str, critical: bool, path: str) -> dict[str, Any]:
    return {"name": name, "status": status, "critical": critical, "path": path}


def _path_at(result: Any, index: int) -> str:
    files = getattr(result, "generated_files", ())
    return files[index] if len(files) > index else ""


def _render_readme(result: V09ReviewBuildResult) -> str:
    return "\n".join(
        [
            "# README v0.9 Review Build",
            "",
            V09_REVIEW_BUILD_WARNING,
            "",
            f"review_build_status: `{result.review_build_status}`",
            "project_use_allowed: `false`",
            "ml_ready_for_project_use: `false`",
            "",
            "Review `v09_review_build.md` and `manifest.json` before handoff.",
        ]
    ) + "\n"


def _manifest(result: V09ReviewBuildResult) -> dict[str, Any]:
    return {
        "report_type": "v09_review_build_manifest",
        "status": result.status,
        "version": result.version,
        "artifact_items": list(result.artifact_items),
        "generated_files": list(result.generated_files),
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "ml_ready_for_project_use": False,
        "project_use_allowed": False,
    }
