import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import run_user_acceptance_smoke


def test_user_acceptance_smoke_creates_summary_and_nested_outputs(tmp_path):
    result = run_user_acceptance_smoke(output_dir=tmp_path)

    assert result.status in {"pass", "review_required"}
    assert result.user_acceptance_status == "review_required"
    assert result.smoke_count >= 8
    assert result.failed_count == 0
    assert result.review_required_count >= 1
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.ml_ready_for_project_use is False
    assert (tmp_path / "user_acceptance_smoke.json").exists()
    assert (tmp_path / "user_acceptance_smoke.md").exists()
    assert (tmp_path / "project_template").exists()
    assert (tmp_path / "batch_valid").exists()
    assert (tmp_path / "release_manifest").exists()


def test_user_acceptance_smoke_json_records_smoke_results(tmp_path):
    run_user_acceptance_smoke(output_dir=tmp_path)

    payload = json.loads((tmp_path / "user_acceptance_smoke.json").read_text(encoding="utf-8"))
    smoke_names = {item["name"] for item in payload["smoke_results"]}
    assert payload["report_type"] == "user_acceptance_smoke"
    assert payload["ml_ready_for_project_use"] is False
    assert "validate --golden" in smoke_names
    assert "docs-audit --json" in smoke_names
    assert "release-manifest --json" in smoke_names


def test_cli_user_acceptance_smoke_json(tmp_path, capsys):
    output_dir = tmp_path / "acceptance"

    exit_code = main(["user-acceptance-smoke", "--output-dir", str(output_dir), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "user-acceptance-smoke"
    assert payload["user_acceptance_status"] == "review_required"
    assert payload["failed_count"] == 0
    assert payload["ml_ready_for_project_use"] is False


def test_cli_user_acceptance_smoke_markdown(tmp_path, capsys):
    exit_code = main(
        [
            "user-acceptance-smoke",
            "--output-dir",
            str(tmp_path / "acceptance_markdown"),
            "--markdown",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "# User Acceptance Smoke Suite" in output
    assert "ml_ready_for_project_use = false" in output


def test_user_acceptance_smoke_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/user_acceptance_smoke.py").read_text(
        encoding="utf-8"
    )

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source
