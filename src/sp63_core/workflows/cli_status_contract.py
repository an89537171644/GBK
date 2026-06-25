"""CLI status and exit-code contract for engineering workflow commands."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CLI_STATUS_CONTRACT_WARNING = (
    "CLI status contract is automation guidance only. It does not approve "
    "project use, certify designs, or make ML project-ready."
)

STATUS_MAPPING: dict[str, str] = {
    "pass": "command completed and reported a passing review status",
    "review_required": "command completed but engineer review remains mandatory",
    "fail": "command completed and reported a blocking failure",
}

EXIT_CODE_MAPPING: dict[str, int] = {
    "pass": 0,
    "review_required": 0,
    "fail": 1,
}

COMMAND_CONTRACTS: tuple[dict[str, Any], ...] = (
    {
        "command": "validate",
        "status_field": "status",
        "review_required_allowed": False,
        "fail_is_nonzero": True,
        "ci_usable": True,
    },
    {
        "command": "materials-audit",
        "status_field": "status",
        "review_required_allowed": True,
        "fail_is_nonzero": True,
        "ci_usable": True,
    },
    {
        "command": "manual-cases",
        "status_field": "status",
        "review_required_allowed": False,
        "fail_is_nonzero": True,
        "ci_usable": True,
    },
    {
        "command": "external-validation",
        "status_field": "status",
        "review_required_allowed": True,
        "fail_is_nonzero": True,
        "ci_usable": True,
    },
    {
        "command": "input-preflight",
        "status_field": "status",
        "review_required_allowed": True,
        "fail_is_nonzero": True,
        "ci_usable": True,
    },
    {
        "command": "engineering-workflow",
        "status_field": "status",
        "review_required_allowed": True,
        "fail_is_nonzero": True,
        "ci_usable": True,
    },
    {
        "command": "engineering-workflow-batch",
        "status_field": "status",
        "review_required_allowed": True,
        "fail_is_nonzero": True,
        "ci_usable": True,
    },
    {
        "command": "protected-files-check",
        "status_field": "status",
        "review_required_allowed": True,
        "fail_is_nonzero": True,
        "ci_usable": True,
        "ci_blocker_note": "fail means protected calculation/material files changed",
    },
    {
        "command": "docs-audit",
        "status_field": "status",
        "review_required_allowed": True,
        "fail_is_nonzero": True,
        "ci_usable": True,
    },
    {
        "command": "release-candidate-report",
        "status_field": "status",
        "review_required_allowed": True,
        "fail_is_nonzero": True,
        "ci_usable": True,
    },
    {
        "command": "v09-readiness",
        "status_field": "status",
        "review_required_allowed": True,
        "fail_is_nonzero": True,
        "ci_usable": True,
    },
    {
        "command": "v09-final-audit",
        "status_field": "status",
        "review_required_allowed": True,
        "fail_is_nonzero": True,
        "ci_usable": True,
    },
    {
        "command": "clean-demo-workflow",
        "status_field": "status",
        "review_required_allowed": False,
        "fail_is_nonzero": True,
        "ci_usable": True,
    },
    {
        "command": "user-acceptance-smoke",
        "status_field": "status",
        "review_required_allowed": True,
        "fail_is_nonzero": True,
        "ci_usable": True,
    },
)


@dataclass(frozen=True)
class CliStatusContractResult:
    """CLI status and exit-code contract result."""

    status: str
    contract_status: str
    output_dir: str | None
    command_count: int
    status_mapping: dict[str, str]
    exit_code_mapping: dict[str, int]
    command_contracts: tuple[dict[str, Any], ...]
    generated_files: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_cli_status_contract(
    *,
    output_dir: Path | None = None,
) -> CliStatusContractResult:
    """Build the CLI status and exit-code contract."""
    errors = _validate_contracts(COMMAND_CONTRACTS)
    status = "fail" if errors else "pass"
    generated_files: tuple[str, ...] = ()
    output_dir_text: str | None = None
    result = CliStatusContractResult(
        status=status,
        contract_status=status,
        output_dir=None,
        command_count=len(COMMAND_CONTRACTS),
        status_mapping=STATUS_MAPPING,
        exit_code_mapping=EXIT_CODE_MAPPING,
        command_contracts=COMMAND_CONTRACTS,
        generated_files=generated_files,
        warnings=(CLI_STATUS_CONTRACT_WARNING,),
        errors=errors,
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    if output_dir is not None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        json_path = output_path / "cli_status_contract.json"
        markdown_path = output_path / "cli_status_contract.md"
        json_path.write_text(
            json.dumps(_payload(result), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        markdown_path.write_text(render_cli_status_contract_markdown(result), encoding="utf-8")
        generated_files = (str(json_path), str(markdown_path))
        output_dir_text = str(output_path)
        result = CliStatusContractResult(
            **{
                **result.__dict__,
                "output_dir": output_dir_text,
                "generated_files": generated_files,
            }
        )
    return result


def render_cli_status_contract_markdown(result: CliStatusContractResult) -> str:
    """Render the CLI status contract as Markdown."""
    lines = [
        "# CLI Status And Exit-Code Contract",
        "",
        CLI_STATUS_CONTRACT_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Status Mapping",
        "",
        "| status | meaning | exit_code |",
        "|---|---|---:|",
    ]
    for status, meaning in result.status_mapping.items():
        lines.append(f"| `{status}` | {meaning} | `{result.exit_code_mapping[status]}` |")
    lines.extend(
        [
            "",
            "## Technical Errors",
            "",
            "Invalid CLI usage and uncaught technical errors keep standard argparse or "
            "Python nonzero behavior.",
            "",
            "## Command Contracts",
            "",
            "| command | status field | review_required allowed | fail nonzero | CI usable |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for contract in result.command_contracts:
        lines.append(
            "| `{command}` | `{status_field}` | `{review}` | `{fail}` | `{ci}` |".format(
                command=contract["command"],
                status_field=contract["status_field"],
                review=contract["review_required_allowed"],
                fail=contract["fail_is_nonzero"],
                ci=contract["ci_usable"],
            )
        )
    lines.extend(
        [
            "",
            "## CI Blockers",
            "",
            "- `protected-files-check` status `fail` is a CI blocker.",
            "- Calculation formula files and material catalogs must not be changed in "
            "workflow/productization steps.",
        ]
    )
    return "\n".join(lines) + "\n"


def _validate_contracts(contracts: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    errors: list[str] = []
    seen: set[str] = set()
    for contract in contracts:
        command = str(contract.get("command", "")).strip()
        if not command:
            errors.append("command contract is missing command")
        if command in seen:
            errors.append(f"duplicate command contract: {command}")
        seen.add(command)
        if contract.get("status_field") != "status":
            errors.append(f"{command} must expose top-level status")
        if contract.get("fail_is_nonzero") is not True:
            errors.append(f"{command} must document fail as nonzero")
    return tuple(errors)


def _payload(result: CliStatusContractResult) -> dict[str, Any]:
    return {"report_type": "cli_status_contract", **result.__dict__}
