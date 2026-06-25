import csv
import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.materials import MATERIAL_VERIFICATION_REQUIRED_COLUMNS
from sp63_core.validation import EXTERNAL_VALIDATION_COLUMNS
from sp63_core.workflows import build_evidence_templates_package


def test_evidence_templates_package_creates_files(tmp_path):
    result = build_evidence_templates_package(output_dir=tmp_path)

    assert result.status == "pass"
    assert result.package_status == "pass"
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert (tmp_path / "external_validation_template.csv").exists()
    assert (tmp_path / "material_verification_template.csv").exists()
    assert (tmp_path / "README_EVIDENCE_TEMPLATES.md").exists()
    assert (tmp_path / "evidence_templates_manifest.json").exists()


def test_evidence_templates_use_existing_schema_headers(tmp_path):
    build_evidence_templates_package(output_dir=tmp_path)

    with (tmp_path / "external_validation_template.csv").open(encoding="utf-8") as csv_file:
        external_header = next(csv.reader(csv_file))
    with (tmp_path / "material_verification_template.csv").open(encoding="utf-8") as csv_file:
        material_header = next(csv.reader(csv_file))
    assert tuple(external_header) == EXTERNAL_VALIDATION_COLUMNS
    assert tuple(material_header) == MATERIAL_VERIFICATION_REQUIRED_COLUMNS


def test_evidence_templates_manifest_contains_sha256(tmp_path):
    build_evidence_templates_package(output_dir=tmp_path)

    manifest = json.loads(
        (tmp_path / "evidence_templates_manifest.json").read_text(encoding="utf-8")
    )
    files = manifest["files"]
    assert manifest["report_type"] == "evidence_templates_manifest"
    assert len(files) >= 3
    assert all(len(file_info["sha256"]) == 64 for file_info in files)
    assert "external_validation_template.csv" in {
        file_info["relative_path"] for file_info in files
    }


def test_evidence_templates_readme_contains_safety_warning(tmp_path):
    build_evidence_templates_package(output_dir=tmp_path)

    readme = (tmp_path / "README_EVIDENCE_TEMPLATES.md").read_text(encoding="utf-8")
    assert "do not approve project use" in readme
    assert "Material verification does not auto-update catalog values" in readme
    assert "ML remains advisory-only" in readme


def test_cli_evidence_templates_json(tmp_path, capsys):
    output_dir = tmp_path / "evidence"

    exit_code = main(["evidence-templates", "--output-dir", str(output_dir), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "evidence-templates"
    assert payload["status"] == "pass"
    assert payload["ml_ready_for_project_use"] is False
    assert (output_dir / "evidence_templates_manifest.json").exists()


def test_evidence_templates_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/evidence_templates.py").read_text(
        encoding="utf-8"
    )

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source
