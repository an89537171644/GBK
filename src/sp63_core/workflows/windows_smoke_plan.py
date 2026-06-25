"""Windows clean-machine smoke plan generator."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

WINDOWS_SMOKE_WARNING = (
    "Windows smoke plan is a manual clean-machine checklist. It does not build "
    "an executable, certify designs, or approve project use."
)

EXPECTED_COMMANDS: tuple[str, ...] = (
    "python --version",
    "python -m venv .venv",
    ".\\.venv\\Scripts\\python.exe -m pip install --upgrade pip",
    ".\\.venv\\Scripts\\python.exe -m pip install -e .",
    ".\\.venv\\Scripts\\python.exe -m sp63_core validate --golden",
    ".\\.venv\\Scripts\\python.exe -m sp63_core clean-demo-workflow "
    "--output-dir reports\\clean_demo_windows --json",
    ".\\.venv\\Scripts\\python.exe -m sp63_core protected-files-check --json",
    ".\\.venv\\Scripts\\python.exe -m sp63_core release-bundle "
    "--output-dir reports\\release_bundle_windows --version 0.9.0-rc1 --json",
)


@dataclass(frozen=True)
class WindowsSmokePlanResult:
    """Windows clean-machine smoke plan result."""

    status: str
    output_dir: str
    generated_files: tuple[str, ...]
    command_count: int
    expected_statuses: tuple[dict[str, str], ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False
    project_use_allowed: bool = False


def build_windows_smoke_plan(*, output_dir: Path) -> WindowsSmokePlanResult:
    """Build review-only Windows clean-machine smoke plan files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    plan_path = output_path / "WINDOWS_SMOKE_PLAN.md"
    ps1_path = output_path / "WINDOWS_COMMANDS.ps1"
    cmd_path = output_path / "WINDOWS_COMMANDS.cmd"
    manifest_path = output_path / "windows_smoke_manifest.json"
    readme_path = output_path / "README_WINDOWS_SMOKE.md"
    generated_files = (plan_path, ps1_path, cmd_path, manifest_path, readme_path)
    expected_statuses = (
        {"command": "validate --golden", "expected_status": "pass"},
        {"command": "clean-demo-workflow", "expected_status": "pass"},
        {"command": "protected-files-check", "expected_status": "pass"},
        {"command": "release-bundle", "expected_status": "pass"},
    )
    result = WindowsSmokePlanResult(
        status="pass",
        output_dir=str(output_path),
        generated_files=tuple(str(path) for path in generated_files),
        command_count=len(EXPECTED_COMMANDS),
        expected_statuses=expected_statuses,
        warnings=(WINDOWS_SMOKE_WARNING,),
        errors=(),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
        project_use_allowed=False,
    )

    plan_path.write_text(_render_plan(result), encoding="utf-8")
    ps1_path.write_text(_render_ps1(), encoding="utf-8")
    cmd_path.write_text(_render_cmd(), encoding="utf-8")
    manifest_path.write_text(
        json.dumps({"report_type": "windows_smoke_plan", **result.__dict__}, indent=2),
        encoding="utf-8",
    )
    readme_path.write_text(_render_readme(), encoding="utf-8")
    return result


def _render_plan(result: WindowsSmokePlanResult) -> str:
    lines = [
        "# Windows Clean-Machine Smoke Plan",
        "",
        WINDOWS_SMOKE_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "project_use_allowed = false",
        "",
        "## Manual Steps",
        "",
        "1. Start from a clean Windows machine or clean user profile.",
        "2. Install supported Python.",
        "3. Create a virtual environment.",
        "4. Install the package in editable or wheel form.",
        "5. Run the commands in `WINDOWS_COMMANDS.ps1` or `WINDOWS_COMMANDS.cmd`.",
        "6. Open generated `index.html` files manually if present.",
        "7. Confirm generated artifacts are not committed.",
        "",
        "## Commands",
        "",
        "```powershell",
        *EXPECTED_COMMANDS,
        "Start-Process reports\\clean_demo_windows\\index.html",
        "```",
        "",
        "## Expected Statuses",
        "",
        "| command | expected_status |",
        "|---|---|",
    ]
    for item in result.expected_statuses:
        lines.append(f"| {item['command']} | `{item['expected_status']}` |")
    return "\n".join(lines) + "\n"


def _render_ps1() -> str:
    lines = [
        "# Review-only Windows smoke commands. Run manually on a clean machine.",
        "$ErrorActionPreference = 'Stop'",
        *EXPECTED_COMMANDS,
        "if (Test-Path 'reports\\clean_demo_windows\\index.html') {",
        "  Start-Process 'reports\\clean_demo_windows\\index.html'",
        "}",
        "Write-Host 'Do not commit generated reports/*_windows artifacts.'",
    ]
    return "\n".join(lines) + "\n"


def _render_cmd() -> str:
    lines = [
        "@echo off",
        "REM Review-only Windows smoke commands. Run manually on a clean machine.",
        "python --version || exit /b 1",
        "python -m venv .venv || exit /b 1",
        ".\\.venv\\Scripts\\python.exe -m pip install --upgrade pip || exit /b 1",
        ".\\.venv\\Scripts\\python.exe -m pip install -e . || exit /b 1",
        ".\\.venv\\Scripts\\python.exe -m sp63_core validate --golden || exit /b 1",
        ".\\.venv\\Scripts\\python.exe -m sp63_core clean-demo-workflow "
        "--output-dir reports\\clean_demo_windows --json || exit /b 1",
        ".\\.venv\\Scripts\\python.exe -m sp63_core protected-files-check --json || exit /b 1",
        ".\\.venv\\Scripts\\python.exe -m sp63_core release-bundle "
        "--output-dir reports\\release_bundle_windows --version 0.9.0-rc1 --json || exit /b 1",
        "echo Do not commit generated reports/*_windows artifacts.",
    ]
    return "\n".join(lines) + "\n"


def _render_readme() -> str:
    return "\n".join(
        [
            "# README Windows Smoke",
            "",
            WINDOWS_SMOKE_WARNING,
            "",
            "Use this folder as a manual clean-machine checklist.",
            "The scripts are generated for reviewer convenience and are not run by tests.",
        ]
    ) + "\n"
