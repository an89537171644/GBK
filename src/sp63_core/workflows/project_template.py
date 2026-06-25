"""Create a portable project template package for engineering review."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

PROJECT_TEMPLATE_WARNING = (
    "Project template package is a handoff scaffold only. It does not certify "
    "designs, update material values, or make ML project-ready."
)

INPUT_TEMPLATE_SOURCE = Path("docs/reports/examples/rectangular_design_input_example.json")
EXTERNAL_TEMPLATE_SOURCE = Path(
    "docs/validation/templates/external_validation_engineer_input_template.csv"
)
MATERIAL_TEMPLATE_SOURCE = Path(
    "docs/materials/templates/material_catalog_verification_template.csv"
)


@dataclass(frozen=True)
class ProjectTemplatePackageResult:
    """Result of creating a project template package."""

    status: str
    package_status: str
    output_dir: str
    generated_files: tuple[str, ...]
    input_json_path: str
    external_validation_template_path: str
    material_verification_template_path: str
    readme_path: str
    run_commands_path: str
    acceptance_checklist_path: str
    manifest_path: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_project_template_package(*, output_dir: Path) -> ProjectTemplatePackageResult:
    """Create a reusable project handoff folder with input and evidence templates."""
    output_path = Path(output_dir)
    input_dir = output_path / "input"
    evidence_dir = output_path / "evidence"
    input_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    input_json_path = input_dir / "rectangular_input.json"
    external_template_path = evidence_dir / "external_validation_template.csv"
    material_template_path = evidence_dir / "material_verification_template.csv"
    readme_path = output_path / "README_PROJECT_TEMPLATE.md"
    run_commands_path = output_path / "RUN_COMMANDS.md"
    acceptance_checklist_path = output_path / "acceptance_checklist.md"
    manifest_path = output_path / "project_template_manifest.json"

    warnings: list[str] = [PROJECT_TEMPLATE_WARNING]
    errors: list[str] = []
    generated_files: list[Path] = []

    for source, target in (
        (INPUT_TEMPLATE_SOURCE, input_json_path),
        (EXTERNAL_TEMPLATE_SOURCE, external_template_path),
        (MATERIAL_TEMPLATE_SOURCE, material_template_path),
    ):
        if not source.exists():
            errors.append(f"template source missing: {source}")
            continue
        shutil.copyfile(source, target)
        generated_files.append(target)

    readme_path.write_text(_render_project_template_readme(), encoding="utf-8")
    run_commands_path.write_text(_render_run_commands(), encoding="utf-8")
    acceptance_checklist_path.write_text(_render_acceptance_checklist(), encoding="utf-8")
    generated_files.extend([readme_path, run_commands_path, acceptance_checklist_path])

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

    return ProjectTemplatePackageResult(
        status=status,
        package_status=status,
        output_dir=str(output_path),
        generated_files=tuple(str(path) for path in generated_files),
        input_json_path=str(input_json_path),
        external_validation_template_path=str(external_template_path),
        material_verification_template_path=str(material_template_path),
        readme_path=str(readme_path),
        run_commands_path=str(run_commands_path),
        acceptance_checklist_path=str(acceptance_checklist_path),
        manifest_path=str(manifest_path),
        warnings=tuple(warnings),
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
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
        "report_type": "project_template_manifest",
        "status": status,
        "package_status": status,
        "output_dir": str(output_dir),
        "files": [
            {
                "path": str(path),
                "relative_path": path.relative_to(output_dir).as_posix(),
                "sha256": _sha256(path),
            }
            for path in generated_files
            if path.exists()
        ],
        "source_templates": {
            "input_json": str(INPUT_TEMPLATE_SOURCE),
            "external_validation": str(EXTERNAL_TEMPLATE_SOURCE),
            "material_verification": str(MATERIAL_TEMPLATE_SOURCE),
        },
        "warnings": list(warnings),
        "errors": list(errors),
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "ml_ready_for_project_use": False,
    }


def _render_project_template_readme() -> str:
    lines = [
        "# Project Template Package",
        "",
        PROJECT_TEMPLATE_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Contents",
        "",
        "- `input/rectangular_input.json`: editable deterministic workflow input.",
        "- `evidence/external_validation_template.csv`: blank external validation input.",
        "- `evidence/material_verification_template.csv`: blank material verification input.",
        "- `RUN_COMMANDS.md`: recommended commands for deterministic review.",
        "- `acceptance_checklist.md`: engineer review checklist.",
        "- `project_template_manifest.json`: SHA256 checksums for this package.",
        "",
        "## Limits",
        "",
        "- The package does not include full SP 63 text.",
        "- The package does not include personal, grant, private, SCAD, or LIRA files.",
        "- Material verification and external validation must be completed by an engineer.",
        "- ML output, if used later, remains advisory-only and must be verified by "
        "deterministic checks.",
    ]
    return "\n".join(lines) + "\n"


def _render_run_commands() -> str:
    lines = [
        "# Run Commands",
        "",
        "Run deterministic workflow:",
        "",
        "```bash",
        "python -m sp63_core engineering-workflow \\",
        "  --input-json input/rectangular_input.json \\",
        "  --output-dir reports/engineering_workflow \\",
        "  --with-preflight \\",
        "  --with-index \\",
        "  --json",
        "```",
        "",
        "Run external validation after an engineer fills the CSV:",
        "",
        "```bash",
        "python -m sp63_core external-validation \\",
        "  --csv evidence/external_validation_template.csv \\",
        "  --strict \\",
        "  --json",
        "```",
        "",
        "Run material audit and review template:",
        "",
        "```bash",
        "python -m sp63_core materials-audit --json",
        "python -m sp63_core materials-audit --verification-template",
        "```",
        "",
        "Safety smoke commands:",
        "",
        "```bash",
        "python -m sp63_core validate --golden",
        "python -m sp63_core manual-cases --json",
        "python -m sp63_core ml-proposal-verify --json",
        "```",
    ]
    return "\n".join(lines) + "\n"


def _render_acceptance_checklist() -> str:
    lines = [
        "# Acceptance Checklist",
        "",
        "- [ ] Deterministic workflow completed without failed status.",
        "- [ ] `input_preflight_report` was reviewed.",
        "- [ ] `report.md`, `report.json`, and `report.html` were reviewed.",
        "- [ ] External validation CSV was filled by an engineer.",
        "- [ ] External validation strict mode was reviewed.",
        "- [ ] Material verification was completed by an engineer.",
        "- [ ] No full SP 63 text was added to project files.",
        "- [ ] No personal, grant, private, SCAD, or LIRA files were added.",
        "- [ ] ML outputs, if any, were treated as advisory-only.",
        "- [ ] Deterministic SP63 checks remained mandatory.",
        "- [ ] Engineer review remains mandatory.",
    ]
    return "\n".join(lines) + "\n"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
