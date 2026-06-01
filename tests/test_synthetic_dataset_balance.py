import csv
import json

from sp63_core.cli import main
from sp63_core.dataset import (
    analyze_synthetic_dataset_balance,
    build_stratified_split_summary,
)


def _balanced_rows():
    rows = []
    statuses = ("pass", "fail", "review_or_fail")
    for index in range(9):
        status = statuses[index % len(statuses)]
        rows.append(
            {
                "dataset_source": "synthetic_report_derived_sp63_core",
                "case_id": f"case_{index:03d}",
                "source_archive_path": f"reports/case_{index:03d}",
                "report_json_path": f"reports/case_{index:03d}/report.json",
                "input_json_path": f"inputs/case_{index:03d}.json",
                "manifest_path": f"reports/case_{index:03d}/manifest.json",
                "input_sha256": f"input-{index}",
                "report_json_sha256": f"report-{index}",
                "manifest_sha256": f"manifest-{index}",
                "archive_validation_status": "pass",
                "b": 300,
                "h": 500,
                "cover": 32,
                "concrete_class": "B25",
                "longitudinal_rebar_class": "A500",
                "stirrup_rebar_class": "A240",
                "M": 120_000_000 + index,
                "Q": 80_000 + index,
                "Mser": 30_000_000 + index,
                "span": 6000,
                "strength_status": "pass" if status != "fail" else "fail",
                "serviceability_status": (
                    "review_or_fail" if status == "review_or_fail" else status
                ),
                "overall_status": status,
                "bending_status": "pass" if status != "fail" else "fail",
                "shear_status": "pass",
                "crack_width_status": "pass",
                "deflection_status": (
                    "review_or_fail" if status == "review_or_fail" else "pass"
                ),
                "failure_reason": "" if status == "pass" else "synthetic diagnostic status",
                "warnings_count": 0 if status == "pass" else 1,
                "external_validation_status": "provided",
                "material_verification_status": "provided",
                "requires_engineer_review": True,
                "ml_is_advisory_only": True,
                "deterministic_checks_required": True,
            }
        )
    return rows


def _write_jsonl(path, rows):
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_synthetic_dataset_balance_passes_for_balanced_rows(tmp_path):
    dataset_path = tmp_path / "synthetic.jsonl"
    _write_jsonl(dataset_path, _balanced_rows())

    result = analyze_synthetic_dataset_balance(
        dataset_path=dataset_path,
        min_rows=9,
        min_class_count=3,
    )

    assert result.status == "pass"
    assert result.row_count == 9
    assert result.required_classes_present is True
    assert result.target_distribution == {"fail": 3, "pass": 3, "review_or_fail": 3}
    assert result.stratified_split_ready is True
    assert result.train_count + result.validation_count + result.test_count == 9
    assert result.synthetic_data_only is True
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True


def test_synthetic_dataset_balance_warns_for_missing_review_class(tmp_path):
    rows = _balanced_rows()
    for row in rows:
        if row["overall_status"] == "review_or_fail":
            row["overall_status"] = "pass"
            row["serviceability_status"] = "pass"
            row["deflection_status"] = "pass"
    dataset_path = tmp_path / "synthetic_missing_class.jsonl"
    _write_jsonl(dataset_path, rows)

    result = analyze_synthetic_dataset_balance(
        dataset_path=dataset_path,
        min_rows=9,
        min_class_count=1,
    )

    assert result.status == "review_required"
    assert "review_or_fail" in result.missing_required_classes
    assert any("serviceability review cases" in item for item in result.recommendations)


def test_synthetic_dataset_balance_fails_for_archive_validation_failure(tmp_path):
    rows = _balanced_rows()
    rows[0]["archive_validation_status"] = "fail"
    dataset_path = tmp_path / "synthetic_archive_fail.jsonl"
    _write_jsonl(dataset_path, rows)

    result = analyze_synthetic_dataset_balance(dataset_path=dataset_path)

    assert result.status == "fail"
    assert any("archive_validation_status" in error for error in result.errors)


def test_synthetic_dataset_balance_reads_csv(tmp_path):
    dataset_path = tmp_path / "synthetic.csv"
    _write_csv(dataset_path, _balanced_rows())

    result = analyze_synthetic_dataset_balance(
        dataset_path=dataset_path,
        dataset_format="csv",
        min_rows=9,
        min_class_count=3,
    )

    assert result.status == "pass"
    assert result.row_count == 9
    assert result.target_distribution["pass"] == 3


def test_build_stratified_split_summary_preserves_classes(tmp_path):
    rows = _balanced_rows()

    summary = build_stratified_split_summary(rows=rows, target="overall_status")

    assert summary["stratified_split_ready"] is True
    assert summary["train_count"] + summary["validation_count"] + summary["test_count"] == 9
    for split_name in ("train", "validation", "test"):
        assert set(summary["class_counts_by_split"][split_name]) == {
            "pass",
            "fail",
            "review_or_fail",
        }


def test_cli_synthetic_dataset_balance_json_output(tmp_path, capsys):
    dataset_path = tmp_path / "synthetic.jsonl"
    _write_jsonl(dataset_path, _balanced_rows())

    exit_code = main(
        [
            "synthetic-dataset-balance",
            "--dataset",
            str(dataset_path),
            "--min-rows",
            "9",
            "--min-class-count",
            "3",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "synthetic-dataset-balance"
    assert payload["status"] == "pass"
    assert payload["target_distribution"]["review_or_fail"] == 3


def test_cli_synthetic_dataset_balance_writes_split_index(tmp_path, capsys):
    dataset_path = tmp_path / "synthetic.jsonl"
    split_index_path = tmp_path / "synthetic_split_index.json"
    _write_jsonl(dataset_path, _balanced_rows())

    exit_code = main(
        [
            "synthetic-dataset-balance",
            "--dataset",
            str(dataset_path),
            "--split-index-output",
            str(split_index_path),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    split_payload = json.loads(split_index_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["split_index_output"] == str(split_index_path)
    assert split_payload["target"] == "overall_status"
    assert split_payload["stratified_split_ready"] is True
    assert split_payload["requires_engineer_review"] is True
