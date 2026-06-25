import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_v09_review_build


def test_v09_review_build_generates_artifact_manifest(tmp_path):
    result = build_v09_review_build(output_dir=tmp_path, version="0.9.0-rc1")

    assert result.status in {"pass", "review_required"}
    assert result.review_build_status == result.status
    assert result.version == "0.9.0-rc1"
    assert result.artifact_count >= 12
    assert result.critical_failed_count == 0
    assert result.review_required_count >= 1
    assert result.project_use_allowed is False
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.ml_ready_for_project_use is False
    for path in result.generated_files:
        assert Path(path).exists()
    assert (tmp_path / "artifacts").exists()


def test_v09_review_build_contains_required_artifacts(tmp_path):
    result = build_v09_review_build(output_dir=tmp_path)
    artifacts = {item["name"]: item for item in result.artifact_items}

    for name in (
        "clean-demo-workflow",
        "clean-demo-verify",
        "portable-package",
        "release-bundle",
        "traceability-matrix",
        "v10-gap-report",
        "v09-freeze-report",
        "freeze-remediation-plan",
        "engineer-review-packet",
        "static-launcher-dashboard",
        "release-acceptance-checklist",
        "review-signoff-templates",
    ):
        assert name in artifacts


def test_v09_review_build_json_markdown_manifest(tmp_path):
    result = build_v09_review_build(output_dir=tmp_path)
    payload = json.loads(Path(result.summary_json_path).read_text(encoding="utf-8"))
    markdown = Path(result.summary_markdown_path).read_text(encoding="utf-8")
    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))

    assert payload["report_type"] == "v09_review_build"
    assert payload["project_use_allowed"] is False
    assert "v0.9 Review Build" in markdown
    assert manifest["report_type"] == "v09_review_build_manifest"
    assert manifest["ml_ready_for_project_use"] is False


def test_v09_review_build_docs_exist():
    assert Path("docs/v09_review_build.md").exists()
    assert Path("README.md").exists()


def test_cli_v09_review_build_json(tmp_path, capsys):
    exit_code = main(
        [
            "v09-review-build",
            "--output-dir",
            str(tmp_path),
            "--version",
            "0.9.0-rc1",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "v09-review-build"
    assert payload["status"] in {"pass", "review_required"}
    assert payload["critical_failed_count"] == 0
    assert payload["project_use_allowed"] is False
    assert (tmp_path / "v09_review_build.json").exists()
