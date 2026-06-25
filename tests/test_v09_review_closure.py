import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_v09_review_closure
from sp63_core.workflows.protected_files_guard import run_protected_files_guard
from sp63_core.workflows.v09_review_closure import _classify_v09_review_closure


def test_v09_review_closure_generates_json_markdown_and_readme(tmp_path):
    result = build_v09_review_closure(output_dir=tmp_path, version="0.9.0-rc1")

    assert result.status in {"pass", "review_required"}
    assert result.closure_status == result.status
    assert result.ready_for_project_use is False
    assert result.ml_ready_for_project_use is False
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ready_for_v09_review_build is True
    assert result.acceptable_review_gates
    for path in result.generated_files:
        assert Path(path).exists()

    payload = json.loads(Path(result.summary_json_path).read_text(encoding="utf-8"))
    markdown = Path(result.summary_markdown_path).read_text(encoding="utf-8")
    readme = Path(result.readme_path).read_text(encoding="utf-8")
    assert payload["report_type"] == "v09_review_closure"
    assert payload["ready_for_project_use"] is False
    assert "v0.9 Review Closure" in markdown
    assert "ml_ready_for_project_use = false" in markdown
    assert "README v0.9 Review Closure" in readme


def test_v09_review_closure_failure_classification():
    state = _classify_v09_review_closure(
        checked_artifacts=(
            {
                "name": "protected-files-check",
                "status": "fail",
                "critical": True,
                "path": None,
            },
        ),
        acceptable_review_gates=(),
        release_bundle_present=True,
        clean_demo_pass=True,
        clean_demo_verify_pass=True,
        protected_pass=False,
        docs_pass=True,
        known_limitations_documented=True,
    )

    assert state["status"] == "fail"
    assert state["critical_failures"] == ("critical artifact failed: protected-files-check",)
    assert state["ready_for_v09_review_build"] is False


def test_v09_review_closure_review_required_classification():
    state = _classify_v09_review_closure(
        checked_artifacts=(
            {"name": "protected-files-check", "status": "pass", "critical": True, "path": None},
        ),
        acceptable_review_gates=(
            {"gate_id": "material_engineer_review", "status": "review_required"},
        ),
        release_bundle_present=True,
        clean_demo_pass=True,
        clean_demo_verify_pass=True,
        protected_pass=True,
        docs_pass=True,
        known_limitations_documented=True,
    )

    assert state["status"] == "review_required"
    assert state["critical_failures"] == ()
    assert state["ready_for_v09_review_build"] is True
    assert state["ready_for_v09_release_candidate"] is True


def test_v09_review_closure_formula_files_not_touched():
    result = run_protected_files_guard(
        changed_files=("src/sp63_core/workflows/v09_review_closure.py",)
    )

    assert result.status == "pass"
    assert result.changed_protected_files == ()


def test_cli_v09_review_closure_json(tmp_path, capsys):
    exit_code = main(
        [
            "v09-review-closure",
            "--output-dir",
            str(tmp_path),
            "--version",
            "0.9.0-rc1",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "v09-review-closure"
    assert payload["status"] in {"pass", "review_required"}
    assert payload["ready_for_project_use"] is False
    assert payload["ml_ready_for_project_use"] is False
    assert (tmp_path / "v09_review_closure.json").exists()


def test_cli_v09_review_closure_markdown(tmp_path, capsys):
    exit_code = main(["v09-review-closure", "--output-dir", str(tmp_path), "--markdown"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "v0.9 Review Closure" in output
    assert "ready_for_project_use = false" in output
