import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_docs_audit_report


def test_docs_audit_current_repository_passes_required_checks():
    result = build_docs_audit_report()

    assert result.status == "pass"
    assert result.docs_audit_status == "pass"
    assert result.markdown_files_count > 0
    assert result.required_files_missing == ()
    assert result.missing_local_links == ()
    assert result.required_commands_missing == ()
    assert result.requires_engineer_review is True
    assert result.ml_ready_for_project_use is False


def test_docs_audit_writes_json_and_markdown(tmp_path):
    result = build_docs_audit_report(output_dir=tmp_path)

    assert result.status == "pass"
    assert (tmp_path / "docs_audit_report.json").exists()
    assert (tmp_path / "docs_audit_report.md").exists()
    payload = json.loads((tmp_path / "docs_audit_report.json").read_text(encoding="utf-8"))
    assert payload["report_type"] == "docs_audit_report"
    assert payload["docs_audit_status"] == "pass"


def test_docs_audit_detects_missing_required_command_and_link(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (tmp_path / "README.md").write_text(
        "[Missing](docs/missing.md)\npython -m sp63_core validate --golden\n",
        encoding="utf-8",
    )

    result = build_docs_audit_report(
        root_dir=tmp_path,
        required_files=("README.md",),
        required_cli_examples=(
            "python -m sp63_core validate --golden",
            "python -m sp63_core project-template",
        ),
    )

    assert result.status == "fail"
    assert result.required_commands_missing == ("python -m sp63_core project-template",)
    assert result.missing_local_links


def test_cli_docs_audit_json(capsys):
    exit_code = main(["docs-audit", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "docs-audit"
    assert payload["status"] == "pass"
    assert payload["ml_ready_for_project_use"] is False


def test_docs_audit_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/docs_audit.py").read_text(encoding="utf-8")

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source
