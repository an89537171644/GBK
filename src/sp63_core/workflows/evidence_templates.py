"""Package external/material evidence templates for engineer handoff."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

EVIDENCE_TEMPLATE_WARNING = (
    "Evidence templates are blank engineer-input forms. They do not approve "
    "project use and do not update material catalog values automatically."
)

EXTERNAL_TEMPLATE_SOURCE = Path(
    "docs/validation/templates/external_validation_engineer_input_template.csv"
)
MATERIAL_TEMPLATE_SOURCE = Path(
    "docs/materials/templates/material_catalog_verification_template.csv"
)


@dataclass(frozen=True)
class EvidenceTemplatesPackageResult:
    """Result of creating an evidence templates package."""

    status: str
    package_status: str
    output_dir: str
    generated_files: tuple[str, ...]
    external_validation_template_path: str
    material_verification_template_path: str
    readme_path: str
    manifest_path: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_evidence_templates_package(
    *,
    output_dir: Path,
) -> EvidenceTemplatesPackageResult:
    """Create an engineer evidence templates package."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    external_output = output_path / "external_validation_template.csv"
    material_output = output_path / "material_verification_template.csv"
    readme_path = output_path / "README_EVIDENCE_TEMPLATES.md"
    manifest_path = output_path / "evidence_templates_manifest.json"

    warnings: list[str] = [EVIDENCE_TEMPLATE_WARNING]
    errors: list[str] = []
    generated_files: list[Path] = []

    for source, target in (
        (EXTERNAL_TEMPLATE_SOURCE, external_output),
        (MATERIAL_TEMPLATE_SOURCE, material_output),
    ):
        if not source.exists():
            errors.append(f"template source missing: {source}")
            continue
        shutil.copyfile(source, target)
        generated_files.append(target)

    readme_path.write_text(_render_evidence_templates_readme(), encoding="utf-8")
    generated_files.append(readme_path)

    status = "fail" if errors else "pass"
    manifest = _build_manifest(
        output_dir=output_path,
        generated_files=tuple(generated_files),
        status=status,
        warnings=tuple(warnings),
        errors=tuple(errors),
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    generated_files.append(manifest_path)

    return EvidenceTemplatesPackageResult(
        status=status,
        package_status=status,
        output_dir=str(output_path),
        generated_files=tuple(str(path) for path in generated_files),
        external_validation_template_path=str(external_output),
        material_verification_template_path=str(material_output),
        readme_path=str(readme_path),
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
        "report_type": "evidence_templates_manifest",
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


def _render_evidence_templates_readme() -> str:
    lines = [
        "# Evidence Templates Package",
        "",
        EVIDENCE_TEMPLATE_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Files",
        "",
        "- `external_validation_template.csv`: blank engineer input template for "
        "manual, Excel, SCAD, or LIRA comparison values.",
        "- `material_verification_template.csv`: blank material catalog verification "
        "template based on the current audit schema.",
        "- `evidence_templates_manifest.json`: generated-file SHA256 checksums.",
        "",
        "## Engineer Instructions",
        "",
        "1. Fill external validation values manually from public/manual/engineer "
        "review sources.",
        "2. Fill material verification values manually after checking SP 63 tables.",
        "3. Do not paste full normative text into these CSV files.",
        "4. Do not include personal, grant, private, or closed SCAD/LIRA documents.",
        "5. Run external validation and material verification commands after filling.",
        "",
        "## Safety",
        "",
        "- The templates do not certify designs.",
        "- Material verification does not auto-update catalog values.",
        "- ML remains advisory-only.",
        "- Deterministic SP63 checks remain mandatory.",
        "- Engineer review remains mandatory.",
    ]
    return "\n".join(lines) + "\n"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
