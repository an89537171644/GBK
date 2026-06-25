"""Engineering handoff package for v0.9 review."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from sp63_core.workflows.static_input_form_preview import build_static_input_form_preview

HANDOFF_PACKAGE_WARNING = (
    "Engineering handoff package is a review scaffold only. It does not certify "
    "designs, update materials, or make ML project-ready."
)

BASE_INPUT_SOURCE = Path("docs/reports/examples/rectangular_design_input_example.json")
CLEAN_DEMO_INPUT_SOURCE = Path(
    "docs/reports/examples/clean_demo/rectangular_clean_demo_input.json"
)
EXTERNAL_TEMPLATE_SOURCE = Path(
    "docs/validation/templates/external_validation_engineer_input_template.csv"
)
MATERIAL_TEMPLATE_SOURCE = Path(
    "docs/materials/templates/material_catalog_verification_template.csv"
)
QUICKSTART_SOURCE = Path("docs/user_manual/quickstart.md")
CHECKLIST_SOURCE = Path("docs/user_manual/acceptance_checklist.md")
CLEAN_DEMO_DOC_SOURCE = Path("docs/clean_demo_workflow.md")


@dataclass(frozen=True)
class EngineeringHandoffPackageResult:
    """Result of creating the v0.9 engineering handoff package."""

    status: str
    package_status: str
    output_dir: str
    generated_files: tuple[str, ...]
    manifest_path: str
    readme_path: str
    run_commands_path: str
    input_json_path: str
    clean_demo_input_path: str
    external_validation_template_path: str
    material_verification_template_path: str
    preview_path: str | None
    file_count: int
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_engineering_handoff_package(
    *,
    output_dir: Path,
) -> EngineeringHandoffPackageResult:
    """Create a portable engineering handoff package without running calculations."""
    output_path = Path(output_dir)
    input_dir = output_path / "input"
    demo_dir = output_path / "demo"
    evidence_dir = output_path / "evidence"
    docs_dir = output_path / "docs"
    preview_dir = output_path / "previews"
    for directory in (input_dir, demo_dir, evidence_dir, docs_dir, preview_dir):
        directory.mkdir(parents=True, exist_ok=True)

    generated_files: list[Path] = []
    warnings: list[str] = [HANDOFF_PACKAGE_WARNING]
    errors: list[str] = []

    input_json_path = input_dir / "rectangular_input.json"
    clean_demo_input_path = demo_dir / "rectangular_clean_demo_input.json"
    external_template_path = evidence_dir / "external_validation_template.csv"
    material_template_path = evidence_dir / "material_verification_template.csv"
    quickstart_path = docs_dir / "quickstart.md"
    checklist_path = docs_dir / "acceptance_checklist.md"
    clean_demo_doc_path = docs_dir / "clean_demo_workflow.md"
    readme_path = output_path / "README_ENGINEERING_HANDOFF_PACKAGE.md"
    run_commands_path = output_path / "RUN_COMMANDS.md"
    manifest_path = output_path / "engineering_handoff_manifest.json"

    for source, target in (
        (BASE_INPUT_SOURCE, input_json_path),
        (CLEAN_DEMO_INPUT_SOURCE, clean_demo_input_path),
        (EXTERNAL_TEMPLATE_SOURCE, external_template_path),
        (MATERIAL_TEMPLATE_SOURCE, material_template_path),
        (QUICKSTART_SOURCE, quickstart_path),
        (CHECKLIST_SOURCE, checklist_path),
        (CLEAN_DEMO_DOC_SOURCE, clean_demo_doc_path),
    ):
        _copy_required_file(
            source=source,
            target=target,
            generated_files=generated_files,
            errors=errors,
        )

    preview = build_static_input_form_preview(output_dir=preview_dir)
    if preview.status != "pass":
        errors.extend(preview.errors)
    generated_files.extend(path for path in preview_dir.iterdir() if path.is_file())

    readme_path.write_text(_render_handoff_readme(), encoding="utf-8")
    run_commands_path.write_text(_render_run_commands(), encoding="utf-8")
    generated_files.extend([readme_path, run_commands_path])

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

    return EngineeringHandoffPackageResult(
        status=status,
        package_status=status,
        output_dir=str(output_path),
        generated_files=tuple(str(path) for path in generated_files),
        manifest_path=str(manifest_path),
        readme_path=str(readme_path),
        run_commands_path=str(run_commands_path),
        input_json_path=str(input_json_path),
        clean_demo_input_path=str(clean_demo_input_path),
        external_validation_template_path=str(external_template_path),
        material_verification_template_path=str(material_template_path),
        preview_path=preview.output_path,
        file_count=len(generated_files),
        warnings=tuple(warnings),
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )


def _copy_required_file(
    *,
    source: Path,
    target: Path,
    generated_files: list[Path],
    errors: list[str],
) -> None:
    if not source.exists():
        errors.append(f"handoff source missing: {source}")
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
        "report_type": "engineering_handoff_manifest",
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
        "source_files": {
            "base_input": str(BASE_INPUT_SOURCE),
            "clean_demo_input": str(CLEAN_DEMO_INPUT_SOURCE),
            "external_validation_template": str(EXTERNAL_TEMPLATE_SOURCE),
            "material_verification_template": str(MATERIAL_TEMPLATE_SOURCE),
            "quickstart": str(QUICKSTART_SOURCE),
            "acceptance_checklist": str(CHECKLIST_SOURCE),
            "clean_demo_doc": str(CLEAN_DEMO_DOC_SOURCE),
        },
        "warnings": list(warnings),
        "errors": list(errors),
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "ml_ready_for_project_use": False,
    }


def _render_handoff_readme() -> str:
    lines = [
        "# Engineering Handoff Package",
        "",
        HANDOFF_PACKAGE_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Contents",
        "",
        "- `input/rectangular_input.json` - editable deterministic workflow input.",
        "- `demo/rectangular_clean_demo_input.json` - known clean demo input.",
        "- `evidence/external_validation_template.csv` - engineer-filled external validation "
        "template.",
        "- `evidence/material_verification_template.csv` - engineer-filled material "
        "verification template.",
        "- `docs/quickstart.md` - copied quickstart.",
        "- `docs/acceptance_checklist.md` - copied review checklist.",
        "- `docs/clean_demo_workflow.md` - clean demo workflow notes.",
        "- `previews/input_form_preview.html` - static input metadata preview.",
        "- `RUN_COMMANDS.md` - recommended commands.",
        "- `engineering_handoff_manifest.json` - SHA256 checksums.",
        "",
        "## Safety",
        "",
        "- This package does not include full SP 63 text.",
        "- This package does not include personal, grant, private, SCAD, or LIRA files.",
        "- Material catalog values are not changed by this package.",
        "- ML output remains advisory-only and cannot approve a design.",
        "- Deterministic SP63 checks and engineer review remain mandatory.",
    ]
    return "\n".join(lines) + "\n"


def _render_run_commands() -> str:
    lines = [
        "# Engineering Handoff Run Commands",
        "",
        "Run the clean demo workflow:",
        "",
        "```bash",
        "python -m sp63_core clean-demo-workflow \\",
        "  --output-dir reports/clean_demo_workflow \\",
        "  --json",
        "```",
        "",
        "Run a project workflow after editing the input JSON:",
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
        "Run strict external validation after an engineer fills the CSV:",
        "",
        "```bash",
        "python -m sp63_core external-validation \\",
        "  --csv evidence/external_validation_template.csv \\",
        "  --strict \\",
        "  --json",
        "```",
        "",
        "Run material verification closure after an engineer fills the CSV:",
        "",
        "```bash",
        "python -m sp63_core material-verification-closure \\",
        "  --material-verification-csv evidence/material_verification_template.csv \\",
        "  --output-dir reports/material_verification_closure \\",
        "  --json",
        "```",
        "",
        "Baseline checks:",
        "",
        "```bash",
        "python -m sp63_core validate --golden",
        "python -m sp63_core manual-cases --json",
        "python -m sp63_core protected-files-check --json",
        "```",
    ]
    return "\n".join(lines) + "\n"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
