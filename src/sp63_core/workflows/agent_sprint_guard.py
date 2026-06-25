"""Local sprint guard for Codex K-step continuation checks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

AGENT_SPRINT_GUARD_WARNING = (
    "Agent sprint guard is a local completeness check only. It does not inspect "
    "GitHub state, approve merges, certify designs, or make ML project-ready."
)


@dataclass(frozen=True)
class SprintStepSpec:
    """Expected files for a K-step."""

    k: int
    title: str
    required_paths: tuple[str, ...]


@dataclass(frozen=True)
class AgentSprintGuardResult:
    """Local sprint guard result."""

    status: str
    guard_status: str
    from_k: int
    to_k: int
    checked_step_count: int
    completed_count: int
    missing_count: int
    completed_steps: tuple[int, ...]
    missing_steps: tuple[dict[str, Any], ...]
    proposed_next_k: int | None
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


DEFAULT_SPRINT_STEP_SPECS: tuple[SprintStepSpec, ...] = (
    SprintStepSpec(
        k=83,
        title="material verification closure workflow",
        required_paths=(
            "src/sp63_core/workflows/material_verification_closure.py",
            "tests/test_material_verification_closure.py",
            "docs/material_verification_closure.md",
        ),
    ),
    SprintStepSpec(
        k=84,
        title="clean deterministic demo workflow",
        required_paths=(
            "src/sp63_core/workflows/clean_demo_workflow.py",
            "tests/test_clean_demo_workflow.py",
            "docs/clean_demo_workflow.md",
        ),
    ),
    SprintStepSpec(
        k=85,
        title="engineering handoff package",
        required_paths=(
            "src/sp63_core/workflows/engineering_handoff_package.py",
            "tests/test_engineering_handoff_package.py",
            "docs/engineering_handoff_package.md",
        ),
    ),
    SprintStepSpec(
        k=86,
        title="launcher scripts package",
        required_paths=(
            "src/sp63_core/workflows/launcher_scripts.py",
            "tests/test_launcher_scripts.py",
            "docs/launcher_scripts.md",
        ),
    ),
    SprintStepSpec(
        k=87,
        title="external validation evidence package",
        required_paths=(
            "src/sp63_core/workflows/external_validation_evidence_package.py",
            "tests/test_external_validation_evidence_package.py",
            "docs/external_validation_evidence_package.md",
        ),
    ),
    SprintStepSpec(
        k=88,
        title="v0.9 final audit",
        required_paths=(
            "src/sp63_core/workflows/v09_final_audit.py",
            "tests/test_v09_final_audit.py",
            "docs/v09_final_audit.md",
        ),
    ),
    SprintStepSpec(
        k=89,
        title="agent sprint guard",
        required_paths=(
            "src/sp63_core/workflows/agent_sprint_guard.py",
            "tests/test_agent_sprint_guard.py",
            "docs/agent_sprint_guard.md",
        ),
    ),
    SprintStepSpec(
        k=90,
        title="release notes package",
        required_paths=(
            "src/sp63_core/workflows/release_notes.py",
            "tests/test_release_notes.py",
            "docs/release_notes_v0_9.md",
            "docs/v09_release_checklist.md",
            "docs/known_limitations_v0_9.md",
        ),
    ),
)


def build_agent_sprint_guard(
    *,
    from_k: int,
    to_k: int,
    root_dir: Path = Path("."),
    step_specs: tuple[SprintStepSpec, ...] = DEFAULT_SPRINT_STEP_SPECS,
) -> AgentSprintGuardResult:
    """Check local K-step artifact completeness for a sprint range."""
    if from_k > to_k:
        return AgentSprintGuardResult(
            status="fail",
            guard_status="fail",
            from_k=from_k,
            to_k=to_k,
            checked_step_count=0,
            completed_count=0,
            missing_count=0,
            completed_steps=(),
            missing_steps=(),
            proposed_next_k=None,
            warnings=(AGENT_SPRINT_GUARD_WARNING,),
            errors=("from_k must be less than or equal to to_k",),
        )

    selected_specs = tuple(spec for spec in step_specs if from_k <= spec.k <= to_k)
    completed_steps: list[int] = []
    missing_steps: list[dict[str, Any]] = []
    root_path = Path(root_dir)
    for spec in selected_specs:
        missing_paths = tuple(
            path for path in spec.required_paths if not (root_path / path).exists()
        )
        if missing_paths:
            missing_steps.append(
                {
                    "k": spec.k,
                    "title": spec.title,
                    "missing_paths": missing_paths,
                }
            )
        else:
            completed_steps.append(spec.k)

    status = "pass" if not missing_steps else "review_required"
    proposed_next_k = missing_steps[0]["k"] if missing_steps else None
    return AgentSprintGuardResult(
        status=status,
        guard_status=status,
        from_k=from_k,
        to_k=to_k,
        checked_step_count=len(selected_specs),
        completed_count=len(completed_steps),
        missing_count=len(missing_steps),
        completed_steps=tuple(completed_steps),
        missing_steps=tuple(missing_steps),
        proposed_next_k=proposed_next_k,
        warnings=(AGENT_SPRINT_GUARD_WARNING,),
        errors=(),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )


def render_agent_sprint_guard_json(result: AgentSprintGuardResult) -> str:
    """Render sprint guard result as JSON."""
    return json.dumps({"report_type": "agent_sprint_guard", **result.__dict__}, indent=2)
