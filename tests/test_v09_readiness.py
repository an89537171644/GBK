import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_v09_readiness_gate


def test_v09_readiness_gate_creates_summary_and_nested_reports(tmp_path):
    result = build_v09_readiness_gate(output_dir=tmp_path)

    assert result.status in {"pass", "review_required"}
    assert result.readiness_status == "review_required"
    assert result.gate_count == 5
    assert result.failed_count == 0
    assert result.review_required_count >= 1
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.ml_ready_for_project_use is False
    assert (tmp_path / "v09_readiness_report.json").exists()
    assert (tmp_path / "v09_readiness_report.md").exists()
    assert (tmp_path / "release_manifest").exists()
    assert (tmp_path / "user_acceptance_smoke").exists()
    assert (tmp_path / "release_candidate").exists()


def test_v09_readiness_json_records_gates(tmp_path):
    build_v09_readiness_gate(output_dir=tmp_path)

    payload = json.loads((tmp_path / "v09_readiness_report.json").read_text(encoding="utf-8"))
    gate_names = {item["name"] for item in payload["gates"]}
    assert payload["report_type"] == "v09_readiness_gate"
    assert payload["ml_ready_for_project_use"] is False
    assert "protected-files-check" in gate_names
    assert "docs-audit" in gate_names
    assert "user-acceptance-smoke" in gate_names
    assert "release-candidate-report" in gate_names


def test_cli_v09_readiness_json(tmp_path, capsys):
    output_dir = tmp_path / "readiness"

    exit_code = main(["v09-readiness", "--output-dir", str(output_dir), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "v09-readiness"
    assert payload["readiness_status"] == "review_required"
    assert payload["failed_count"] == 0
    assert payload["ml_ready_for_project_use"] is False


def test_cli_v09_readiness_markdown(tmp_path, capsys):
    exit_code = main(
        [
            "v09-readiness",
            "--output-dir",
            str(tmp_path / "readiness_markdown"),
            "--markdown",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "# v0.9 Readiness Gate" in output
    assert "ml_ready_for_project_use = false" in output


def test_v09_readiness_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/v09_readiness.py").read_text(encoding="utf-8")

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source
