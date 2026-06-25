"""Generate lightweight launcher scripts for engineering review workflows."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

LAUNCHER_SCRIPTS_WARNING = (
    "Launcher scripts are command wrappers only. They do not perform calculations "
    "outside sp63_core, start servers, implement UI, or approve project use."
)


@dataclass(frozen=True)
class LauncherScriptsPackageResult:
    """Result of creating launcher scripts for review workflows."""

    status: str
    package_status: str
    output_dir: str
    generated_files: tuple[str, ...]
    manifest_path: str
    readme_path: str
    script_count: int
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_launcher_scripts_package(*, output_dir: Path) -> LauncherScriptsPackageResult:
    """Create portable launcher scripts that call existing CLI commands."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    generated_files: list[Path] = []
    warnings = [LAUNCHER_SCRIPTS_WARNING]
    errors: list[str] = []

    scripts = _script_specs()
    for filename, content in scripts.items():
        path = output_path / filename
        path.write_text(content, encoding="utf-8", newline="\n")
        generated_files.append(path)

    readme_path = output_path / "README_LAUNCHER_SCRIPTS.md"
    manifest_path = output_path / "launcher_scripts_manifest.json"
    readme_path.write_text(_render_readme(tuple(scripts)), encoding="utf-8")
    generated_files.append(readme_path)

    manifest = _build_manifest(
        output_dir=output_path,
        generated_files=tuple(generated_files),
        status="pass",
        warnings=tuple(warnings),
        errors=tuple(errors),
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    generated_files.append(manifest_path)

    return LauncherScriptsPackageResult(
        status="pass",
        package_status="pass",
        output_dir=str(output_path),
        generated_files=tuple(str(path) for path in generated_files),
        manifest_path=str(manifest_path),
        readme_path=str(readme_path),
        script_count=len(scripts),
        warnings=tuple(warnings),
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )


def _script_specs() -> dict[str, str]:
    return {
        "run_clean_demo_workflow.cmd": _cmd_script(
            "python -m sp63_core clean-demo-workflow "
            "--output-dir reports\\clean_demo_workflow --json"
        ),
        "run_clean_demo_workflow.sh": _sh_script(
            "python -m sp63_core clean-demo-workflow "
            "--output-dir reports/clean_demo_workflow --json"
        ),
        "run_engineering_workflow.cmd": _cmd_script(
            "python -m sp63_core engineering-workflow "
            "--input-json input\\rectangular_input.json "
            "--output-dir reports\\engineering_workflow --with-preflight --with-index --json"
        ),
        "run_engineering_workflow.sh": _sh_script(
            "python -m sp63_core engineering-workflow "
            "--input-json input/rectangular_input.json "
            "--output-dir reports/engineering_workflow --with-preflight --with-index --json"
        ),
        "run_engineering_workflow_batch.cmd": _cmd_script(
            "python -m sp63_core engineering-workflow-batch "
            "--input-dir input --output-dir reports\\engineering_workflow_batch "
            "--with-preflight --with-index --json"
        ),
        "run_engineering_workflow_batch.sh": _sh_script(
            "python -m sp63_core engineering-workflow-batch "
            "--input-dir input --output-dir reports/engineering_workflow_batch "
            "--with-preflight --with-index --json"
        ),
        "open_clean_demo_index.cmd": _cmd_script(
            "start \"\" reports\\clean_demo_workflow\\index.html"
        ),
        "open_clean_demo_index.sh": _sh_script(
            "if command -v xdg-open >/dev/null 2>&1; then "
            "xdg-open reports/clean_demo_workflow/index.html; else "
            "echo reports/clean_demo_workflow/index.html; fi"
        ),
    }


def _cmd_script(command: str) -> str:
    return "\n".join(
        [
            "@echo off",
            "rem sp63_core engineering review launcher.",
            "rem Deterministic checks and engineer review remain mandatory.",
            command,
            "exit /b %ERRORLEVEL%",
            "",
        ]
    )


def _sh_script(command: str) -> str:
    return "\n".join(
        [
            "#!/usr/bin/env sh",
            "set -eu",
            "# sp63_core engineering review launcher.",
            "# Deterministic checks and engineer review remain mandatory.",
            command,
            "",
        ]
    )


def _build_manifest(
    *,
    output_dir: Path,
    generated_files: tuple[Path, ...],
    status: str,
    warnings: tuple[str, ...],
    errors: tuple[str, ...],
) -> dict[str, object]:
    return {
        "report_type": "launcher_scripts_manifest",
        "status": status,
        "package_status": status,
        "output_dir": str(output_dir),
        "files": [
            {
                "path": str(path),
                "relative_path": path.relative_to(output_dir).as_posix(),
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            }
            for path in generated_files
            if path.exists()
        ],
        "warnings": list(warnings),
        "errors": list(errors),
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "ml_ready_for_project_use": False,
    }


def _render_readme(script_names: tuple[str, ...]) -> str:
    lines = [
        "# Launcher Scripts Package",
        "",
        LAUNCHER_SCRIPTS_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Scripts",
        "",
        *(f"- `{name}`" for name in script_names),
        "",
        "## Limits",
        "",
        "- Scripts call existing CLI commands only.",
        "- Scripts do not contain calculation formulas.",
        "- Scripts do not start a web server.",
        "- Scripts do not add Streamlit, Gradio, FastAPI, Flask, Electron, PyQt, or Tkinter.",
        "- Generated reports must still be reviewed by an engineer.",
    ]
    return "\n".join(lines) + "\n"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
