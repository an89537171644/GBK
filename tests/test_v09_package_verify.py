import hashlib
import json
import zipfile
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import verify_v09_release_candidate_package
from sp63_core.workflows.protected_files_guard import run_protected_files_guard


def test_v09_package_verify_build_mode_creates_review_reports(tmp_path):
    output_dir = tmp_path / "verification"

    result = verify_v09_release_candidate_package(
        output_dir=output_dir,
        build=True,
        version="0.9.0-rc1",
    )

    assert result.status == "review_required"
    assert result.verification_status == "review_required"
    assert result.build_ran is True
    assert result.ready_for_manual_review is True
    assert result.ready_for_project_use is False
    assert result.ml_ready_for_project_use is False
    assert result.missing_required_paths == ()
    assert result.missing_zip_entries == ()
    assert result.forbidden_package_paths == ()
    assert result.forbidden_zip_entries == ()
    assert result.manual_review_gates
    assert (output_dir / "v09_package_verification.json").exists()
    assert (output_dir / "v09_package_verification.md").exists()
    assert (output_dir / "README_V09_PACKAGE_VERIFICATION.md").exists()
    assert (output_dir / "manual_acceptance_log_template.md").exists()


def test_v09_package_verify_existing_package_passes_review_required(tmp_path):
    package_dir = _make_minimal_package(tmp_path / "package")

    result = verify_v09_release_candidate_package(
        package_dir=package_dir,
        output_dir=tmp_path / "verification",
    )

    assert result.status == "review_required"
    assert result.ready_for_manual_review is True
    assert result.manual_review_gates[0]["gate_id"] == "manual_signoff"
    assert result.manifest_missing_files == ()


def test_v09_package_verify_missing_required_file_fails(tmp_path):
    package_dir = _make_minimal_package(tmp_path / "package")
    (package_dir / "README_RELEASE_CANDIDATE.md").unlink()

    result = verify_v09_release_candidate_package(
        package_dir=package_dir,
        output_dir=tmp_path / "verification",
    )

    assert result.status == "fail"
    assert result.ready_for_manual_review is False
    assert "README_RELEASE_CANDIDATE.md" in result.missing_required_paths


def test_v09_package_verify_forbidden_zip_entry_fails(tmp_path):
    package_dir = _make_minimal_package(tmp_path / "package")
    with zipfile.ZipFile(package_dir / "v09_release_candidate_package.zip", "a") as archive:
        archive.writestr("secrets/token.txt", "do not include")

    result = verify_v09_release_candidate_package(
        package_dir=package_dir,
        output_dir=tmp_path / "verification",
    )

    assert result.status == "fail"
    assert "secrets/token.txt" in result.forbidden_zip_entries


def test_v09_package_verify_manifest_checksum_mismatch_fails(tmp_path):
    package_dir = _make_minimal_package(tmp_path / "package")
    (package_dir / "README_START_HERE.md").write_text("changed\n", encoding="utf-8")

    result = verify_v09_release_candidate_package(
        package_dir=package_dir,
        output_dir=tmp_path / "verification",
    )

    assert result.status == "fail"
    assert "README_START_HERE.md" in result.manifest_checksum_mismatches


def test_cli_v09_package_verify_json(tmp_path, capsys):
    package_dir = _make_minimal_package(tmp_path / "package")
    output_dir = tmp_path / "verification"

    exit_code = main(
        [
            "v09-package-verify",
            "--package-dir",
            str(package_dir),
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "v09-package-verify"
    assert payload["status"] == "review_required"
    assert payload["ready_for_manual_review"] is True
    assert payload["ready_for_project_use"] is False
    assert payload["ml_ready_for_project_use"] is False


def test_cli_v09_package_verify_markdown(tmp_path, capsys):
    package_dir = _make_minimal_package(tmp_path / "package")

    exit_code = main(
        [
            "v09-package-verify",
            "--package-dir",
            str(package_dir),
            "--output-dir",
            str(tmp_path / "verification"),
            "--markdown",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "v0.9 Package Verification" in output
    assert "ready_for_project_use = false" in output


def test_v09_package_verify_docs_exist():
    assert Path("docs/v09_package_verification.md").exists()


def test_v09_package_verify_formula_files_not_touched():
    result = run_protected_files_guard(
        changed_files=("src/sp63_core/workflows/v09_package_verify.py",)
    )

    assert result.status == "pass"
    assert result.changed_protected_files == ()


def _make_minimal_package(package_dir: Path) -> Path:
    package_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "README_START_HERE.md": "# Start Here\n",
        "README_RELEASE_CANDIDATE.md": "# Release Candidate\n",
        "v09_release_candidate_package.json": json.dumps(
            {
                "report_type": "v09_release_candidate_package",
                "status": "review_required",
                "package_status": "review_required",
                "review_required_gates": (
                    {
                        "gate_id": "manual_signoff",
                        "status": "review_required",
                        "reason": "manual signoff remains open",
                    },
                ),
                "ready_for_project_use": False,
                "ml_ready_for_project_use": False,
            },
            indent=2,
        ),
        "v09_release_candidate_package.md": "# Package\n",
        "artifacts/clean_demo/workflow_summary.json": "{}\n",
        "artifacts/engineer_review_packet/engineer_review_packet.md": "# Engineer Packet\n",
        "artifacts/known_limitations/known_limitations_v0_9.md": "# Known Limitations\n",
        "artifacts/release_acceptance_checklist/release_acceptance_checklist.md": (
            "# Acceptance Checklist\n"
        ),
        "artifacts/signoff_templates/review_signoff_manifest.json": "{}\n",
    }
    for relative_path, content in files.items():
        path = package_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    manifest_path = package_dir / "v09_release_candidate_manifest.json"
    manifest_files = [
        {
            "relative_path": relative_path,
            "sha256": _sha256(package_dir / relative_path),
            "size_bytes": (package_dir / relative_path).stat().st_size,
        }
        for relative_path in sorted(files)
    ]
    manifest_path.write_text(
        json.dumps(
            {
                "report_type": "v09_release_candidate_manifest",
                "status": "review_required",
                "files": manifest_files,
                "ready_for_project_use": False,
                "ml_ready_for_project_use": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    with zipfile.ZipFile(
        package_dir / "v09_release_candidate_package.zip",
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for relative_path in sorted((*files, "v09_release_candidate_manifest.json")):
            archive.write(package_dir / relative_path, arcname=relative_path)
    return package_dir


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
