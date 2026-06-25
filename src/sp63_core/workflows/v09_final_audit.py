"""Final v0.9 audit report for engineering release preparation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.workflows.clean_demo_workflow import run_clean_demo_workflow
from sp63_core.workflows.docs_audit import build_docs_audit_report
from sp63_core.workflows.engineering_handoff_package import build_engineering_handoff_package
from sp63_core.workflows.external_validation_evidence_package import (
    build_external_validation_evidence_package,
)
from sp63_core.workflows.launcher_scripts import build_launcher_scripts_package
from sp63_core.workflows.material_verification_closure import (
    build_material_verification_closure,
)
from sp63_core.workflows.protected_files_guard import run_protected_files_guard
from sp63_core.workflows.v09_readiness import build_v09_readiness_gate

FINAL_AUDIT_WARNING = (
    "v0.9 final audit is release-preparation evidence only. It does not publish "
    "a release, certify designs, approve project use, or make ML project-ready."
)
MATERIAL_FIXTURE = Path("tests/fixtures/material_verification_sample.csv")
EXTERNAL_SAMPLE = Path("docs/validation/samples/external_validation_filled_sample.csv")


@dataclass(frozen=True)
class V09FinalAuditResult:
    """Aggregated v0.9 final audit result."""

    status: str
    audit_status: str
    output_dir: str
    version: str
    audit_count: int
    passed_count: int
    review_required_count: int
    failed_count: int
    audit_items: tuple[dict[str, Any], ...]
    blockers: tuple[str, ...]
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


def build_v09_final_audit(
    *,
    output_dir: Path,
    version: str = "0.9.0-rc1",
) -> V09FinalAuditResult:
    """Build the aggregated v0.9 final audit report."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    audit_items = (
        _item("protected-files-check", run_protected_files_guard().status),
        _item("docs-audit", build_docs_audit_report().status),
        _item(
            "v09-readiness",
            build_v09_readiness_gate(
                output_dir=output_path / "v09_readiness",
                version=version,
            ).status,
        ),
        _item(
            "clean-demo-workflow",
            run_clean_demo_workflow(output_dir=output_path / "clean_demo_workflow").status,
        ),
        _item(
            "engineering-handoff-package",
            build_engineering_handoff_package(
                output_dir=output_path / "engineering_handoff_package"
            ).status,
        ),
        _item(
            "launcher-scripts",
            build_launcher_scripts_package(output_dir=output_path / "launcher_scripts").status,
        ),
        _item(
            "material-verification-closure",
            build_material_verification_closure(
                material_verification_csv=MATERIAL_FIXTURE,
                output_dir=output_path / "material_verification_closure",
            ).status,
        ),
        _item(
            "external-validation-evidence-package",
            build_external_validation_evidence_package(
                output_dir=output_path / "external_validation_evidence",
                external_validation_csv=EXTERNAL_SAMPLE,
                strict_mode=True,
            ).status,
        ),
    )
    passed_count = sum(1 for item in audit_items if item["status"] == "pass")
    review_required_count = sum(1 for item in audit_items if item["status"] == "review_required")
    failed_count = sum(1 for item in audit_items if item["status"] == "fail")
    status = _audit_status(
        failed_count=failed_count,
        review_required_count=review_required_count,
    )
    blockers = tuple(item["name"] for item in audit_items if item["status"] == "fail")
    recommendations = _recommendations(
        failed_count=failed_count,
        review_required_count=review_required_count,
    )

    summary_json_path = output_path / "v09_final_audit.json"
    summary_markdown_path = output_path / "v09_final_audit.md"
    result = V09FinalAuditResult(
        status=status,
        audit_status=status,
        output_dir=str(output_path),
        version=version,
        audit_count=len(audit_items),
        passed_count=passed_count,
        review_required_count=review_required_count,
        failed_count=failed_count,
        audit_items=audit_items,
        blockers=blockers,
        recommendations=recommendations,
        generated_files=(str(summary_json_path), str(summary_markdown_path)),
        summary_json_path=str(summary_json_path),
        summary_markdown_path=str(summary_markdown_path),
        warnings=(FINAL_AUDIT_WARNING,),
        errors=tuple(f"final audit item failed: {blocker}" for blocker in blockers),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    summary_json_path.write_text(
        json.dumps({"report_type": "v09_final_audit", **result.__dict__}, indent=2),
        encoding="utf-8",
    )
    summary_markdown_path.write_text(_render_final_audit_markdown(result), encoding="utf-8")
    return result


def _item(name: str, status: str) -> dict[str, Any]:
    return {"name": name, "status": status}


def _audit_status(*, failed_count: int, review_required_count: int) -> str:
    if failed_count:
        return "fail"
    if review_required_count:
        return "review_required"
    return "pass"


def _recommendations(*, failed_count: int, review_required_count: int) -> tuple[str, ...]:
    recommendations: list[str] = []
    if failed_count:
        recommendations.append("fix failed audit items before release review")
    if review_required_count:
        recommendations.append("complete engineer review gates before project use")
    recommendations.append("complete real external validation before engineering use")
    recommendations.append("keep material verification separate from automatic catalog changes")
    recommendations.append("keep ML advisory-only and deterministic SP63 checks mandatory")
    recommendations.append("do not treat final audit output as design certification")
    return tuple(recommendations)


def _render_final_audit_markdown(result: V09FinalAuditResult) -> str:
    lines = [
        "# v0.9 Final Audit",
        "",
        FINAL_AUDIT_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Summary",
        "",
        f"- version: `{result.version}`",
        f"- audit_status: `{result.audit_status}`",
        f"- audit_count: `{result.audit_count}`",
        f"- passed_count: `{result.passed_count}`",
        f"- review_required_count: `{result.review_required_count}`",
        f"- failed_count: `{result.failed_count}`",
        "",
        "## Audit Items",
        "",
        "| item | status |",
        "|---|---|",
    ]
    for item in result.audit_items:
        lines.append(f"| {item['name']} | `{item['status']}` |")
    lines.extend(
        [
            "",
            "## Recommendations",
            "",
            *_bullet_lines(result.recommendations),
            "",
            "## Blockers",
            "",
            *_bullet_lines(result.blockers),
        ]
    )
    return "\n".join(lines) + "\n"


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]
