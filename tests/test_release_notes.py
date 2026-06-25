import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_release_notes_package


def test_release_notes_package_writes_expected_files(tmp_path):
    output_dir = tmp_path / "release_notes"

    result = build_release_notes_package(output_dir=output_dir, version="0.9.0-rc1")

    assert result.status == "pass"
    assert result.package_status == "pass"
    assert result.version == "0.9.0-rc1"
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    for path_text in (
        result.release_notes_json_path,
        result.release_notes_markdown_path,
        result.release_checklist_path,
        result.known_limitations_path,
    ):
        assert Path(path_text).exists()


def test_release_notes_content_includes_k83_k90_and_limitations(tmp_path):
    output_dir = tmp_path / "release_notes_content"

    result = build_release_notes_package(output_dir=output_dir)
    markdown = Path(result.release_notes_markdown_path).read_text(encoding="utf-8")
    limitations = Path(result.known_limitations_path).read_text(encoding="utf-8")

    assert "K83 material verification closure workflow" in markdown
    assert "K90 release notes package" in markdown
    assert "ml_ready_for_project_use = false" in markdown
    assert "real external validation" in limitations
    assert "ML and neural surrogate outputs are advisory-only" in limitations


def test_release_notes_docs_exist():
    for path in (
        Path("CHANGELOG.md"),
        Path("docs/release_notes_v0_9.md"),
        Path("docs/v09_release_checklist.md"),
        Path("docs/known_limitations_v0_9.md"),
    ):
        assert path.exists()


def test_cli_release_notes_json(tmp_path, capsys):
    output_dir = tmp_path / "release_notes_cli"

    exit_code = main(
        [
            "release-notes",
            "--output-dir",
            str(output_dir),
            "--version",
            "0.9.0-rc1",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "release-notes"
    assert payload["status"] == "pass"
    assert payload["version"] == "0.9.0-rc1"
    assert payload["requires_engineer_review"] is True
    assert payload["ml_ready_for_project_use"] is False
    assert Path(payload["release_notes_markdown_path"]).exists()
