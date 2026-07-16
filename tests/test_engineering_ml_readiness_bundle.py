import csv
import json

from sp63_core.cli import main
from sp63_core.dataset import DATASET_VERSION, REQUIRED_REPORT_DATASET_COLUMNS
from sp63_core.ml import (
    build_engineering_ml_readiness_bundle,
    render_readiness_matrix_csv,
)

EXTERNAL_FIXTURE = "tests/fixtures/external_validation_sample.csv"
MATERIAL_FIXTURE = "tests/fixtures/material_verification_sample.csv"


def _dataset_row():
    row = {column: "1" for column in REQUIRED_REPORT_DATASET_COLUMNS}
    row.update(
        {
            "dataset_source": "validated_report_archive",
            "dataset_version": DATASET_VERSION,
            "case_id": "case_001",
            "source_archive_path": "reports/case_001",
            "report_json_path": "reports/case_001/report.json",
            "input_json_path": "reports/case_001/input.json",
            "manifest_path": "reports/case_001/manifest.json",
            "input_sha256": "a" * 64,
            "report_json_sha256": "b" * 64,
            "manifest_sha256": "c" * 64,
            "archive_validation_status": "pass",
            "local_axes_id": "case-001-local-axes",
            "moment_axis": "local_z",
            "tension_face": "local_y_min",
            "load_duration": "short",
            "completeness_status": "incomplete",
            "evidence_status": "needs_engineer_review",
            "project_use_status": "prohibited",
            "project_use": False,
            "b": 300,
            "h": 500,
            "cover": 32,
            "concrete_class": "B25",
            "longitudinal_rebar_class": "A500",
            "stirrup_rebar_class": "A240",
            "M": 150_000_000,
            "Q": 80_000,
            "strength_status": "pass",
            "serviceability_status": "pass",
            "overall_status": "pass",
            "warnings_count": 0,
            "requires_engineer_review": True,
            "ml_is_advisory_only": True,
            "deterministic_checks_required": True,
            "external_validation_status": "not_provided",
            "material_verification_status": "not_provided",
        }
    )
    return row


