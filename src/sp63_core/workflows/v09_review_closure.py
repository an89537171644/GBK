"""v0.9 manual review closure and release-candidate stabilization report."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sp63_core.workflows.clean_demo_verify import verify_clean_demo_artifacts
from sp63_core.workflows.clean_demo_workflow import run_clean_demo_workflow
from sp63_core.workflows.docs_audit import build_docs_audit_report
from sp63_core.workflows.next_release_roadmap import build_next_release_roadmap
from sp63_core.workflows.protected_files_guard import run_protected_files_guard
from sp63_core.workflows.release_acceptance_checklist import (
    build_release_acceptance_checklist,
)
from sp63_core.workflows.v09_final_audit import build_v09_final_audit
from sp63_core.workflows.v09_freeze_report import build_v09_freeze_report
from sp63_core.workflows.v09_review_build import build_v09_review_build

V09_REVIEW_CLOSURE_WARNING = (
    "v0.9 review closure is manual review evidence only. It does not certify "
    "designs, approve project use, or close engineer signoff gates automatically."
)

ACCEPTABLE_REVIEW_GATES: tuple[dict[str, Any], ...] = (
    {
        "gate_id": "material_engineer_review",
        "status": "review_required",
        "auto_close_allowed": False,
        "reason": "material catalog verification must be signed off by an engineer",
    },
    {
        "gate_id": "external_validation_engineer_review",
        "status": "review_required",
        "auto_close_allowed": False,
        "reason": "real manual/Excel/SCAD/LIRA validation remains separate",
    },
    {
        "gate_id": "manual_engineer_signoff",
        "status": "review_required",
        "auto_close_allowed": False,
        "reason": "manual release acceptance signoff is not automated",
    },
    {
        "gate_id": "project_approval",
        "status": "not_approved",
        "auto_close_allowed": False,
        "reason": "review artifacts do not approve project use",
    },
)


@dataclass(frozen=True)
class V09ReviewClosureResult:
    """v0.9 manual review closure result."""

    status: str
    closure_status: str
    output_dir: str
    version: str
    checked_artifacts: tuple[dict[str, Any], ...]
    acceptable_review_gates: tuple[dict[str, Any], ...]
    blocking_review_gates: tuple[dict[str, Any], ...]
    critical_failures: tuple[str, ...]
    ready_for_v09_review_build: bool
    ready_for_v09_release_candidate: bool
    ready_for_project_use: bool
    recommendations: tuple[str, ...]
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


def build_v09_review_closure(
    *,
    output_dir: Path,
    version: str = "0.9.0-rc1",
) -> V09ReviewClosureResult:
    """Build the manual v0.9 review closure report."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    protected = run_protected_files_guard()
    docs = build_docs_audit_report(output_dir=output_path / "docs")
    clean_demo = run_clean_demo_workflow(output_dir=output_path / "demo")
    clean_demo_verify = verify_clean_demo_artifacts(workflow_dir=Path(clean_demo.output_dir))
    acceptance = build_release_acceptance_checklist(
        output_dir=output_path / "acceptance"
    )
    final_audit = build_v09_final_audit(
        output_dir=output_path / "audit",
        version=version,
    )
    freeze = build_v09_freeze_report(
        output_dir=output_path / "freeze",
        version=version,
    )
    review_build = build_v09_review_build(
        output_dir=output_path / "rb",
        version=version,
    )
    roadmap = build_next_release_roadmap(output_dir=output_path / "roadmap")

    checked_artifacts = (
        _artifact("protected-files-check", protected.status, True, None),
        _artifact("docs-audit", docs.status, True, docs.markdown_path),
        _artifact("clean-demo-workflow", clean_demo.status, True, clean_demo.output_dir),
        _artifact(
            "clean-demo-verify",
            clean_demo_verify.status,
            True,
            clean_demo_verify.summary_markdown_path,
        ),
        _artifact(
            "release-acceptance-checklist",
            acceptance.status,
            False,
            acceptance.summary_markdown_path,
        ),
        _artifact("v09-final-audit", final_audit.status, False, final_audit.summary_markdown_path),
        _artifact("v09-freeze-report", freeze.status, False, freeze.summary_markdown_path),
        _artifact(
            "v09-review-build",
            review_build.status,
            True,
            review_build.summary_markdown_path,
        ),
        _artifact("next-release-roadmap", roadmap.status, False, roadmap.summary_markdown_path),
    )
    known_limitations_documented = Path("docs/known_limitations_v0_9.md").exists()
    release_bundle_present = _review_build_artifact_passed(review_build, "release-bundle")
    state = _classify_v09_review_closure(
        checked_artifacts=checked_artifacts,
        acceptable_review_gates=ACCEPTABLE_REVIEW_GATES,
        release_bundle_present=release_bundle_present,
        clean_demo_pass=clean_demo.status == "pass",
        clean_demo_verify_pass=clean_demo_verify.status == "pass",
        protected_pass=protected.status == "pass",
        docs_pass=docs.status == "pass",
        known_limitations_documented=known_limitations_documented,
    )

    summary_json_path = output_path / "v09_review_closure.json"
    summary_markdown_path = output_path / "v09_review_closure.md"
    readme_path = output_path / "README_V09_REVIEW_CLOSURE.md"
    recommendations = _recommendations(
        critical_failures=state["critical_failures"],
        ready_for_v09_release_candidate=state["ready_for_v09_release_candidate"],
    )
    result = V09ReviewClosureResult(
        status=state["status"],
        closure_status=state["status"],
        output_dir=str(output_path),
        version=version,
        checked_artifacts=checked_artifacts,
        acceptable_review_gates=ACCEPTABLE_REVIEW_GATES,
        blocking_review_gates=state["blocking_review_gates"],
        critical_failures=state["critical_failures"],
        ready_for_v09_review_build=state["ready_for_v09_review_build"],
        ready_for_v09_release_candidate=state["ready_for_v09_release_candidate"],
        ready_for_project_use=False,
        recommendations=recommendations,
        generated_files=(str(summary_json_path), str(summary_markdown_path), str(readme_path)),
        summary_json_path=str(summary_json_path),
        summary_markdown_path=str(summary_markdown_path),
        readme_path=str(readme_path),
        warnings=(V09_REVIEW_CLOSURE_WARNING,),
        errors=tuple(state["critical_failures"]),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    _write_review_closure_outputs(result)
    return result


def render_v09_review_closure_markdown(result: V09ReviewClosureResult) -> str:
    """Render v0.9 review closure as Markdown."""
    lines = [
        "# v0.9 Review Closure",
        "",
        V09_REVIEW_CLOSURE_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "ready_for_project_use = false",
        "",
        "## Summary",
        "",
        f"- version: `{result.version}`",
        f"- closure_status: `{result.closure_status}`",
        f"- ready_for_v09_review_build: `{result.ready_for_v09_review_build}`",
        f"- ready_for_v09_release_candidate: `{result.ready_for_v09_release_candidate}`",
        f"- ready_for_project_use: `{result.ready_for_project_use}`",
        f"- critical_failures: `{len(result.critical_failures)}`",
        "",
        "## Checked Artifacts",
        "",
        "| name | status | critical | path |",
        "|---|---|---:|---|",
    ]
    for item in result.checked_artifacts:
        lines.append(
            f"| {item['name']} | `{item['status']}` | "
            f"`{item['critical']}` | `{item['path'] or ''}` |"
        )
    lines.extend(
        [
            "",
            "## Acceptable Manual Review Gates",
            "",
            "| gate_id | status | auto_close_allowed | reason |",
            "|---|---|---:|---|",
        ]
    )
    for gate in result.acceptable_review_gates:
        lines.append(
            "| {gate_id} | `{status}` | `{auto_close_allowed}` | {reason} |".format(**gate)
        )
    lines.extend(
        [
            "",
            "## Blocking Review Gates",
            "",
            *_gate_lines(result.blocking_review_gates),
            "",
            "## Recommendations",
            "",
            *_bullet_lines(result.recommendations),
            "",
            "## Errors",
            "",
            *_bullet_lines(result.errors),
        ]
    )
    return "\n".join(lines) + "\n"


def _classify_v09_review_closure(
    *,
    checked_artifacts: tuple[dict[str, Any], ...],
    acceptable_review_gates: tuple[dict[str, Any], ...],
    release_bundle_present: bool,
    clean_demo_pass: bool,
    clean_demo_verify_pass: bool,
    protected_pass: bool,
    docs_pass: bool,
    known_limitations_documented: bool,
) -> dict[str, Any]:
    critical_failures = tuple(
        f"critical artifact failed: {item['name']}"
        for item in checked_artifacts
        if item["critical"] and item["status"] == "fail"
    )
    blocking_review_gates: list[dict[str, Any]] = [
        {
            "gate_id": item["name"],
            "status": item["status"],
            "reason": "critical generated review artifact failed",
        }
        for item in checked_artifacts
        if item["critical"] and item["status"] == "fail"
    ]
    if not release_bundle_present:
        blocking_review_gates.append(
            {
                "gate_id": "release_bundle",
                "status": "missing_or_failed",
                "reason": "v0.9 review build did not produce a passing release bundle",
            }
        )
    if not known_limitations_documented:
        blocking_review_gates.append(
            {
                "gate_id": "known_limitations_documented",
                "status": "missing",
                "reason": "docs/known_limitations_v0_9.md is required for release review",
            }
        )

    ready_for_review_build = not critical_failures
    ready_for_release_candidate = (
        not critical_failures
        and release_bundle_present
        and clean_demo_pass
        and clean_demo_verify_pass
        and protected_pass
        and docs_pass
        and known_limitations_documented
    )
    status = (
        "fail"
        if critical_failures
        else "review_required"
        if acceptable_review_gates or blocking_review_gates
        else "pass"
    )
    return {
        "status": status,
        "critical_failures": critical_failures,
        "blocking_review_gates": tuple(blocking_review_gates),
        "ready_for_v09_review_build": ready_for_review_build,
        "ready_for_v09_release_candidate": ready_for_release_candidate,
    }


def _artifact(name: str, status: str, critical: bool, path: str | None) -> dict[str, Any]:
    return {"name": name, "status": status, "critical": critical, "path": path}


def _review_build_artifact_passed(result: Any, artifact_name: str) -> bool:
    return any(
        item["name"] == artifact_name and item["status"] == "pass"
        for item in result.artifact_items
    )


def _recommendations(
    *,
    critical_failures: tuple[str, ...],
    ready_for_v09_release_candidate: bool,
) -> tuple[str, ...]:
    recommendations: list[str] = []
    if critical_failures:
        recommendations.append("fix critical closure failures before v0.9 review handoff")
    if ready_for_v09_release_candidate:
        recommendations.append("use v0.9 artifacts for manual release-candidate review only")
    else:
        recommendations.append("rerun v0.9 closure after fixing release-candidate blockers")
    recommendations.extend(
        [
            "complete material engineer verification before project use",
            "complete real external validation before project use",
            "complete manual engineer signoff before any release decision",
            "keep ML advisory-only and deterministic SP63 checks mandatory",
            "keep ready_for_project_use false until a separate engineer approval process",
        ]
    )
    return tuple(recommendations)


def _write_review_closure_outputs(result: V09ReviewClosureResult) -> None:
    output_path = Path(result.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    payload = {"report_type": "v09_review_closure", **asdict(result)}
    Path(result.summary_json_path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    Path(result.summary_markdown_path).write_text(
        render_v09_review_closure_markdown(result),
        encoding="utf-8",
    )
    Path(result.readme_path).write_text(_render_readme(result), encoding="utf-8")


def _render_readme(result: V09ReviewClosureResult) -> str:
    return "\n".join(
        [
            "# README v0.9 Review Closure",
            "",
            V09_REVIEW_CLOSURE_WARNING,
            "",
            f"version: `{result.version}`",
            f"closure_status: `{result.closure_status}`",
            f"ready_for_v09_review_build: `{result.ready_for_v09_review_build}`",
            f"ready_for_v09_release_candidate: `{result.ready_for_v09_release_candidate}`",
            "ready_for_project_use: `false`",
            "ml_ready_for_project_use: `false`",
            "",
            "Review `v09_review_closure.json` and `v09_review_closure.md` with an "
            "engineer before any release-candidate decision.",
        ]
    ) + "\n"


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]


def _gate_lines(values: tuple[dict[str, Any], ...]) -> list[str]:
    if not values:
        return ["- none"]
    return [
        f"- `{gate['gate_id']}`: `{gate['status']}` - {gate['reason']}" for gate in values
    ]
