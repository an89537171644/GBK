import json

from sp63_core.cli import main
from sp63_core.workflows import SprintStepSpec, build_agent_sprint_guard


def test_agent_sprint_guard_passes_when_required_paths_exist(tmp_path):
    for relative_path in ("a.txt", "b.txt"):
        path = tmp_path / relative_path
        path.write_text("ok", encoding="utf-8")
    specs = (
        SprintStepSpec(k=1, title="one", required_paths=("a.txt",)),
        SprintStepSpec(k=2, title="two", required_paths=("b.txt",)),
    )

    result = build_agent_sprint_guard(
        from_k=1,
        to_k=2,
        root_dir=tmp_path,
        step_specs=specs,
    )

    assert result.status == "pass"
    assert result.completed_steps == (1, 2)
    assert result.missing_steps == ()
    assert result.proposed_next_k is None
    assert result.requires_engineer_review is True
    assert result.ml_ready_for_project_use is False


def test_agent_sprint_guard_reports_first_missing_k(tmp_path):
    (tmp_path / "a.txt").write_text("ok", encoding="utf-8")
    specs = (
        SprintStepSpec(k=1, title="one", required_paths=("a.txt",)),
        SprintStepSpec(k=2, title="two", required_paths=("b.txt",)),
        SprintStepSpec(k=3, title="three", required_paths=("c.txt",)),
    )

    result = build_agent_sprint_guard(
        from_k=1,
        to_k=3,
        root_dir=tmp_path,
        step_specs=specs,
    )

    assert result.status == "review_required"
    assert result.completed_steps == (1,)
    assert result.missing_count == 2
    assert result.proposed_next_k == 2
    assert result.missing_steps[0]["missing_paths"] == ("b.txt",)


def test_agent_sprint_guard_rejects_invalid_range():
    result = build_agent_sprint_guard(from_k=90, to_k=83)

    assert result.status == "fail"
    assert result.errors == ("from_k must be less than or equal to to_k",)


def test_cli_agent_sprint_guard_json(capsys):
    exit_code = main(["agent-sprint-guard", "--from-k", "83", "--to-k", "90", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "agent-sprint-guard"
    assert payload["status"] in {"pass", "review_required"}
    assert payload["from_k"] == 83
    assert payload["to_k"] == 90
    assert payload["requires_engineer_review"] is True
    assert payload["ml_ready_for_project_use"] is False
