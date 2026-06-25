import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_traceability_matrix


def test_traceability_matrix_contains_required_features():
    result = build_traceability_matrix()
    features = {row["feature"] for row in result.rows}

    assert result.status == "pass"
    assert result.row_count >= 16
    assert "deterministic validation" in features
    assert "manual cases" in features
    assert "external validation" in features
    assert "ML advisory readiness" in features
    assert result.requires_engineer_review is True
    assert result.ml_ready_for_project_use is False


def test_traceability_matrix_rows_have_cli_docs_tests_and_safety():
    result = build_traceability_matrix()

    for row in result.rows:
        assert row["cli_command"].startswith("python -m sp63_core")
        assert row["doc_path"]
        assert row["test_path"].startswith("tests/")
        assert row["safety_warnings"]
        assert row["project_use_allowed"] is False


def test_traceability_matrix_writes_files(tmp_path):
    result = build_traceability_matrix(output_dir=tmp_path)

    assert result.output_dir == str(tmp_path)
    assert (tmp_path / "traceability_matrix.json").exists()
    assert (tmp_path / "traceability_matrix.md").exists()
    payload = json.loads((tmp_path / "traceability_matrix.json").read_text(encoding="utf-8"))
    assert payload["report_type"] == "traceability_matrix"


def test_traceability_matrix_docs_exist():
    assert Path("docs/traceability_matrix.md").exists()


def test_cli_traceability_matrix_json(tmp_path, capsys):
    exit_code = main(["traceability-matrix", "--output-dir", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "traceability-matrix"
    assert payload["status"] == "pass"
    assert payload["row_count"] >= 16
    assert payload["ml_ready_for_project_use"] is False
    assert (tmp_path / "traceability_matrix.json").exists()


def test_cli_traceability_matrix_markdown(capsys):
    exit_code = main(["traceability-matrix", "--markdown"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Traceability Matrix" in output
    assert "ml_ready_for_project_use = false" in output
