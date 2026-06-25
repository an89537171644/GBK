"""Engineer review packet for v0.9 review handoff."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.workflows.clean_demo_verify import run_clean_demo_and_verify
from sp63_core.workflows.external_validation_evidence_package import (
    build_external_validation_evidence_package,
)
from sp63_core.workflows.material_verification_closure import (
    build_material_verification_closure,
)
from sp63_core.workflows.release_notes import build_release_notes_package
from sp63_core.workflows.traceability_matrix import build_traceability_matrix
from sp63_core.workflows.v09_final_audit import build_v09_final_audit
from sp63_core.workflows.v09_freeze_report import build_v09_freeze_report
from sp63_core.workflows.v10_gap_report import build_v10_gap_report

ENGINEER_REVIEW_PACKET_WARNING = (
    "Engineer review packet is handoff evidence only. It does not certify "
    "designs, approve project use, or make ML project-ready."
)


@dataclass(frozen=True)
class EngineerReviewPacketResult:
    """Engineer review packet result."""

    status: str
    packet_status: str
    output_dir: str
    evidence_items: tuple[dict[str, Any], ...]
    evidence_count: int
    review_required_count: int
    failed_count: int
    generated_files: tuple[str, ...]
    readme_path: str
    packet_json_path: str
    packet_markdown_path: str
    review_checklist_path: str
    evidence_index_path: str
    manifest_path: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False
    project_use_allowed: bool = False


def build_engineer_review_packet(*, output_dir: Path) -> EngineerReviewPacketResult:
    """Build an engineer review packet with links to generated evidence."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    v09_freeze = build_v09_freeze_report(output_dir=output_path / "v09_freeze_report")
    v09_final = build_v09_final_audit(output_dir=output_path / "v09_final_audit")
    v10_gap = build_v10_gap_report(output_dir=output_path / "v10_gap_report")
    material = build_material_verification_closure(
        output_dir=output_path / "material_verification_closure"
    )
    external = build_external_validation_evidence_package(
        output_dir=output_path / "external_validation_evidence"
    )
    traceability = build_traceability_matrix(output_dir=output_path / "traceability_matrix")
    clean_demo = run_clean_demo_and_verify(output_dir=output_path / "clean_demo_verification")
    release_notes = build_release_notes_package(output_dir=output_path / "release_notes")

    evidence_items = (
        _evidence("v09-freeze-report", v09_freeze.status, v09_freeze.summary_markdown_path),
        _evidence("v09-final-audit", v09_final.status, v09_final.summary_markdown_path),
        _evidence("v10-gap-report", v10_gap.status, v10_gap.summary_markdown_path),
        _evidence(
            "material-verification-closure",
            material.status,
            material.generated_files[1] if len(material.generated_files) > 1 else "",
        ),
        _evidence(
            "external-validation-evidence-package",
            external.status,
            external.summary_markdown_path,
        ),
        _evidence(
            "traceability-matrix",
            traceability.status,
            traceability.generated_files[1] if len(traceability.generated_files) > 1 else "",
        ),
        _evidence("clean-demo-verification", clean_demo.status, clean_demo.summary_markdown_path),
        _evidence("release-notes", release_notes.status, release_notes.release_notes_markdown_path),
        _evidence("known-limitations", "review_required", "docs/known_limitations_v0_9.md"),
        _evidence(
            "acceptance-checklist",
            "review_required",
            "docs/user_manual/acceptance_checklist.md",
        ),
    )
    failed_count = sum(1 for item in evidence_items if item["status"] == "fail")
    review_required_count = sum(1 for item in evidence_items if item["status"] == "review_required")
    status = "fail" if failed_count else "review_required"

    readme_path = output_path / "README_ENGINEER_REVIEW.md"
    packet_json_path = output_path / "engineer_review_packet.json"
    packet_markdown_path = output_path / "engineer_review_packet.md"
    review_checklist_path = output_path / "review_checklist.md"
    evidence_index_path = output_path / "evidence_index.md"
    manifest_path = output_path / "packet_manifest.json"
    generated_files = (
        readme_path,
        packet_json_path,
        packet_markdown_path,
        review_checklist_path,
        evidence_index_path,
        manifest_path,
    )
    result = EngineerReviewPacketResult(
        status=status,
        packet_status=status,
        output_dir=str(output_path),
        evidence_items=evidence_items,
        evidence_count=len(evidence_items),
        review_required_count=review_required_count,
        failed_count=failed_count,
        generated_files=tuple(str(path) for path in generated_files),
        readme_path=str(readme_path),
        packet_json_path=str(packet_json_path),
        packet_markdown_path=str(packet_markdown_path),
        review_checklist_path=str(review_checklist_path),
        evidence_index_path=str(evidence_index_path),
        manifest_path=str(manifest_path),
        warnings=(ENGINEER_REVIEW_PACKET_WARNING,),
        errors=tuple(
            f"evidence item failed: {item['name']}"
            for item in evidence_items
            if item["status"] == "fail"
        ),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
        project_use_allowed=False,
    )

    packet_json_path.write_text(
        json.dumps({"report_type": "engineer_review_packet", **result.__dict__}, indent=2),
        encoding="utf-8",
    )
    packet_markdown_path.write_text(
        render_engineer_review_packet_markdown(result),
        encoding="utf-8",
    )
    readme_path.write_text(_render_readme(result), encoding="utf-8")
    review_checklist_path.write_text(_render_review_checklist(), encoding="utf-8")
    evidence_index_path.write_text(_render_evidence_index(result), encoding="utf-8")
    manifest_path.write_text(
        json.dumps(_manifest(result), indent=2),
        encoding="utf-8",
    )
    return result


