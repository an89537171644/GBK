import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_release_artifact_manifest


def test_release_manifest_creates_metadata_files(tmp_path):
    result = build_release_artifact_manifest(output_dir=tmp_path, version="0.9.0-rc1")

    assert result.status == "pass"
    assert result.manifest_status == "pass"
    assert result.version == "0.9.0-rc1"
    assert result.artifact_count > 0
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.ml_ready_for_project_use is False
    assert (tmp_path / "release_artifact_manifest.json").exists()
    assert (tmp_path / "release_artifact_manifest.md").exists()
    assert (tmp_path / "VERSION.txt").read_text(encoding="utf-8").strip() == "0.9.0-rc1"


def test_release_manifest_json_contains_artifact_sha256(tmp_path):
    build_release_artifact_manifest(output_dir=tmp_path)

    payload = json.loads(
        (tmp_path / "release_artifact_manifest.json").read_text(encoding="utf-8")
    )

    assert payload["report_type"] == "release_artifact_manifest"
    assert payload["ml_ready_for_project_use"] is False
    assert payload["artifacts"]
    assert all(len(artifact["sha256"]) == 64 for artifact in payload["artifacts"])
    assert any(artifact["path"] == "README.md" for artifact in payload["artifacts"])


def test_release_manifest_missing_artifact_fails(tmp_path):
    result = build_release_artifact_manifest(
        output_dir=tmp_path,
        artifact_paths=("README.md", "docs/does_not_exist.md"),
    )

    assert result.status == "fail"
    assert result.errors


def test_cli_release_manifest_json(tmp_path, capsys):
    output_dir = tmp_path / "release_manifest"

    exit_code = main(
        [
            "release-manifest",
            "--output-dir",
            str(output_dir),
            "--version",
            "0.9.0-rc1",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "release-manifest"
    assert payload["status"] == "pass"
    assert payload["version"] == "0.9.0-rc1"
    assert payload["ml_ready_for_project_use"] is False
    assert (output_dir / "release_artifact_manifest.json").exists()


def test_cli_release_manifest_markdown(tmp_path, capsys):
    exit_code = main(
        [
            "release-manifest",
            "--output-dir",
            str(tmp_path / "release_manifest_markdown"),
            "--markdown",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "# Release Artifact Manifest" in output
    assert "ml_ready_for_project_use = false" in output


def test_release_manifest_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/release_manifest.py").read_text(
        encoding="utf-8"
    )

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source