def _write_jsonl_dataset(path):
    path.write_text(json.dumps(_dataset_row(), ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _write_csv_dataset(path):
    row = _dataset_row()
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=tuple(row))
        writer.writeheader()
        writer.writerow(row)
    return path


def _write_failed_external_csv(path):
    with open(EXTERNAL_FIXTURE, newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
        fieldnames = csv_file.seek(0) or csv.DictReader(csv_file).fieldnames
    rows[0]["acceptance_status"] = "failed"
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _write_rejected_material_csv(path):
    with open(MATERIAL_FIXTURE, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)
        fieldnames = reader.fieldnames
    for row in rows:
        if row["material_type"] == "rebar" and row["class_name"] == "A500":
            row["verification_status"] = "rejected"
            break
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_bundle_without_evidence_is_review_required(tmp_path):
    dataset = _write_jsonl_dataset(tmp_path / "dataset.jsonl")

    result = build_engineering_ml_readiness_bundle(dataset_path=dataset)

    assert result.status == "review_required"
    assert result.ml_ready_for_research is True
    assert result.ml_ready_for_engineering_review is False
    assert result.ml_ready_for_project_use is False
    assert result.external_validation_present is False
    assert result.material_verification_present is False


def test_bundle_with_external_and_material_csv_is_ready_for_engineering_review(tmp_path):
    dataset = _write_jsonl_dataset(tmp_path / "dataset.jsonl")

    result = build_engineering_ml_readiness_bundle(
        dataset_path=dataset,
        external_validation_csv=EXTERNAL_FIXTURE,
        material_verification_csv=MATERIAL_FIXTURE,
    )

    assert result.external_validation_present is True
    assert result.accepted_external_case_count == 1
    assert result.failed_external_case_count == 0
    assert result.material_verification_complete is True
    assert result.material_coverage_ratio == 1.0
    assert result.ml_ready_for_engineering_review is True
    assert result.ml_ready_for_project_use is False


def test_bundle_supports_csv_dataset(tmp_path):
    dataset = _write_csv_dataset(tmp_path / "dataset.csv")

    result = build_engineering_ml_readiness_bundle(
        dataset_path=dataset,
        dataset_format="csv",
        external_validation_csv=EXTERNAL_FIXTURE,
        material_verification_csv=MATERIAL_FIXTURE,
    )

    assert result.row_count == 1
    assert result.material_verification_complete is True
    assert result.ml_ready_for_research is True


def test_bundle_fails_failed_external_validation(tmp_path):
    dataset = _write_jsonl_dataset(tmp_path / "dataset.jsonl")
    failed_external = _write_failed_external_csv(tmp_path / "external_failed.csv")

    result = build_engineering_ml_readiness_bundle(
        dataset_path=dataset,
        external_validation_csv=failed_external,
        material_verification_csv=MATERIAL_FIXTURE,
    )

    assert result.status == "fail"
    assert result.failed_external_case_count == 1
    assert result.ml_ready_for_engineering_review is False


def test_bundle_fails_rejected_material_verification(tmp_path):
    dataset = _write_jsonl_dataset(tmp_path / "dataset.jsonl")
    rejected_material = _write_rejected_material_csv(tmp_path / "materials_rejected.csv")

    result = build_engineering_ml_readiness_bundle(
        dataset_path=dataset,
        external_validation_csv=EXTERNAL_FIXTURE,
        material_verification_csv=rejected_material,
    )

    assert result.status == "fail"
    assert result.material_verification_complete is False
    assert result.ml_ready_for_engineering_review is False


def test_bundle_writes_markdown_json_csv_and_readme(tmp_path):
    dataset = _write_jsonl_dataset(tmp_path / "dataset.jsonl")
    output_dir = tmp_path / "bundle"

    result = build_engineering_ml_readiness_bundle(
        dataset_path=dataset,
        external_validation_csv=EXTERNAL_FIXTURE,
        material_verification_csv=MATERIAL_FIXTURE,
        output_dir=output_dir,
    )

    assert (output_dir / "engineering_ml_readiness.md").exists()
    assert (output_dir / "engineering_ml_readiness.json").exists()
    assert (output_dir / "engineering_ml_readiness_matrix.csv").exists()
    assert (output_dir / "README_REVIEW.md").exists()
    assert "Advisory Only" in result.markdown
    assert "requires_engineer_review" in (output_dir / "README_REVIEW.md").read_text(
        encoding="utf-8"
    )


def test_bundle_matrix_csv_contains_required_columns(tmp_path):
    dataset = _write_jsonl_dataset(tmp_path / "dataset.jsonl")
    result = build_engineering_ml_readiness_bundle(dataset_path=dataset)

    csv_text = render_readiness_matrix_csv(result.readiness_matrix)

    assert "check,status,ready_for_research" in csv_text
    assert "dataset_quality" in csv_text


def test_cli_engineering_ml_readiness_json(tmp_path, capsys):
    dataset = _write_jsonl_dataset(tmp_path / "dataset.jsonl")

    exit_code = main(
        [
            "engineering-ml-readiness",
            "--dataset",
            str(dataset),
            "--external-validation-csv",
            EXTERNAL_FIXTURE,
            "--material-verification-csv",
            MATERIAL_FIXTURE,
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "engineering-ml-readiness"
    assert payload["ml_ready_for_engineering_review"] is True
    assert payload["ml_ready_for_project_use"] is False


def test_cli_engineering_ml_readiness_markdown_and_csv(tmp_path, capsys):
    dataset = _write_jsonl_dataset(tmp_path / "dataset.jsonl")

    markdown_exit = main(["engineering-ml-readiness", "--dataset", str(dataset), "--markdown"])
    markdown_output = capsys.readouterr().out
    csv_exit = main(["engineering-ml-readiness", "--dataset", str(dataset), "--csv"])
    csv_output = capsys.readouterr().out

    assert markdown_exit == 0
    assert "Engineering ML Readiness Bundle" in markdown_output
    assert csv_exit == 0
    assert "dataset_quality" in csv_output


def test_cli_engineering_ml_readiness_output_dir(tmp_path, capsys):
    dataset = _write_jsonl_dataset(tmp_path / "dataset.jsonl")
    output_dir = tmp_path / "engineering_ml_readiness"

    exit_code = main(
        [
            "engineering-ml-readiness",
            "--dataset",
            str(dataset),
            "--external-validation-csv",
            EXTERNAL_FIXTURE,
            "--material-verification-csv",
            MATERIAL_FIXTURE,
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["output_dir"] == str(output_dir)
    assert (output_dir / "engineering_ml_readiness.md").exists()
    assert (output_dir / "engineering_ml_readiness.json").exists()
    assert (output_dir / "engineering_ml_readiness_matrix.csv").exists()
    assert (output_dir / "README_REVIEW.md").exists()