def render_engineer_review_packet_markdown(result: EngineerReviewPacketResult) -> str:
    """Render engineer review packet as Markdown."""
    lines = [
        "# Engineer Review Packet",
        "",
        ENGINEER_REVIEW_PACKET_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "project_use_allowed = false",
        "",
        "## Summary",
        "",
        f"- packet_status: `{result.packet_status}`",
        f"- evidence_count: `{result.evidence_count}`",
        f"- review_required_count: `{result.review_required_count}`",
        f"- failed_count: `{result.failed_count}`",
        "",
        "## Evidence",
        "",
        "| name | status | path |",
        "|---|---|---|",
    ]
    for item in result.evidence_items:
        lines.append(f"| {item['name']} | `{item['status']}` | `{item['path']}` |")
    return "\n".join(lines) + "\n"


def _evidence(name: str, status: str, path: str) -> dict[str, Any]:
    return {"name": name, "status": status, "path": path}


def _render_readme(result: EngineerReviewPacketResult) -> str:
    return "\n".join(
        [
            "# README Engineer Review",
            "",
            ENGINEER_REVIEW_PACKET_WARNING,
            "",
            f"packet_status: `{result.packet_status}`",
            "project_use_allowed: `false`",
            "ml_ready_for_project_use: `false`",
            "",
            "Review `review_checklist.md`, `evidence_index.md`, and packet reports.",
        ]
    ) + "\n"


def _render_review_checklist() -> str:
    return "\n".join(
        [
            "# Review Checklist",
            "",
            "- Confirm deterministic validation evidence.",
            "- Confirm material verification evidence or keep review gate open.",
            "- Confirm external validation evidence or keep review gate open.",
            "- Confirm known limitations are accepted for internal review only.",
            "- Confirm ML remains advisory-only.",
            "- Confirm `ml_ready_for_project_use = false`.",
            "- Confirm project use is not approved by this packet.",
        ]
    ) + "\n"


def _render_evidence_index(result: EngineerReviewPacketResult) -> str:
    lines = ["# Evidence Index", "", "| name | status | path |", "|---|---|---|"]
    for item in result.evidence_items:
        lines.append(f"| {item['name']} | `{item['status']}` | `{item['path']}` |")
    return "\n".join(lines) + "\n"


def _manifest(result: EngineerReviewPacketResult) -> dict[str, Any]:
    return {
        "report_type": "engineer_review_packet_manifest",
        "status": result.status,
        "generated_files": list(result.generated_files),
        "evidence_items": list(result.evidence_items),
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "ml_ready_for_project_use": False,
        "project_use_allowed": False,
    }
