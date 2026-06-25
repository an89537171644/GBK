import json
import shutil
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import REQUIRED_USER_MANUAL_FILES, build_user_manual_index

MANUAL_DIR = Path("docs/user_manual")


def test_user_manual_files_exist():
    result = build_user_manual_index()

    assert result.status == "pass"
    assert result.manual_status == "pass"
    assert result.missing_files == ()
    assert set(result.existing_files) == set(REQUIRED_USER_MANUAL_FILES)
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False


def test_user_manual_index_output_dir_writes_json_and_markdown(tmp_path):
    output_dir = tmp_path / "manual_index"

    result = build_user_manual_index(output_dir=output_dir)

    payload = json.loads((output_dir / "user_manual_index.json").read_text(encoding="utf-8"))
    markdown = (output_dir / "user_manual_index.md").read_text(encoding="utf-8")
    assert result.status == "pass"
    assert payload["report_type"] == "user_manual_index"
    assert payload["manual_status"] == "pass"
    assert "# User Manual Index" in markdown
    assert "ml_ready_for_project_use = false" in markdown


def test_user_manual_index_missing_file_is_fail(tmp_path):
    manual_copy = tmp_path / "manual"
    shutil.copytree(MANUAL_DIR, manual_copy)
    (manual_copy / "quickstart.md").unlink()

    result = build_user_manual_index(manual_dir=manual_copy)

    assert result.status == "fail"
    assert result.manual_status == "fail"
    assert result.missing_files == ("quickstart.md",)
    assert result.errors


def test_cli_user_manual_index_json(capsys):
    exit_code = main(["user-manual-index", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "user-manual-index"
    assert payload["status"] == "pass"
    assert payload["missing_files"] == []
    assert payload["ml_ready_for_project_use"] is False


def test_cli_user_manual_index_markdown(capsys):
    exit_code = main(["user-manual-index", "--markdown"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "# User Manual Index" in output
    assert "quickstart.md" in output


def test_user_manual_index_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/user_manual_index.py").read_text(
        encoding="utf-8"
    )

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source
