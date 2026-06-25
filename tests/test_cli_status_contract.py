import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_cli_status_contract


def test_cli_status_contract_builds_mapping():
    result = build_cli_status_contract()

    assert result.status == "pass"
    assert result.contract_status == "pass"
    assert result.exit_code_mapping["pass"] == 0
    assert result.exit_code_mapping["review_required"] == 0
    assert result.exit_code_mapping["fail"] == 1
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False


def test_cli_status_contract_documents_review_required_and_protected_guard():
    result = build_cli_status_contract()
    contracts = {item["command"]: item for item in result.command_contracts}

    assert contracts["materials-audit"]["review_required_allowed"] is True
    assert contracts["protected-files-check"]["fail_is_nonzero"] is True
    assert "ci_blocker_note" in contracts["protected-files-check"]


def test_cli_status_contract_writes_output_files(tmp_path):
    result = build_cli_status_contract(output_dir=tmp_path)

    assert result.output_dir == str(tmp_path)
    assert (tmp_path / "cli_status_contract.json").exists()
    assert (tmp_path / "cli_status_contract.md").exists()
    payload = json.loads((tmp_path / "cli_status_contract.json").read_text(encoding="utf-8"))
    assert payload["report_type"] == "cli_status_contract"
    assert payload["ml_ready_for_project_use"] is False


def test_cli_status_contract_docs_exist():
    assert Path("docs/cli_status_contract.md").exists()
    assert Path("docs/user_manual/troubleshooting.md").exists()


def test_cli_status_contract_json(tmp_path, capsys):
    exit_code = main(["cli-status-contract", "--output-dir", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "cli-status-contract"
    assert payload["status"] == "pass"
    assert payload["exit_code_mapping"]["review_required"] == 0
    assert payload["requires_engineer_review"] is True
    assert (tmp_path / "cli_status_contract.json").exists()


def test_cli_status_contract_markdown(capsys):
    exit_code = main(["cli-status-contract", "--markdown"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "CLI Status And Exit-Code Contract" in output
    assert "ml_ready_for_project_use = false" in output
