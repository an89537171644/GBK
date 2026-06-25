"""Lightweight JSON output contracts for user-facing workflow commands."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

JSON_OUTPUT_CONTRACT_WARNING = (
    "JSON output contracts are compatibility guidance only. They do not certify "
    "designs, approve project use, or make ML project-ready."
)

BOOLEAN_SAFETY_KEYS: tuple[str, ...] = (
    "requires_engineer_review",
    "ml_is_advisory_only",
    "deterministic_checks_required",
    "ml_ready_for_project_use",
)

JSON_OUTPUT_CONTRACTS: tuple[dict[str, Any], ...] = (
    {
        "command": "input-preflight",
        "required_keys": ("command", "status", "preflight_status", "issue_count"),
        "status_keys": ("status", "preflight_status"),
        "boolean_safety_keys": BOOLEAN_SAFETY_KEYS,
    },
    {
        "command": "engineering-workflow",
        "required_keys": ("command", "status", "workflow_status", "files_created"),
        "status_keys": ("status", "workflow_status"),
        "boolean_safety_keys": BOOLEAN_SAFETY_KEYS,
    },
    {
        "command": "engineering-workflow-batch",
        "required_keys": ("command", "status", "batch_status", "case_count"),
        "status_keys": ("status", "batch_status"),
        "boolean_safety_keys": BOOLEAN_SAFETY_KEYS,
    },
    {
        "command": "engineering-report-index",
        "required_keys": ("command", "status", "index_status", "linked_files"),
        "status_keys": ("status", "index_status"),
        "boolean_safety_keys": BOOLEAN_SAFETY_KEYS,
    },
    {
        "command": "input-form-schema",
        "required_keys": ("command", "status", "schema_status", "field_count"),
        "status_keys": ("status", "schema_status"),
        "boolean_safety_keys": BOOLEAN_SAFETY_KEYS,
    },
    {
        "command": "input-form-preview",
        "required_keys": ("command", "status", "preview_status", "generated_files"),
        "status_keys": ("status", "preview_status"),
        "boolean_safety_keys": BOOLEAN_SAFETY_KEYS,
    },
    {
        "command": "material-verification-closure",
        "required_keys": ("command", "status", "closure_status", "coverage_ratio"),
        "status_keys": ("status", "closure_status"),
        "boolean_safety_keys": BOOLEAN_SAFETY_KEYS,
    },
    {
        "command": "clean-demo-workflow",
        "required_keys": ("command", "status", "demo_status", "files_created"),
        "status_keys": ("status", "demo_status"),
        "boolean_safety_keys": BOOLEAN_SAFETY_KEYS,
    },
    {
        "command": "engineering-handoff-package",
        "required_keys": ("command", "status", "package_status", "file_count"),
        "status_keys": ("status", "package_status"),
        "boolean_safety_keys": BOOLEAN_SAFETY_KEYS,
    },
    {
        "command": "launcher-scripts",
        "required_keys": ("command", "status", "package_status", "script_count"),
        "status_keys": ("status", "package_status"),
        "boolean_safety_keys": BOOLEAN_SAFETY_KEYS,
    },
    {
        "command": "external-validation-evidence-package",
        "required_keys": ("command", "status", "evidence_status", "total_cases"),
        "status_keys": ("status", "evidence_status"),
        "boolean_safety_keys": BOOLEAN_SAFETY_KEYS,
    },
    {
        "command": "v09-final-audit",
        "required_keys": ("command", "status", "audit_status", "audit_count"),
        "status_keys": ("status", "audit_status"),
        "boolean_safety_keys": BOOLEAN_SAFETY_KEYS,
    },
    {
        "command": "release-notes",
        "required_keys": ("command", "status", "package_status", "version"),
        "status_keys": ("status", "package_status"),
        "boolean_safety_keys": BOOLEAN_SAFETY_KEYS,
    },
    {
        "command": "protected-files-check",
        "required_keys": ("command", "status", "guard_status", "changed_protected_files"),
        "status_keys": ("status", "guard_status"),
        "boolean_safety_keys": ("requires_engineer_review",),
    },
    {
        "command": "docs-audit",
        "required_keys": ("command", "status", "docs_audit_status", "missing_local_links"),
        "status_keys": ("status", "docs_audit_status"),
        "boolean_safety_keys": BOOLEAN_SAFETY_KEYS,
    },
    {
        "command": "user-acceptance-smoke",
        "required_keys": ("command", "status", "user_acceptance_status", "smoke_count"),
        "status_keys": ("status", "user_acceptance_status"),
        "boolean_safety_keys": BOOLEAN_SAFETY_KEYS,
    },
    {
        "command": "v09-readiness",
        "required_keys": ("command", "status", "readiness_status", "gate_count"),
        "status_keys": ("status", "readiness_status"),
        "boolean_safety_keys": BOOLEAN_SAFETY_KEYS,
    },
)


@dataclass(frozen=True)
class JsonOutputContractResult:
    """JSON output contract summary."""

    status: str
    contract_status: str
    output_dir: str | None
    contract_count: int
    contracts: tuple[dict[str, Any], ...]
    generated_files: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


@dataclass(frozen=True)
class JsonContractValidationResult:
    """Validation result for one payload against one lightweight contract."""

    status: str
    command: str
    missing_required_keys: tuple[str, ...]
    missing_safety_keys: tuple[str, ...]
    errors: tuple[str, ...]


def build_json_output_contract(
    *,
    output_dir: Path | None = None,
) -> JsonOutputContractResult:
    """Build lightweight JSON output contracts."""
    errors = _validate_contract_definitions(JSON_OUTPUT_CONTRACTS)
    status = "fail" if errors else "pass"
    result = JsonOutputContractResult(
        status=status,
        contract_status=status,
        output_dir=None,
        contract_count=len(JSON_OUTPUT_CONTRACTS),
        contracts=JSON_OUTPUT_CONTRACTS,
        generated_files=(),
        warnings=(JSON_OUTPUT_CONTRACT_WARNING,),
        errors=errors,
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    if output_dir is not None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        json_path = output_path / "json_output_contract.json"
        markdown_path = output_path / "json_output_contract.md"
        json_path.write_text(
            json.dumps(_payload(result), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        markdown_path.write_text(render_json_output_contract_markdown(result), encoding="utf-8")
        result = JsonOutputContractResult(
            **{
                **result.__dict__,
                "output_dir": str(output_path),
                "generated_files": (str(json_path), str(markdown_path)),
            }
        )
    return result


def validate_payload_against_json_contract(
    payload: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> JsonContractValidationResult:
    """Validate a payload against a lightweight JSON output contract."""
    required_keys = tuple(str(key) for key in contract.get("required_keys", ()))
    safety_keys = tuple(str(key) for key in contract.get("boolean_safety_keys", ()))
    missing_required = tuple(key for key in required_keys if key not in payload)
    missing_safety = tuple(key for key in safety_keys if key not in payload)
    errors = tuple(
        f"missing required key: {key}" for key in (*missing_required, *missing_safety)
    )
    status = "fail" if errors else "pass"
    return JsonContractValidationResult(
        status=status,
        command=str(contract.get("command", "")),
        missing_required_keys=missing_required,
        missing_safety_keys=missing_safety,
        errors=errors,
    )


def render_json_output_contract_markdown(result: JsonOutputContractResult) -> str:
    """Render JSON output contracts as Markdown."""
    lines = [
        "# JSON Output Contract",
        "",
        JSON_OUTPUT_CONTRACT_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Lightweight Contract Shape",
        "",
        "```json",
        "{",
        '  "command": "...",',
        '  "required_keys": [],',
        '  "status_keys": [],',
        '  "boolean_safety_keys": []',
        "}",
        "```",
        "",
        "## Contracts",
        "",
        "| command | required keys | status keys | safety keys |",
        "|---|---|---|---|",
    ]
    for contract in result.contracts:
        lines.append(
            "| `{command}` | {required} | {status_keys} | {safety} |".format(
                command=contract["command"],
                required=", ".join(f"`{key}`" for key in contract["required_keys"]),
                status_keys=", ".join(f"`{key}`" for key in contract["status_keys"]),
                safety=", ".join(f"`{key}`" for key in contract["boolean_safety_keys"]),
            )
        )
    return "\n".join(lines) + "\n"


def _validate_contract_definitions(contracts: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    errors: list[str] = []
    seen: set[str] = set()
    for contract in contracts:
        command = str(contract.get("command", "")).strip()
        if not command:
            errors.append("JSON output contract is missing command")
        if command in seen:
            errors.append(f"duplicate JSON output contract: {command}")
        seen.add(command)
        required_keys = set(contract.get("required_keys", ()))
        if "command" not in required_keys or "status" not in required_keys:
            errors.append(f"{command} contract must require command and status")
        if not contract.get("boolean_safety_keys"):
            errors.append(f"{command} contract must declare boolean safety keys")
    return tuple(errors)


def _payload(result: JsonOutputContractResult) -> dict[str, Any]:
    return {"report_type": "json_output_contract", **result.__dict__}
