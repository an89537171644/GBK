import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import (
    build_json_output_contract,
    validate_payload_against_json_contract,
)


def test_json_output_contract_builds_contracts():
    result = build_json_output_contract()

    assert result.status == "pass"
    assert result.contract_status == "pass"
    assert result.contract_count >= 15
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False


def test_json_output_contract_requires_safety_keys():
    result = build_json_output_contract()

    for contract in result.contracts:
        assert "requires_engineer_review" in contract["boolean_safety_keys"]


def test_json_output_contract_helper_fails_on_missing_key():
    result = build_json_output_contract()
    contract = next(item for item in result.contracts if item["command"] == "input-preflight")

    validation = validate_payload_against_json_contract({"command": "input-preflight"}, contract)

    assert validation.status == "fail"
    assert "status" in validation.missing_required_keys
    assert "requires_engineer_review" in validation.missing_safety_keys


def test_json_output_contract_helper_passes_on_minimal_payload():
    result = build_json_output_contract()
    contract = next(item for item in result.contracts if item["command"] == "protected-files-check")
    payload = {
        "command": "protected-files-check",
        "status": "pass",
        "guard_status": "pass",
        "changed_protected_files": [],
        "requires_engineer_review": True,
    }

    validation = validate_payload_against_json_contract(payload, contract)

    assert validation.status == "pass"
    assert validation.errors == ()


def test_json_output_contract_writes_output_files(tmp_path):
    result = build_json_output_contract(output_dir=tmp_path)

    assert result.output_dir == str(tmp_path)
    assert (tmp_path / "json_output_contract.json").exists()
    assert (tmp_path / "json_output_contract.md").exists()
    payload = json.loads((tmp_path / "json_output_contract.json").read_text(encoding="utf-8"))
    assert payload["report_type"] == "json_output_contract"


def test_json_output_contract_docs_exist():
    assert Path("docs/json_output_contract.md").exists()


def test_cli_json_output_contract_json(tmp_path, capsys):
    exit_code = main(["json-output-contract", "--output-dir", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "json-output-contract"
    assert payload["status"] == "pass"
    assert payload["contract_count"] >= 15
    assert payload["ml_ready_for_project_use"] is False
    assert (tmp_path / "json_output_contract.json").exists()


def test_cli_json_output_contract_markdown(capsys):
    exit_code = main(["json-output-contract", "--markdown"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "JSON Output Contract" in output
    assert "ml_ready_for_project_use = false" in output
