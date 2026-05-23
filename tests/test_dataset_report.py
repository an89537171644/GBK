import json

from sp63_core.dataset import (
    build_dataset_report,
    export_dataset_report_json,
    generate_dataset_cases,
)


def test_build_dataset_report_contains_core_counts():
    cases = generate_dataset_cases(limit=10)

    report = build_dataset_report(cases)

    assert report["total_rows"] == 10
    assert report["unsafe_rows_count"] == 0
    assert report["unique_group_count"] > 0
    assert report["geometry_stirrup_mismatch_count"] == 0
    assert report["duplicate_case_id_count"] == 0
    assert report["counts_by_main_rebar_scheme"]
    assert report["counts_by_stirrup_scheme"]
    assert "counts_by_concrete_class" in report
    assert report["counts_by_element_type"] == {"beam": 10}
    assert report["min_b"] <= report["max_b"]
    assert report["min_h0"] <= report["max_h0"]


def test_export_dataset_report_json_creates_file(tmp_path):
    cases = generate_dataset_cases(limit=3)
    report = build_dataset_report(cases)

    path = export_dataset_report_json(report, tmp_path / "report.json")

    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["total_rows"] == 3
    assert data["unsafe_rows_count"] == 0
