import csv
import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_material_verification_closure

FIXTURE = Path("tests/fixtures/material_verification_sample.csv")


def test_material_verification_closure_without_csv_requires_review(tmp_path):
    result = build_material_verification_closure(output_dir=tmp_path)

    assert result.status == "review_required"
    assert result.material_ready_for_engineering_review is False
    assert result.material_ready_for_project_use is False
    assert result.coverage_ratio == 0.0
    assert result.missing_material_keys
    assert (tmp_path / "material_verification_closure.json").exists()
    assert (tmp_path / "README_MATERIAL_VERIFICATION_CLOSURE.md").exists()


def test_material_verification_closure_synthetic_fixture_requires_review(tmp_path):
    result = build_material_verification_closure(
        material_verification_csv=FIXTURE,
        output_dir=tmp_path,
    )

    assert result.status == "review_required"
    assert result.material_ready_for_engineering_review is False
    assert result.material_ready_for_project_use is False
    assert result.coverage_ratio == (len(result.required_material_keys) - 6) / len(
        result.required_material_keys
    )
    assert result.missing_material_keys == ()
    assert result.rejected_material_keys == ()
    assert len(result.review_required_material_keys) == 6


def test_material_verification_closure_missing_row_requires_review(tmp_path):
    csv_path = _write_modified_fixture(tmp_path / "missing.csv", drop_last=True)

    result = build_material_verification_closure(material_verification_csv=csv_path)

    assert result.status == "review_required"
    assert result.material_ready_for_engineering_review is False
    assert result.missing_material_keys
    assert result.material_ready_for_project_use is False


def test_material_verification_closure_rejected_row_fails(tmp_path):
    csv_path = _write_modified_fixture(tmp_path / "rejected.csv", reject_first=True)

    result = build_material_verification_closure(material_verification_csv=csv_path)

    assert result.status == "fail"
    assert result.rejected_material_keys
    assert result.material_ready_for_engineering_review is False
    assert result.material_ready_for_project_use is False


def test_cli_material_verification_closure_json(tmp_path, capsys):
    output_dir = tmp_path / "closure"

    exit_code = main(
        [
            "material-verification-closure",
            "--material-verification-csv",
            str(FIXTURE),
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "material-verification-closure"
    assert payload["status"] == "review_required"
    assert payload["material_ready_for_engineering_review"] is False
    assert payload["material_ready_for_project_use"] is False
    assert (output_dir / "material_verification_closure.md").exists()


def test_cli_material_verification_closure_markdown_no_output_files(tmp_path, capsys):
    exit_code = main(
        [
            "material-verification-closure",
            "--material-verification-csv",
            str(FIXTURE),
            "--output-dir",
            str(tmp_path / "not_written"),
            "--no-output-files",
            "--markdown",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "# Material Verification Closure" in output
    assert "material_ready_for_project_use = false" in output
    assert not (tmp_path / "not_written").exists()


def test_material_verification_closure_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/material_verification_closure.py").read_text(
        encoding="utf-8"
    )

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source


def _write_modified_fixture(
    path: Path,
    *,
    drop_last: bool = False,
    reject_first: bool = False,
) -> Path:
    with FIXTURE.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))
        fieldnames = csv_file.seek(0) or next(csv.reader(csv_file))
    if drop_last:
        rows = rows[:-1]
    if reject_first:
        rows[0]["verification_status"] = "rejected"
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path
