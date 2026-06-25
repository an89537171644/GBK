import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import PROTECTED_FILES, run_protected_files_guard


def test_protected_files_guard_list_contains_required_files():
    assert "src/sp63_core/checks/bending.py" in PROTECTED_FILES
    assert "src/sp63_core/checks/shear.py" in PROTECTED_FILES
    assert "src/sp63_core/checks/cracking.py" in PROTECTED_FILES
    assert "src/sp63_core/checks/crack_width.py" in PROTECTED_FILES
    assert "src/sp63_core/checks/deflection.py" in PROTECTED_FILES
    assert "src/sp63_core/validation/external.py" in PROTECTED_FILES
    assert "src/sp63_core/materials/concrete.py" in PROTECTED_FILES
    assert "src/sp63_core/materials/rebar.py" in PROTECTED_FILES


def test_protected_files_guard_passes_with_no_changed_files():
    result = run_protected_files_guard(changed_files=())

    assert result.status == "pass"
    assert result.guard_status == "pass"
    assert result.changed_protected_files == ()
    assert result.requires_engineer_review is True


def test_protected_files_guard_fails_with_simulated_protected_change():
    result = run_protected_files_guard(
        changed_files=("src/sp63_core/checks/bending.py", "README.md")
    )

    assert result.status == "fail"
    assert result.guard_status == "fail"
    assert result.changed_protected_files == ("src/sp63_core/checks/bending.py",)
    assert result.errors


def test_protected_files_guard_records_github_actions_refs_with_base_ref():
    result = run_protected_files_guard(
        changed_files=("README.md",),
        env={"GITHUB_ACTIONS": "true", "GITHUB_BASE_REF": "main"},
    )

    assert result.status == "pass"
    assert result.github_actions_detected is True
    assert result.base_ref == "origin/main"
    assert result.head_ref == "HEAD"
    assert result.checked_git_ref == "provided_changed_files"


def test_protected_files_guard_records_github_actions_refs_without_base_ref():
    result = run_protected_files_guard(
        changed_files=("README.md",),
        env={"GITHUB_ACTIONS": "true"},
    )

    assert result.status == "pass"
    assert result.github_actions_detected is True
    assert result.base_ref == "origin/main"


def test_protected_files_guard_git_unavailable_is_review_required(tmp_path):
    result = run_protected_files_guard(repo_dir=tmp_path)

    assert result.status == "review_required"
    assert result.guard_status == "review_required"
    assert result.changed_protected_files == ()
    assert result.warnings


def test_cli_protected_files_check_json(capsys):
    exit_code = main(["protected-files-check", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "protected-files-check"
    assert payload["status"] in {"pass", "review_required"}
    assert "src/sp63_core/checks/bending.py" in payload["protected_files"]
    assert "base_ref" in payload
    assert "head_ref" in payload
    assert "github_actions_detected" in payload


def test_protected_files_guard_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/protected_files_guard.py").read_text(
        encoding="utf-8"
    )

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source
