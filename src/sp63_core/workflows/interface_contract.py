"""Interface contract for a future engineering GUI or desktop wrapper."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

WORKFLOW_NAMES = (
    "deterministic_design_workflow",
    "workflow_self_check",
    "engineering_ml_readiness",
    "optional_neural_advisory_review",
    "report_archive_review",
    "material_verification_review",
    "external_validation_review",
)

REQUIRED_SCREENS = (
    "Start / Project Safety Notice",
    "Input JSON Selection",
    "Deterministic Design Report",
    "Archive Validation and ZIP",
    "Engineering ML Readiness",
    "Material Verification",
    "External Validation",
    "Neural Advisory Review",
    "Generated Files",
    "Engineer Acceptance Checklist",
)

REQUIRED_INPUTS = (
    "input_json_path",
    "output_dir",
    "dataset_path",
    "external_validation_csv",
    "material_verification_csv",
    "include_ml_readiness",
    "create_zip",
    "engineer_name",
    "review_date",
    "source_note",
)

REQUIRED_OUTPUTS = (
    "deterministic_report/report.md",
    "deterministic_report/report.json",
    "deterministic_report/report.html",
    "deterministic_report/manifest.json",
    "deterministic_report.zip",
    "workflow_summary.json",
    "workflow_summary.md",
    "README_WORKFLOW.md",
    "engineering_ml_readiness.json",
    "engineering_ml_readiness.md",
    "engineering_ml_readiness_matrix.csv",
)

MANDATORY_WARNINGS = (
    "This software does not certify design decisions.",
    "Deterministic SP63 verification is mandatory.",
    "Engineer review is mandatory.",
    "ML output is advisory-only.",
    "ML is not a design checker.",
    "ml_ready_for_project_use must remain false.",
    "Synthetic benchmarks are not external validation.",
    "Material verification does not certify the design automatically.",
    "ZIP/manifest do not certify the design.",
)

FORBIDDEN_UI_ACTIONS = (
    "hide deterministic SP63 result",
    "present ML result as final design decision",
    "allow project approval based only on ML",
    "allow ml_ready_for_project_use = true",
    "silence engineer-review warnings",
    "modify material catalog automatically",
    "replace deterministic report with neural prediction",
    "skip archive validation",
    "skip manifest/ZIP integrity checks",
)

RECOMMENDED_CLI_COMMANDS = (
    "python -m sp63_core engineering-workflow "
    "--input-json <input.json> --output-dir <output-dir> --json",
    "python -m sp63_core engineering-workflow-self-check --output-dir <output-dir> --json",
    "python -m sp63_core report-archive-validate --path <report-dir> --json",
    "python -m sp63_core report-archive-zip --path <report-dir> --output <report.zip> --json",
    "python -m sp63_core materials-audit --verification-csv <materials.csv> --json",
    "python -m sp63_core external-validation --csv <external-validation.csv> --strict --json",
    "python -m sp63_core neural-safety-audit --json",
)

CONTRACT_WARNING = (
    "This document is a UI/desktop wrapper contract only. It does not implement "
    "a user interface and does not approve ML for project use."
)


@dataclass(frozen=True)
class EngineeringInterfaceContractResult:
    """Machine-readable contract for future engineering UI wrappers."""

    status: str
    contract_status: str
    output_dir: str | None
    workflow_names: tuple[str, ...]
    required_screens: tuple[str, ...]
    required_inputs: tuple[str, ...]
    required_outputs: tuple[str, ...]
    mandatory_warnings: tuple[str, ...]
    forbidden_ui_actions: tuple[str, ...]
    recommended_cli_commands: tuple[str, ...]
    json_data: dict[str, Any]
    markdown: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_engineering_interface_contract(
    *,
    output_dir: Path | None = None,
) -> EngineeringInterfaceContractResult:
    """Build the GUI/desktop wrapper contract and optionally write it to disk."""
    json_data: dict[str, Any] = {
        "contract_type": "engineering_gui_wrapper_contract",
        "status": "pass",
        "workflows": list(WORKFLOW_NAMES),
        "required_screens": list(REQUIRED_SCREENS),
        "required_inputs": list(REQUIRED_INPUTS),
        "required_outputs": list(REQUIRED_OUTPUTS),
        "mandatory_warnings": list(MANDATORY_WARNINGS),
        "forbidden_ui_actions": list(FORBIDDEN_UI_ACTIONS),
        "recommended_cli_commands": list(RECOMMENDED_CLI_COMMANDS),
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "ml_ready_for_project_use": False,
    }
    markdown = render_engineering_interface_contract_markdown(json_data)
    result = EngineeringInterfaceContractResult(
        status="pass",
        contract_status="pass",
        output_dir=str(output_dir) if output_dir is not None else None,
        workflow_names=WORKFLOW_NAMES,
        required_screens=REQUIRED_SCREENS,
        required_inputs=REQUIRED_INPUTS,
        required_outputs=REQUIRED_OUTPUTS,
        mandatory_warnings=MANDATORY_WARNINGS,
        forbidden_ui_actions=FORBIDDEN_UI_ACTIONS,
        recommended_cli_commands=RECOMMENDED_CLI_COMMANDS,
        json_data=json_data,
        markdown=markdown,
        warnings=(CONTRACT_WARNING,),
        errors=(),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    if output_dir is not None:
        _write_contract_files(Path(output_dir), result)
    return result


def render_engineering_interface_contract_markdown(json_data: dict[str, Any]) -> str:
    """Render the interface contract as Markdown."""
    lines = [
        "# Engineering GUI/Desktop Wrapper Contract",
        "",
        CONTRACT_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Supported Workflows",
        "",
        *_bullet_lines(tuple(json_data["workflows"])),
        "",
        "## Required Screens",
        "",
        *_bullet_lines(tuple(json_data["required_screens"])),
        "",
        "## Required Inputs",
        "",
        *_bullet_lines(tuple(json_data["required_inputs"])),
        "",
        "## Required Outputs",
        "",
        *_bullet_lines(tuple(json_data["required_outputs"])),
        "",
        "## Mandatory Warnings",
        "",
        *_bullet_lines(tuple(json_data["mandatory_warnings"])),
        "",
        "## Forbidden UI Actions",
        "",
        *_bullet_lines(tuple(json_data["forbidden_ui_actions"])),
        "",
        "## Recommended CLI Commands",
        "",
        *_bullet_lines(tuple(json_data["recommended_cli_commands"])),
        "",
        "## Acceptance Criteria",
        "",
        "- The UI clearly shows deterministic SP63 status.",
        "- The UI never shows ML output as a project decision.",
        "- The UI always displays engineer-review warnings.",
        "- The UI shows `ml_ready_for_project_use = false`.",
        "- The UI exposes generated report, manifest, ZIP, and workflow files.",
        "- The UI does not modify material catalog values automatically.",
        "- The UI does not hide failed or review-required statuses.",
        "",
        "## Limitations",
        "",
        "- This contract does not implement UI.",
        "- This contract does not certify any calculation.",
        "- This contract does not approve ML for project use.",
        "- Deterministic SP63 checks remain mandatory.",
        "- Engineer review remains mandatory.",
    ]
    return "\n".join(lines) + "\n"


def _write_contract_files(output_dir: Path, result: EngineeringInterfaceContractResult) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_payload = dict(result.json_data)
    json_path = output_dir / "engineering_interface_contract.json"
    markdown_path = output_dir / "engineering_interface_contract.md"
    json_path.write_text(
        json.dumps(json_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(result.markdown, encoding="utf-8")


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]
