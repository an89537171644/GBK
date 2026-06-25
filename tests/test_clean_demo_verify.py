import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import run_clean_demo_and_verify, run_clean_demo_workflow


def test_clean_demo_verify_full_run_passes(tmp_path):
    result = run_clean_demo_and_verify(output_dir=tmp_path)

    assert result.status == "pass"
    assert result.verification_status == "pass"
    assert result.missing_artifacts == ()
    assert result.ml_ready_true_files == ()
    assert result.warning_artifacts_present is True
    assert result.requires_engineer_review is True
    assert result.ml_ready_for_project_use is False
    assert (tmp_path / "clean_demo_verification.json").exists()
    assert (tmp_path / "clean_demo_verification.md").exists()


def test_clean_demo_verify_existing_workflow(tmp_path):
    run_clean_demo_workflow(output_dir=tmp_path)

    result = run_clean_demo_and_verify(output_dir=tmp_path)

    assert result.status == "pass"
    assert "workflow_summary.json" in result.checked_artifacts


def test_clean_demo_verify_missing_artifact_fails(tmp_path):
    run_clean_demo_workflow(output_dir=tmp_path)
    (tmp_path / "workflow_summary.json").unlink()

    exit_code = main(["clean-demo-verify", "--workflow-dir", str(tmp_path), "--json"])

    assert exit_code == 1


def test_clean_demo_verify_json_payload_for_missing_artifact(tmp_path, capsys):
    run_clean_demo_workflow(output_dir=tmp_path)
    (tmp_path / "workflow_summary.json").unlink()

    main(["clean-demo-verify", "--workflow-dir", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert payload["command"] == "clean-demo-verify"
    assert payload["status"] == "fail"
    assert "workflow_summary.json" in payload["missing_artifacts"]


def test_cli_clean_demo_verify_run_json(tmp_path, capsys):
    exit_code = main(["clean-demo-verify", "--run", "--output-dir", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "clean-demo-verify"
    assert payload["status"] == "pass"
    assert payload["warning_artifacts_present"] is True
    assert payload["ml_ready_for_project_use"] is False


def test_clean_demo_verification_docs_exist():
    assert Path("docs/clean_demo_verification.md").exists()
