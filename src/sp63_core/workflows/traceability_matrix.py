"""Traceability matrix for v0.9 engineering review workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TRACEABILITY_WARNING = (
    "Traceability matrix is review navigation only. It does not certify designs, "
    "approve project use, or make ML project-ready."
)

TRACEABILITY_ROWS: tuple[dict[str, Any], ...] = (
    {
        "feature": "deterministic validation",
        "cli_command": "python -m sp63_core validate --golden",
        "doc_path": "docs/validation_report.md",
        "test_path": "tests/test_validation_golden.py",
        "safety_warnings": ("engineer review remains mandatory",),
        "project_use_allowed": False,
    },
    {
        "feature": "manual cases",
        "cli_command": "python -m sp63_core manual-cases --json",
        "doc_path": "docs/validation/manual_sp63_cases.md",
        "test_path": "tests/test_validation_manual_cases.py",
        "safety_warnings": ("manual cases are draft MVP checks",),
        "project_use_allowed": False,
    },
    {
        "feature": "materials audit",
        "cli_command": "python -m sp63_core materials-audit --json",
        "doc_path": "docs/materials_audit.md",
        "test_path": "tests/test_materials_audit.py",
        "safety_warnings": ("material values require engineer verification",),
        "project_use_allowed": False,
    },
    {
        "feature": "external validation",
        "cli_command": "python -m sp63_core external-validation --sample --json",
        "doc_path": "docs/validation/external_validation_workflow.md",
        "test_path": "tests/test_external_validation_workflow.py",
        "safety_warnings": ("synthetic sample is not real SCAD/LIRA validation",),
        "project_use_allowed": False,
    },
    {
        "feature": "input form schema",
        "cli_command": "python -m sp63_core input-form-schema --json",
        "doc_path": "docs/input_form_schema.md",
        "test_path": "tests/test_input_form_schema.py",
        "safety_warnings": ("schema does not approve project use",),
        "project_use_allowed": False,
    },
    {
        "feature": "input preflight",
        "cli_command": "python -m sp63_core input-preflight --input-json <input.json> --json",
        "doc_path": "docs/input_preflight.md",
        "test_path": "tests/test_input_preflight.py",
        "safety_warnings": ("preflight is not a design checker",),
        "project_use_allowed": False,
    },
    {
        "feature": "clean demo workflow",
        "cli_command": "python -m sp63_core clean-demo-workflow --output-dir <dir> --json",
        "doc_path": "docs/clean_demo_workflow.md",
        "test_path": "tests/test_clean_demo_workflow.py",
        "safety_warnings": ("clean demo is smoke evidence only",),
        "project_use_allowed": False,
    },
    {
        "feature": "engineering workflow",
        "cli_command": "python -m sp63_core engineering-workflow "
        "--input-json <input.json> --output-dir <dir> --json",
        "doc_path": "docs/engineering_workflow_runner.md",
        "test_path": "tests/test_engineering_workflow.py",
        "safety_warnings": ("workflow output does not certify design",),
        "project_use_allowed": False,
    },
    {
        "feature": "batch workflow",
        "cli_command": "python -m sp63_core engineering-workflow-batch "
        "--input-dir <dir> --output-dir <dir> --json",
        "doc_path": "docs/engineering_workflow_batch.md",
        "test_path": "tests/test_engineering_workflow_batch.py",
        "safety_warnings": ("batch workflow requires engineer review",),
        "project_use_allowed": False,
    },
    {
        "feature": "static report index",
        "cli_command": "python -m sp63_core engineering-report-index --workflow-dir <dir> --json",
        "doc_path": "docs/static_report_index.md",
        "test_path": "tests/test_static_workflow_report_index.py",
        "safety_warnings": ("static index is navigation only",),
        "project_use_allowed": False,
    },
    {
        "feature": "evidence templates",
        "cli_command": "python -m sp63_core evidence-templates --output-dir <dir> --json",
        "doc_path": "docs/user_manual/evidence_templates.md",
        "test_path": "tests/test_evidence_templates.py",
        "safety_warnings": ("templates require engineer-filled data",),
        "project_use_allowed": False,
    },
    {
        "feature": "material verification closure",
        "cli_command": "python -m sp63_core material-verification-closure "
        "--material-verification-csv <csv> --output-dir <dir> --json",
        "doc_path": "docs/material_verification_closure.md",
        "test_path": "tests/test_material_verification_closure.py",
        "safety_warnings": ("material verification does not auto-update catalog",),
        "project_use_allowed": False,
    },
    {
        "feature": "release candidate",
        "cli_command": "python -m sp63_core release-candidate-report --output-dir <dir> --json",
        "doc_path": "docs/release_candidate_v0_9.md",
        "test_path": "tests/test_release_candidate_report.py",
        "safety_warnings": ("release candidate is not certification",),
        "project_use_allowed": False,
    },
    {
        "feature": "v09 final audit",
        "cli_command": "python -m sp63_core v09-final-audit --output-dir <dir> --json",
        "doc_path": "docs/v09_final_audit.md",
        "test_path": "tests/test_v09_final_audit.py",
        "safety_warnings": ("final audit does not approve project use",),
        "project_use_allowed": False,
    },
    {
        "feature": "protected files guard",
        "cli_command": "python -m sp63_core protected-files-check --json",
        "doc_path": "docs/protected_files_guard.md",
        "test_path": "tests/test_protected_files_guard.py",
        "safety_warnings": ("guard is not automatic merge approval",),
        "project_use_allowed": False,
    },
    {
        "feature": "ML advisory readiness",
        "cli_command": "python -m sp63_core engineering-ml-readiness --dataset <dataset> --json",
        "doc_path": "docs/engineering_ml_readiness.md",
        "test_path": "tests/test_engineering_ml_readiness_bundle.py",
        "safety_warnings": ("ML remains advisory-only",),
        "project_use_allowed": False,
    },
)


@dataclass(frozen=True)
class TraceabilityMatrixResult:
    """Traceability matrix result."""

    status: str
    matrix_status: str
    output_dir: str | None
    row_count: int
    rows: tuple[dict[str, Any], ...]
    generated_files: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_traceability_matrix(*, output_dir: Path | None = None) -> TraceabilityMatrixResult:
    """Build the v0.9 traceability matrix."""
    errors = _validate_rows(TRACEABILITY_ROWS)
    status = "fail" if errors else "pass"
    result = TraceabilityMatrixResult(
        status=status,
        matrix_status=status,
        output_dir=None,
        row_count=len(TRACEABILITY_ROWS),
        rows=TRACEABILITY_ROWS,
        generated_files=(),
        warnings=(TRACEABILITY_WARNING,),
        errors=errors,
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    if output_dir is not None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        json_path = output_path / "traceability_matrix.json"
        markdown_path = output_path / "traceability_matrix.md"
        json_path.write_text(
            json.dumps({"report_type": "traceability_matrix", **result.__dict__}, indent=2),
            encoding="utf-8",
        )
        markdown_path.write_text(render_traceability_matrix_markdown(result), encoding="utf-8")
        result = TraceabilityMatrixResult(
            **{
                **result.__dict__,
                "output_dir": str(output_path),
                "generated_files": (str(json_path), str(markdown_path)),
            }
        )
    return result


def render_traceability_matrix_markdown(result: TraceabilityMatrixResult) -> str:
    """Render the traceability matrix as Markdown."""
    lines = [
        "# Traceability Matrix",
        "",
        TRACEABILITY_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "| feature | CLI command | docs | tests | project use allowed |",
        "|---|---|---|---|---:|",
    ]
    for row in result.rows:
        lines.append(
            "| {feature} | `{cli}` | `{doc}` | `{test}` | `{allowed}` |".format(
                feature=row["feature"],
                cli=row["cli_command"],
                doc=row["doc_path"],
                test=row["test_path"],
                allowed=row["project_use_allowed"],
            )
        )
    return "\n".join(lines) + "\n"


def _validate_rows(rows: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    errors: list[str] = []
    seen: set[str] = set()
    for row in rows:
        feature = str(row.get("feature", "")).strip()
        if not feature:
            errors.append("traceability row missing feature")
        if feature in seen:
            errors.append(f"duplicate traceability feature: {feature}")
        seen.add(feature)
        for key in ("cli_command", "doc_path", "test_path", "safety_warnings"):
            if not row.get(key):
                errors.append(f"{feature} missing {key}")
        if row.get("project_use_allowed") is not False:
            errors.append(f"{feature} must not allow project use")
    return tuple(errors)
