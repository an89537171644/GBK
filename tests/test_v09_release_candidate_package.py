import json
import zipfile
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import (
    V09ReleaseCandidatePackageResult,
    build_v09_release_candidate_package,
)
from sp63_core.workflows.protected_files_guard import run_protected_files_guard
from sp63_core.workflows.v09_release_candidate_package import _package_status


def test_v09_release_candidate_package_builds_review_package(tmp_path):
    result = build_v09_release_candidate_package(output_dir=tmp_path, version="0.9.0-rc1")

    assert result.status == "review_required"
    assert result.package_status == "review_required"
    assert result.critical_failures == ()
    assert result.review_required_gates
    assert result.ready_for_engineering_review is True
    assert result.ready_for_project_use is False
    assert result.ml_ready_for_project_use is False
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert Path(result.start_here_path).exists()
    assert Path(result.readme_path).exists()
    assert Path(result.manifest_path).exists()
    assert Path(result.zip_path).exists()

    for folder_name in (
        "review_closure",
        "review_build",
        "freeze_report",
        "final_audit",
        "clean_demo",
        "engineer_review_packet",
        "release_acceptance_checklist",
        "signoff_templates",
        "windows_smoke_plan",
        "release_notes",
        "known_limitations",
        "release_bundle",
    ):
        assert (tmp_path / "artifacts" / folder_name).exists()


def test_v09_release_candidate_package_manifest_and_zip_are_safe(tmp_path):
    result = build_v09_release_candidate_package(output_dir=tmp_path, version="0.9.0-rc1")
    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))

    manifest_paths = {file_item["relative_path"] for file_item in manifest["files"]}
    assert "README_START_HERE.md" in manifest_paths
    assert "README_RELEASE_CANDIDATE.md" in manifest_paths
    assert "v09_release_candidate_package.json" in manifest_paths
    assert "v09_release_candidate_package.md" in manifest_paths

    with zipfile.ZipFile(result.zip_path) as archive:
        names = archive.namelist()

    assert "README_START_HERE.md" in names
    assert "README_RELEASE_CANDIDATE.md" in names
    assert "v09_release_candidate_manifest.json" in names
    assert not any(part.endswith("_smoke") for name in names for part in Path(name).parts)
    lowered_names = [name.lower() for name in names]
    assert not any("full_sp63" in name or "sp63_full" in name for name in lowered_names)
    assert not any("passport" in name or "snils" in name for name in lowered_names)
    assert not any("grant" in name or "private" in name for name in lowered_names)
    assert not any("scad" in name or "lira" in name for name in lowered_names)
    assert not any(
        name.endswith((".pdf", ".doc", ".docx", ".dwg", ".ifc")) for name in lowered_names
    )


def test_v09_release_candidate_package_status_rules():
    assert (
        _package_status(
            critical_failures=(),
            review_required_gates=({"gate_id": "manual_review"},),
        )
        == "review_required"
    )
    assert (
        _package_status(
            critical_failures=("critical artifact failed",),
            review_required_gates=(),
        )
        == "fail"
    )
    assert _package_status(critical_failures=(), review_required_gates=()) == "pass"


def test_v09_release_candidate_package_formula_files_not_touched():
    result = run_protected_files_guard(
        changed_files=("src/sp63_core/workflows/v09_release_candidate_package.py",)
    )

    assert result.status == "pass"
    assert result.changed_protected_files == ()


def test_cli_v09_release_candidate_package_json(monkeypatch, tmp_path, capsys):
    fake_result = _fake_release_candidate_result(tmp_path)

    monkeypatch.setattr(
        "sp63_core.cli.build_v09_release_candidate_package",
        lambda **_: fake_result,
    )
    exit_code = main(
        [
            "v09-release-candidate-package",
            "--output-dir",
            str(tmp_path),
            "--version",
            "0.9.0-rc1",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "v09-release-candidate-package"
    assert payload["status"] == "review_required"
    assert payload["ready_for_project_use"] is False
    assert payload["ml_ready_for_project_use"] is False


def test_cli_v09_release_candidate_package_markdown(monkeypatch, tmp_path, capsys):
    fake_result = _fake_release_candidate_result(tmp_path)

    monkeypatch.setattr(
        "sp63_core.cli.build_v09_release_candidate_package",
        lambda **_: fake_result,
    )
    exit_code = main(
        [
            "v09-release-candidate-package",
            "--output-dir",
            str(tmp_path),
            "--version",
            "0.9.0-rc1",
            "--markdown",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "v0.9 Release Candidate Package" in output
    assert "ready_for_project_use = false" in output


def _fake_release_candidate_result(tmp_path: Path) -> V09ReleaseCandidatePackageResult:
    return V09ReleaseCandidatePackageResult(
        status="review_required",
        package_status="review_required",
        output_dir=str(tmp_path),
        version="0.9.0-rc1",
        package_root=str(tmp_path),
        generated_files=(),
        included_artifacts=(
            {
                "name": "review_closure",
                "status": "review_required",
                "critical": True,
                "path": str(tmp_path / "review_closure"),
            },
        ),
        manifest_path=str(tmp_path / "v09_release_candidate_manifest.json"),
        readme_path=str(tmp_path / "README_RELEASE_CANDIDATE.md"),
        start_here_path=str(tmp_path / "README_START_HERE.md"),
        zip_path=str(tmp_path / "v09_release_candidate_package.zip"),
        critical_failures=(),
        review_required_gates=(
            {
                "gate_id": "material_engineer_review",
                "status": "review_required",
                "reason": "manual review remains open",
            },
        ),
        ready_for_engineering_review=True,
        ready_for_project_use=False,
        warnings=("review package only",),
        errors=(),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
