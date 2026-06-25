"""v0.9 readiness gate for engineering workflow hardening."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.workflows.docs_audit import build_docs_audit_report
from sp63_core.workflows.protected_files_guard import run_protected_files_guard
from sp63_core.workflows.release_candidate import build_release_candidate_report
from sp63_core.workflows.release_manifest import build_release_artifact_manifest
from sp63_core.workflows.user_acceptance_smoke import run_user_acceptance_smoke

V09_READINESS_WARNING = (
    "v0.9 readiness gate is review evidence only. It does not certify designs, "
    "publish a release, approve project use, or make ML project-ready."
)


@dataclass(frozen=True)
class V09ReadinessResult:
    """v0.9 readiness gate result."""

    status: str
    readiness_status: str
    output_dir: str
    version: str
    gate_count: int
    passed_count: int
    review_required_count: int
    failed_count: int
    gates: tuple[dict[str, Any], ...]
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


def build_v09_readiness_gate(
    *,
    output_dir: Path,
    version: str = "0.9.0-rc1",
) -> V09ReadinessResult:
    """Build a v0.9 readiness summary without approving release or project use."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    gates = (
        _gate("protected-files-check", run_protected_files_guard().status),
        _gate("docs-audit", build_docs_audit_report().status),
        _gate(
            "release-manifest",
            build_release_artifact_manifest(
                output_dir=output_path / "release_manifest",
                version=version,
            ).status,
        ),
        _gate(
            "user-acceptance-smoke",
            run_user_acceptance_smoke(
                output_dir=output_path / "user_acceptance_smoke",
                version=version,
            ).status,
        ),
        _gate(
            "release-candidate-report",
            build_release_candidate_report(
                output_dir=output_path / "release_candidate",
                version=version,
            ).status,
        ),
    )
    passed_count = sum(1 for gate in gates if gate["status"] == "pass")
    review_required_count = sum(1 for gate in gates if gate["status"] == "review_required")
    failed_count = sum(1 for gate in gates if gate["status"] == "fail")
    status = _readiness_status(
        failed_count=failed_count,
        review_required_count=review_required_count,
    )
    blockers = tuple(gate["name"] for gate in gates if gate["status"] == "fail")
    recommendations = _recommendations(
        failed_count=failed_count,
        review_required_count=review_required_count,
    )

    summary_json_path = output_path / "v09_readiness_report.json"
    summary_markdown_path = output_path / "v09_readiness_report.md"
    result = V09ReadinessResult(
        status=status,
        readiness_status=status,
        output_dir=str(output_path),
        version=version,
        gate_count=len(gates),
        passed_count=passed_count,
        review_required_count=review_required_count,
        failed_count=failed_count,
        gates=gates,
        blockers=blockers,
        recommendations=recommendations,
        generated_files=(str(summary_json_path), str(summary_markdown_path)),
        summary_json_path=str(summary_json_path),
        summary_markdown_path=str(summary_markdown_path),
        warnings=(V09_READINESS_WARNING,),
        errors=tuple(f"readiness gate failed: {blocker}" for blocker in blockers),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    summary_json_path.write_text(
        json.dumps({"report_type": "v09_readiness_gate", **result.__dict__}, indent=2),
        encoding="utf-8",
    )
    summary_markdown_path.write_text(_render_v09_readiness_markdown(result), encoding="utf-8")
    return result


def _gate(name: str, status: str) -> dict[str, Any]:
    return {"name": name, "status": status}


def _readiness_status(*, failed_count: int, review_required_count: int) -> str:
    if failed_count:
        return "fail"
    if review_required_count:
        return "review_required"
    return "pass"


def _recommendations(*, failed_count: int, review_required_count: int) -> tuple[str, ...]:
    recommendations: list[str] = []
    if failed_count:
        recommendations.append("fix failed readiness gates before v0.9 release review")
    if review_required_count:
        recommendations.append("complete engineer review gates before project use")
    recommendations.append("keep ML advisory-only and deterministic SP63 checks mandatory")
    recommendations.append("do not treat readiness gate output as design certification")
    return tuple(recommendations)


def _render_v09_readiness_markdown(result: V09ReadinessResult) -> str:
    lines = [
        "# v0.9 Readiness Gate",
        "",
        V09_READINESS_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Summary",
        "",
        f"- version: `{result.version}`",
        f"- readiness_status: `{result.readiness_status}`",
        f"- gate_count: `{result.gate_count}`",
        f"- passed_count: `{result.passed_count}`",
        f"- review_required_count: `{result.review_required_count}`",
        f"- failed_count: `{result.failed_count}`",
        "",
        "## Gates",
        "",
        "| gate | status |",
        "|---|---|",
    ]
    for gate in result.gates:
        lines.append(f"| {gate['name']} | `{gate['status']}` |")
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
