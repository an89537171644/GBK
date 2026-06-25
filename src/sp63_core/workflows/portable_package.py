"""Portable Windows package skeleton without binary/exe packaging."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

PORTABLE_PACKAGE_WARNING = (
    "Portable package skeleton is a review convenience only. It does not build an "
    "exe, certify designs, approve project use, or make ML project-ready."
)

BASE_INPUT_SOURCE = Path("docs/reports/examples/rectangular_design_input_example.json")
EXTERNAL_TEMPLATE_SOURCE = Path(
    "docs/validation/templates/external_validation_engineer_input_template.csv"
)
MATERIAL_TEMPLATE_SOURCE = Path(
    "docs/materials/templates/material_catalog_verification_template.csv"
)
QUICKSTART_SOURCE = Path("docs/user_manual/quickstart.md")
CHECKLIST_SOURCE = Path("docs/user_manual/acceptance_checklist.md")


@dataclass(frozen=True)
class PortablePackageResult:
    """Portable package skeleton result."""

    status: str
    package_status: str
    output_dir: str
    generated_files: tuple[str, ...]
    manifest_path: str
    readme_path: str
    install_windows_path: str
    script_count: int
    file_count: int
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_portable_package(*, output_dir: Path) -> PortablePackageResult:
    """Create a portable Windows-oriented package skeleton without binaries."""
    output_path = Path(output_dir)
    input_dir = output_path / "input"
    evidence_dir = output_path / "evidence"
    docs_dir = output_path / "docs"
    for directory in (input_dir, evidence_dir, docs_dir):
        directory.mkdir(parents=True, exist_ok=True)

    warnings = [PORTABLE_PACKAGE_WARNING]
    errors: list[str] = []
    generated_files: list[Path] = []

    copy_specs = (
        (BASE_INPUT_SOURCE, input_dir / "rectangular_input.json"),
        (EXTERNAL_TEMPLATE_SOURCE, evidence_dir / "external_validation_template.csv"),
        (MATERIAL_TEMPLATE_SOURCE, evidence_dir / "material_verification_template.csv"),
        (QUICKSTART_SOURCE, docs_dir / "quickstart.md"),
        (CHECKLIST_SOURCE, docs_dir / "acceptance_checklist.md"),
    )
    for source, target in copy_specs:
        _copy_required_file(
            source=source,
            target=target,
            generated_files=generated_files,
            errors=errors,
        )

    script_specs = _script_specs()
    for filename, content in script_specs.items():
        path = output_path / filename
        path.write_text(content, encoding="utf-8", newline="\n")
        generated_files.append(path)

    readme_path = output_path / "README_PORTABLE_PACKAGE.md"
    install_path = output_path / "INSTALL_WINDOWS.md"
    manifest_path = output_path / "portable_manifest.json"
    readme_path.write_text(_render_readme(), encoding="utf-8")
    install_path.write_text(_render_install_windows(), encoding="utf-8")
    generated_files.extend([readme_path, install_path])

    status = "fail" if errors else "pass"
    manifest = _build_manifest(
        output_dir=output_path,
        generated_files=tuple(generated_files),
        status=status,
        warnings=tuple(warnings),
        errors=tuple(errors),
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    generated_files.append(manifest_path)

    return PortablePackageResult(
        status=status,
        package_status=status,
        output_dir=str(output_path),
        generated_files=tuple(str(path) for path in generated_files),
        manifest_path=str(manifest_path),
        readme_path=str(readme_path),
        install_windows_path=str(install_path),
        script_count=len(script_specs),
        file_count=len(generated_files),
        warnings=tuple(warnings),
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )


def _script_specs() -> dict[str, str]:
    return {
        "RUN_CLEAN_DEMO.cmd": _cmd_script(
            "python -m sp63_core clean-demo-workflow "
            "--output-dir reports\\clean_demo_workflow --json"
        ),
        "RUN_PREFLIGHT.cmd": _cmd_script(
            "python -m sp63_core input-preflight "
            "--input-json input\\rectangular_input.json "
            "--output-dir reports\\input_preflight --json"
        ),
        "RUN_WORKFLOW.cmd": _cmd_script(
            "python -m sp63_core engineering-workflow "
            "--input-json input\\rectangular_input.json "
            "--output-dir reports\\engineering_workflow "
            "--with-preflight --with-index --json"
        ),
        "OPEN_REPORT_INDEX.cmd": _cmd_script(
            "start \"\" reports\\engineering_workflow\\index.html"
        ),
    }


def _cmd_script(command: str) -> str:
    return "\n".join(
        [
            "@echo off",
            "rem sp63_core portable review command.",
            "rem Deterministic SP63 checks and engineer review remain mandatory.",
            command,
            "exit /b %ERRORLEVEL%",
            "",
        ]
    )


def _copy_required_file(
    *,
    source: Path,
    target: Path,
    generated_files: list[Path],
    errors: list[str],
) -> None:
    if not source.exists():
        errors.append(f"portable package source missing: {source}")
        return
    shutil.copyfile(source, target)
    generated_files.append(target)


def _build_manifest(
    *,
    output_dir: Path,
    generated_files: tuple[Path, ...],
    status: str,
    warnings: tuple[str, ...],
    errors: tuple[str, ...],
) -> dict[str, object]:
    return {
        "report_type": "portable_package_manifest",
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


def _render_readme() -> str:
    return "\n".join(
        [
            "# Portable Package Skeleton",
            "",
            PORTABLE_PACKAGE_WARNING,
            "",
            "requires_engineer_review = true",
            "ml_is_advisory_only = true",
            "deterministic_checks_required = true",
            "ml_ready_for_project_use = false",
            "",
            "## Contents",
            "",
            "- `INSTALL_WINDOWS.md` - local Python setup notes.",
            "- `RUN_CLEAN_DEMO.cmd` - run the deterministic clean demo.",
            "- `RUN_PREFLIGHT.cmd` - validate `input/rectangular_input.json`.",
            "- `RUN_WORKFLOW.cmd` - run deterministic workflow with preflight and index.",
            "- `OPEN_REPORT_INDEX.cmd` - open generated `index.html` after workflow run.",
            "- `input/rectangular_input.json` - editable input JSON example.",
            "- `evidence/external_validation_template.csv` - engineer-filled external "
            "validation template.",
            "- `evidence/material_verification_template.csv` - engineer-filled material "
            "verification template.",
            "- `docs/quickstart.md` and `docs/acceptance_checklist.md` - review docs.",
            "- `portable_manifest.json` - SHA256 checksums for skeleton files.",
            "",
            "## Limits",
            "",
            "- No exe, PyInstaller bundle, binary, GUI, web server, or JavaScript "
            "calculation is generated.",
            "- Generated reports are not part of this skeleton and must not be committed.",
            "- Deterministic SP63 checks and engineer review remain mandatory.",
        ]
    ) + "\n"


def _render_install_windows() -> str:
    return "\n".join(
        [
            "# Install On Windows",
            "",
            "1. Install a supported Python version.",
            "2. Install the project package in the selected environment.",
            "3. Run `RUN_CLEAN_DEMO.cmd`.",
            "4. Run `RUN_PREFLIGHT.cmd` after editing `input/rectangular_input.json`.",
            "5. Run `RUN_WORKFLOW.cmd`.",
            "6. Open `reports/engineering_workflow/index.html`.",
            "7. Review warnings, manifests, ZIP validation, material verification, "
            "and external validation.",
            "",
            "This package does not certify designs and does not approve project use.",
        ]
    ) + "\n"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
