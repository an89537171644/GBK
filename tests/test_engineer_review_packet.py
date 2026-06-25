import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_engineer_review_packet


def test_engineer_review_packet_builds_evidence_index(tmp_path):
    result = build_engineer_review_packet(output_dir=tmp_path)

    assert result.status in {"pass", "review_required"}
    assert result.packet_status == result.status
    assert result.evidence_count >= 9
    assert result.review_required_count >= 1
    assert result.failed_count == 0
    assert result.project_use_allowed is False
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    for path in result.generated_files:
        assert Path(path).exists()


def test_engineer_review_packet_contains_required_evidence(tmp_path):
    result = build_engineer_review_packet(output_dir=tmp_path)
    evidence = {item["name"]: item for item in result.evidence_items}

    for name in (
        "v09-freeze-report",
        "v09-final-audit",
        "v10-gap-report",
        "material-verification-closure",
        "external-validation-evidence-package",
        "traceability-matrix",
        "clean-demo-verification",
        "release-notes",
        "known-limitations",
        "acceptance-checklist",
    ):
        assert name in evidence


def test_engineer_review_packet_json_markdown_and_manifest(tmp_path):
    result = build_engineer_review_packet(output_dir=tmp_path)
    payload = json.loads(Path(result.packet_json_path).read_text(encoding="utf-8"))
    markdown = Path(result.packet_markdown_path).read_text(encoding="utf-8")
    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))

    assert payload["report_type"] == "engineer_review_packet"
    assert payload["project_use_allowed"] is False
    assert "Engineer Review Packet" in markdown
    assert manifest["report_type"] == "engineer_review_packet_manifest"
    assert manifest["ml_ready_for_project_use"] is False


def test_engineer_review_packet_docs_exist():
    assert Path("docs/engineer_review_packet.md").exists()
    assert Path("docs/user_manual/acceptance_checklist.md").exists()


def test_cli_engineer_review_packet_json(tmp_path, capsys):
    exit_code = main(["engineer-review-packet", "--output-dir", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "engineer-review-packet"
    assert payload["status"] in {"pass", "review_required"}
    assert payload["project_use_allowed"] is False
    assert (tmp_path / "README_ENGINEER_REVIEW.md").exists()
