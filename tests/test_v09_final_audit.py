import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_v09_final_audit


def test_v09_final_audit_builds_aggregated_report(tmp_path):
    output_dir = tmp_path / "v09_final_audit"

    result = build_v09_final_audit(output_dir=output_dir)

    assert result.status in {"pass", "review_required"}
    assert result.audit_status == result.status
    assert result.audit_count >= 8
    assert result.failed_count == 0
    assert result.passed_count + result.review_required_count == result.audit_count
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert Path(result.summary_json_path).exists()
    assert Path(result.summary_markdown_path).exists()


def test_v09_final_audit_contains_expected_items(tmp_path):
    output_dir = tmp_path / "v09_final_audit_items"

    result = build_v09_final_audit(output_dir=output_dir)
    items = {item["name"]: item["status"] for item in result.audit_items}

    assert items["protected-files-check"] == "pass"
    assert items["clean-demo-workflow"] == "pass"
    assert items["engineering-handoff-package"] == "pass"
    assert items["launcher-scripts"] == "pass"
    assert items["material-verification-closure"] == "pass"
    assert items["external-validation-evidence-package"] == "pass"
    assert "v09-readiness" in items
    assert "docs-audit" in items


def test_v09_final_audit_writes_json_and_markdown(tmp_path):
    output_dir = tmp_path / "v09_final_audit_files"

    result = build_v09_final_audit(output_dir=output_dir)
    payload = json.loads(Path(result.summary_json_path).read_text(encoding="utf-8"))
    markdown = Path(result.summary_markdown_path).read_text(encoding="utf-8")

    assert payload["report_type"] == "v09_final_audit"
    assert payload["audit_status"] == result.audit_status
    assert payload["ml_ready_for_project_use"] is False
    assert "v0.9 Final Audit" in markdown
    assert "ml_ready_for_project_use = false" in markdown


def test_cli_v09_final_audit_json(tmp_path, capsys):
    output_dir = tmp_path / "v09_final_audit_cli"

    exit_code = main(
        [
            "v09-final-audit",
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "v09-final-audit"
    assert payload["status"] in {"pass", "review_required"}
    assert payload["failed_count"] == 0
    assert payload["requires_engineer_review"] is True
    assert payload["ml_ready_for_project_use"] is False
    assert Path(payload["summary_json_path"]).exists()
