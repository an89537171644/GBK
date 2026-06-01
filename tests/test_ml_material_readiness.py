"""Tests for K59 material verification readiness."""

import csv
import json

from sp63_core.cli import main
from sp63_core.ml import (
    evaluate_ml_external_validation_readiness,
    evaluate_ml_material_verification_readiness,
    render_ml_material_readiness_markdown,
)

MATERIAL_FIXTURE = "tests/fixtures/material_verification_sample.csv"
EXTERNAL_FIXTURE = "tests/fixtures/external_validation_sample.csv"


def _dataset_row():
    return {
        "dataset_source": "validated_report_archive",
        "case_id": "case_001",
        "concrete_class": "B25",
        "longitudinal_rebar_class": "A500",
        "stirrup_rebar_class": "A240",
        "deterministic_checks_required": True,
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "overall_status": "pass",
    }


def _write_jsonl_dataset(path):
    path.write_text(json.dumps(_dataset_row(), ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _write_csv_dataset(path):
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=tuple(_dataset_row()))
        writer.writeheader()
        writer.writerow(_dataset_row())
    return path


def _read_material_rows():
    with open(MATERIAL_FIXTURE, newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def _write_material_rows(path, rows):
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_material_readiness_without_csv_is_review_required(tmp_path):
    dataset_path = _write_jsonl_dataset(tmp_path / "dataset.jsonl")

    result = evaluate_ml_material_verification_readiness(dataset_path=dataset_path)

    assert result.status == "review_required"
    assert result.material_verification_present is False
    assert result.material_verification_complete is False
    assert result.material_ready_for_engineering_review is False
    assert result.material_ready_for_project_use is False
    assert result.required_material_keys == (
        "concrete:B25",
        "longitudinal_rebar:A500",
        "stirrup_rebar:A240",
    )
    assert result.missing_material_keys == result.required_material_keys
    assert result.review_required_material_keys == ()


def test_material_readiness_with_complete_fixture(tmp_path):
    dataset_path = _write_jsonl_dataset(tmp_path / "dataset.jsonl")

    result = evaluate_ml_material_verification_readiness(
        dataset_path=dataset_path,
        material_verification_csv=MATERIAL_FIXTURE,
    )

    assert result.status == "review_required"
    assert result.material_verification_present is True
    assert result.material_verification_complete is True
    assert result.material_coverage_ratio == 1.0
    assert result.verified_material_keys == result.required_material_keys
    assert result.missing_material_keys == ()
    assert result.rejected_material_keys == ()
    assert result.review_required_material_keys == ()
    assert result.material_ready_for_engineering_review is True
    assert result.material_ready_for_project_use is False


def test_material_readiness_missing_material_entry_is_review_required(tmp_path):
    dataset_path = _write_jsonl_dataset(tmp_path / "dataset.jsonl")
    rows = [
        row
        for row in _read_material_rows()
        if not (row["material_type"] == "concrete" and row["class_name"] == "B25")
    ]
    material_path = _write_material_rows(tmp_path / "materials_missing.csv", rows)

    result = evaluate_ml_material_verification_readiness(
        dataset_path=dataset_path,
        material_verification_csv=material_path,
    )

    assert result.status == "review_required"
    assert "concrete:B25" in result.missing_material_keys
    assert result.material_verification_complete is False


def test_material_readiness_rejected_material_entry_fails(tmp_path):
    dataset_path = _write_jsonl_dataset(tmp_path / "dataset.jsonl")
    rows = _read_material_rows()
    for row in rows:
        if row["material_type"] == "rebar" and row["class_name"] == "A500":
            row["verification_status"] = "rejected"
            break
    material_path = _write_material_rows(tmp_path / "materials_rejected.csv", rows)

    result = evaluate_ml_material_verification_readiness(
        dataset_path=dataset_path,
        material_verification_csv=material_path,
    )

    assert result.status == "fail"
    assert "longitudinal_rebar:A500" in result.rejected_material_keys


def test_material_readiness_empty_engineer_fields_need_review(tmp_path):
    dataset_path = _write_jsonl_dataset(tmp_path / "dataset.jsonl")
    rows = _read_material_rows()
    for row in rows:
        if row["material_type"] == "rebar" and row["class_name"] == "A240":
            row["engineer_name"] = ""
            break
    material_path = _write_material_rows(tmp_path / "materials_review.csv", rows)

    result = evaluate_ml_material_verification_readiness(
        dataset_path=dataset_path,
        material_verification_csv=material_path,
    )

    assert result.status == "review_required"
    assert "stirrup_rebar:A240" in result.review_required_material_keys


def test_material_readiness_supports_csv_dataset(tmp_path):
    dataset_path = _write_csv_dataset(tmp_path / "dataset.csv")

    result = evaluate_ml_material_verification_readiness(
        dataset_path=dataset_path,
        dataset_format="csv",
        material_verification_csv=MATERIAL_FIXTURE,
    )

    assert result.row_count == 1
    assert result.material_coverage_ratio == 1.0
    assert result.material_ready_for_engineering_review is True


def test_material_readiness_rejects_missing_dataset_material_field(tmp_path):
    row = _dataset_row()
    row["concrete_class"] = ""
    dataset_path = tmp_path / "bad_dataset.jsonl"
    dataset_path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")

    result = evaluate_ml_material_verification_readiness(
        dataset_path=dataset_path,
        material_verification_csv=MATERIAL_FIXTURE,
    )

    assert result.status == "fail"
    assert any("empty material class fields" in error for error in result.errors)


def test_material_readiness_markdown_output(tmp_path):
    dataset_path = _write_jsonl_dataset(tmp_path / "dataset.jsonl")
    result = evaluate_ml_material_verification_readiness(
        dataset_path=dataset_path,
        material_verification_csv=MATERIAL_FIXTURE,
    )

    markdown = render_ml_material_readiness_markdown(result)

    assert "ML Material Verification Readiness" in markdown
    assert "material_coverage_ratio" in markdown


def test_cli_ml_material_readiness_json(tmp_path, capsys):
    dataset_path = _write_jsonl_dataset(tmp_path / "dataset.jsonl")

    exit_code = main(
        [
            "ml-material-readiness",
            "--dataset",
            str(dataset_path),
            "--material-verification-csv",
            MATERIAL_FIXTURE,
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "ml-material-readiness"
    assert payload["material_verification_present"] is True
    assert payload["material_coverage_ratio"] == 1.0
    assert payload["material_ready_for_project_use"] is False


def test_cli_ml_material_readiness_markdown_output(tmp_path, capsys):
    dataset_path = _write_jsonl_dataset(tmp_path / "dataset.jsonl")
    output_path = tmp_path / "ml_material_readiness.md"

    exit_code = main(
        [
            "ml-material-readiness",
            "--dataset",
            str(dataset_path),
            "--material-verification-csv",
            MATERIAL_FIXTURE,
            "--markdown",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "ML Material Verification Readiness" in captured.out
    assert output_path.exists()
    assert "ML Material Verification Readiness" in output_path.read_text(encoding="utf-8")


def test_external_readiness_includes_material_readiness_fields(tmp_path):
    dataset_path = _write_jsonl_dataset(tmp_path / "dataset.jsonl")

    result = evaluate_ml_external_validation_readiness(
        dataset_path=dataset_path,
        external_validation_csv=EXTERNAL_FIXTURE,
        material_verification_csv=MATERIAL_FIXTURE,
    )

    assert result.material_verification_present is True
    assert result.material_verification_complete is True
    assert result.material_coverage_ratio == 1.0
    assert result.required_material_keys == (
        "concrete:B25",
        "longitudinal_rebar:A500",
        "stirrup_rebar:A240",
    )
    assert result.material_ready_for_engineering_review is True
    assert result.ml_ready_for_engineering_review is True
    assert result.ml_ready_for_project_use is False
