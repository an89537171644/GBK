import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_freeze_remediation_plan


def test_freeze_remediation_plan_builds_review_required_plan(tmp_path):
    result = build_freeze_remediation_plan(output_dir=tmp_path, version="0.9.0-rc1")

    assert result.status == "review_required"
    assert result.plan_status == "review_required"
    assert result.version == "0.9.0-rc1"
    assert result.blocker_count >= 1
    assert result.acceptable_review_gate_count >= 1
    assert result.required_before_v09_count >= 1
    assert result.required_before_v10_count >= 1
    assert result.project_use_allowed is False
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert Path(result.summary_json_path).exists()
    assert Path(result.summary_markdown_path).exists()
    assert Path(result.readme_path).exists()


def test_freeze_remediation_plan_contains_expected_gates(tmp_path):
    result = build_freeze_remediation_plan(output_dir=tmp_path)
    items = {item["item_id"]: item for item in result.remediation_items}

    for item_id in (
        "material_audit_review_required",
        "external_validation_sample_only",
        "ml_advisory_only",
        "project_use_false",
        "gui_installer_gap",
        "windows_clean_machine_validation_gap",
        "engineer_review_required",
    ):
        assert item_id in items
        assert items[item_id]["cannot_auto_close"] is True


def test_freeze_remediation_plan_json_and_markdown(tmp_path):
    result = build_freeze_remediation_plan(output_dir=tmp_path)
    payload = json.loads(Path(result.summary_json_path).read_text(encoding="utf-8"))
    markdown = Path(result.summary_markdown_path).read_text(encoding="utf-8")
    readme = Path(result.readme_path).read_text(encoding="utf-8")

    assert payload["report_type"] == "freeze_remediation_plan"
    assert payload["project_use_allowed"] is False
    assert "Freeze Remediation Plan" in markdown
    assert "ml_ready_for_project_use = false" in markdown
    assert "README Freeze Remediation" in readme


def test_freeze_remediation_plan_docs_exist():
    assert Path("docs/freeze_remediation_plan.md").exists()
    assert Path("docs/v09_freeze_report.md").exists()
    assert Path("docs/v10_gap_report.md").exists()


def test_cli_freeze_remediation_plan_json(tmp_path, capsys):
    exit_code = main(
        [
            "freeze-remediation-plan",
            "--output-dir",
            str(tmp_path),
            "--version",
            "0.9.0-rc1",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "freeze-remediation-plan"
    assert payload["status"] == "review_required"
    assert payload["blocker_count"] >= 1
    assert payload["project_use_allowed"] is False


def test_cli_freeze_remediation_plan_markdown(tmp_path, capsys):
    exit_code = main(
        ["freeze-remediation-plan", "--output-dir", str(tmp_path), "--markdown"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Freeze Remediation Plan" in output
    assert "project_use_allowed = false" in output
