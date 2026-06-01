"""Tests for K58 ML external validation readiness."""

import csv
import json

from sp63_core.cli import main
from sp63_core.materials import MATERIAL_VERIFICATION_REQUIRED_COLUMNS
from sp63_core.materials.verification import build_material_verification_rows
from sp63_core.ml import (
    evaluate_ml_external_validation_readiness,
    render_ml_external_readiness_markdown,
)

EXTERNAL_SAMPLE = "tests/fixtures/external_validation_sample.csv"


def _write_dataset(path, *, external_status="not_provided", material_status="not_provided"):
    row = {
        "dataset_source": "validated_report_archive",
        "case_id": "case_001",
        "deterministic_checks_required": True,
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "overall_status": "pass",
        "strength_status": "pass",
        "serviceability_status": "pass",
        "concrete_class": "B25",
        "longitudinal_rebar_class": "A500",
        "stirrup_rebar_class": "A240",
        "external_validation_status": external_status,
        "material_verification_status": material_status,
    }
    path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _write_material_verification_csv(path):
    rows = []
    for row in build_material_verification_rows():
        rows.append(
            {
                "material_type": row.material_type,
                "class_name": row.class_name,
                "property_name": row.property_name,
                "catalog_value": row.catalog_value,
                "unit": row.unit,
                "verification_status": "engineer_verified",
                "engineer_value": row.catalog_value,
                "engineer_name": "Synthetic Engineer",
                "review_date": "2026-06-01",
                "source_note": "synthetic test verification note",
                "engineer_comment": "test fixture only",
                "requires_engineer_review": "false",
            }
        )
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=MATERIAL_VERIFICATION_REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_dataset_only_readiness_is_review_required(tmp_path):
    dataset_path = _write_dataset(tmp_path / "dataset.jsonl")

    result = evaluate_ml_external_validation_readiness(dataset_path=dataset_path)

    assert result.status == "review_required"
    assert result.row_count == 1
    assert result.external_validation_present is False
    assert result.material_verification_present is False
    assert result.synthetic_data_only is True
    assert result.ml_ready_for_research is True
    assert result.ml_ready_for_engineering_review is False
    assert result.ml_ready_for_project_use is False
    assert any("external validation is not provided" in warning for warning in result.warnings)
    assert any("material verification is not provided" in warning for warning in result.warnings)


def test_external_validation_sample_counts_cases(tmp_path):
    dataset_path = _write_dataset(tmp_path / "dataset.jsonl")

    result = evaluate_ml_external_validation_readiness(
        dataset_path=dataset_path,
        external_validation_csv=EXTERNAL_SAMPLE,
    )

    assert result.external_validation_present is True
    assert result.external_case_count == 1
    assert result.accepted_external_case_count == 1
    assert result.failed_external_case_count == 0
    assert result.external_match_rate == 1.0
    assert result.synthetic_data_only is False
    assert result.ml_ready_for_engineering_review is False


def test_material_verification_csv_enables_engineering_review_flag(tmp_path):
    dataset_path = _write_dataset(tmp_path / "dataset.jsonl")
    material_path = _write_material_verification_csv(tmp_path / "materials.csv")

    result = evaluate_ml_external_validation_readiness(
        dataset_path=dataset_path,
        external_validation_csv=EXTERNAL_SAMPLE,
        material_verification_csv=material_path,
    )

    assert result.status == "review_required"
    assert result.external_validation_present is True
    assert result.material_verification_present is True
    assert result.ml_ready_for_engineering_review is True
    assert result.ml_ready_for_project_use is False


def test_bad_external_csv_path_fails(tmp_path):
    dataset_path = _write_dataset(tmp_path / "dataset.jsonl")

    result = evaluate_ml_external_validation_readiness(
        dataset_path=dataset_path,
        external_validation_csv=tmp_path / "missing.csv",
    )

    assert result.status == "fail"
    assert result.errors
    assert any("external validation CSV cannot be read" in error for error in result.errors)


def test_markdown_output_contains_report_title(tmp_path):
    dataset_path = _write_dataset(tmp_path / "dataset.jsonl")
    result = evaluate_ml_external_validation_readiness(dataset_path=dataset_path)

    markdown = render_ml_external_readiness_markdown(result)

    assert "ML External Validation Readiness Report" in markdown
    assert "ML is advisory-only" in markdown


def test_cli_ml_external_readiness_json(tmp_path, capsys):
    dataset_path = _write_dataset(tmp_path / "dataset.jsonl")

    exit_code = main(["ml-external-readiness", "--dataset", str(dataset_path), "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "ml-external-readiness"
    assert payload["status"] == "review_required"
    assert payload["row_count"] == 1
    assert payload["external_validation_present"] is False
    assert payload["ml_ready_for_project_use"] is False


def test_cli_ml_external_readiness_markdown_output_file(tmp_path, capsys):
    dataset_path = _write_dataset(tmp_path / "dataset.jsonl")
    output_path = tmp_path / "ml_external_readiness.md"

    exit_code = main(
        [
            "ml-external-readiness",
            "--dataset",
            str(dataset_path),
            "--markdown",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert output_path.exists()
    assert "ML External Validation Readiness Report" in output_path.read_text(
        encoding="utf-8"
    )
    assert "ML External Validation Readiness Report" in captured.out
