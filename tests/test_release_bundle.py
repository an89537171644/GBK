import json
import zipfile
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_release_bundle


def test_release_bundle_creates_zip_manifest_and_report(tmp_path):
    result = build_release_bundle(output_dir=tmp_path, version="0.9.0-rc1")

    assert result.status == "pass"
    assert result.bundle_status == "pass"
    assert result.version == "0.9.0-rc1"
    assert result.zip_sha256 is not None
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert Path(result.zip_path).exists()
    assert Path(result.manifest_path).exists()
    assert Path(result.report_markdown_path).exists()


def test_release_bundle_zip_contains_expected_review_files(tmp_path):
    result = build_release_bundle(output_dir=tmp_path)

    with zipfile.ZipFile(result.zip_path) as archive:
        names = set(archive.namelist())

    assert "bundle/README.md" in names
    assert "bundle/CHANGELOG.md" in names
    assert "bundle/release_notes_v0_9.md" in names
    assert "bundle/known_limitations_v0_9.md" in names
    assert "bundle/RUN_COMMANDS.md" in names
    assert any(name.startswith("bundle/docs/user_manual/") for name in names)
    assert any(name.startswith("bundle/launcher_scripts/") for name in names)
    assert any(name.startswith("bundle/examples/project_template/") for name in names)


def test_release_bundle_manifest_has_sha256_and_no_forbidden_files(tmp_path):
    result = build_release_bundle(output_dir=tmp_path)
    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))

    assert manifest["report_type"] == "release_bundle_manifest"
    assert manifest["ml_ready_for_project_use"] is False
    assert manifest["file_count"] == result.file_count
    assert len(manifest["zip_sha256"]) == 64
    for file_info in manifest["files"]:
        relative_path = file_info["relative_path"].lower()
        assert len(file_info["sha256"]) == 64
        assert not relative_path.endswith((".exe", ".dll", ".bin"))
        assert "_smoke" not in relative_path


def test_release_bundle_docs_exist():
    assert Path("docs/release_bundle.md").exists()


def test_cli_release_bundle_json(tmp_path, capsys):
    exit_code = main(
        [
            "release-bundle",
            "--output-dir",
            str(tmp_path),
            "--version",
            "0.9.0-rc1",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "release-bundle"
    assert payload["status"] == "pass"
    assert payload["version"] == "0.9.0-rc1"
    assert payload["ml_ready_for_project_use"] is False
    assert Path(payload["zip_path"]).exists()
