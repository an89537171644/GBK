"""Integrity checks for generated report archives."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.report.ed01_contract import public_report_contract_errors
from sp63_core.report.manifest import MANIFEST_VERSION, compute_file_sha256

SINGLE_BUNDLE_REQUIRED_FILES = (
    "manifest.json",
    "README_REVIEW.md",
    "report.md",
    "report.json",
    "report.html",
    "input.json",
)
BATCH_ARCHIVE_REQUIRED_FILES = ("manifest.json", "README_REVIEW.md", "index.md", "index.json")
CASE_REQUIRED_FILES = ("manifest.json", "report.md", "report.json", "report.html", "input.json")
INDEX_CHECKSUM_FIELDS = {
    "input_sha256": "input.json",
    "report_json_sha256": "report.json",
    "report_markdown_sha256": "report.md",
    "report_html_sha256": "report.html",
}


@dataclass(frozen=True)
class ReportArchiveValidationResult:
    """Result of checking a single or batch report archive."""

    status: str
    archive_path: str
    manifest_count: int
    checked_file_count: int
    missing_file_count: int
    checksum_mismatch_count: int
    index_consistency_status: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    completeness_status: str = "incomplete"
    evidence_status: str = "needs_engineer_review"
    project_use_status: str = "prohibited"
    project_use: bool = False
    requires_engineer_review: bool = True


@dataclass
class _ArchiveValidationCounters:
    manifest_count: int = 0
    checked_file_count: int = 0
    missing_file_count: int = 0
    checksum_mismatch_count: int = 0

    def add(self, other: _ArchiveValidationCounters) -> None:
        self.manifest_count += other.manifest_count
        self.checked_file_count += other.checked_file_count
        self.missing_file_count += other.missing_file_count
        self.checksum_mismatch_count += other.checksum_mismatch_count


def validate_report_bundle(path: Path) -> ReportArchiveValidationResult:
    """Validate one report bundle created by ``design-report --bundle-output``."""
    archive_path = Path(path)
    errors: list[str] = []
    warnings: list[str] = []
    counters = _ArchiveValidationCounters()

    if not archive_path.exists():
        errors.append(f"archive path does not exist: {archive_path}")
    elif not archive_path.is_dir():
        errors.append(f"archive path is not a directory: {archive_path}")

    if errors:
        return _build_result(
            archive_path=archive_path,
            counters=counters,
            index_consistency_status="not_checked",
            warnings=warnings,
            errors=errors,
        )

    manifest_path = archive_path / "manifest.json"
    manifest = _load_manifest(manifest_path, errors)
    if manifest is None:
        counters.missing_file_count += 1
        return _build_result(
            archive_path=archive_path,
            counters=counters,
            index_consistency_status="not_checked",
            warnings=warnings,
            errors=errors,
        )

    counters.manifest_count += 1
    _validate_required_files(archive_path, SINGLE_BUNDLE_REQUIRED_FILES, counters, errors)
    counters.add(_validate_manifest_records(manifest, archive_path, manifest_path, errors))
    _validate_manifest_review_flag(manifest, manifest_path, errors)
    _validate_report_ed01_contract(archive_path / "report.json", errors)

    return _build_result(
        archive_path=archive_path,
        counters=counters,
        index_consistency_status="pass",
        warnings=warnings,
        errors=errors,
    )


def validate_batch_report_archive(path: Path) -> ReportArchiveValidationResult:
    """Validate a batch archive created by ``design-report-batch``."""
    archive_path = Path(path)
    errors: list[str] = []
    warnings: list[str] = []
    counters = _ArchiveValidationCounters()

    if not archive_path.exists():
        errors.append(f"archive path does not exist: {archive_path}")
    elif not archive_path.is_dir():
        errors.append(f"archive path is not a directory: {archive_path}")

    if errors:
        return _build_result(
            archive_path=archive_path,
            counters=counters,
            index_consistency_status="not_checked",
            warnings=warnings,
            errors=errors,
        )

    _validate_required_files(archive_path, BATCH_ARCHIVE_REQUIRED_FILES, counters, errors)

    root_manifest_path = archive_path / "manifest.json"
    root_manifest = _load_manifest(root_manifest_path, errors)
    if root_manifest is not None:
        counters.manifest_count += 1
        counters.add(
            _validate_manifest_records(root_manifest, archive_path, root_manifest_path, errors)
        )
        _validate_manifest_review_flag(root_manifest, root_manifest_path, errors)

    index_path = archive_path / "index.json"
    index = _load_json_file(index_path, errors)
    index_errors_before = len(errors)
    if index is None:
        return _build_result(
            archive_path=archive_path,
            counters=counters,
            index_consistency_status="fail",
            warnings=warnings,
            errors=errors,
        )

    cases = index.get("cases")
    if not isinstance(cases, list):
        errors.append("index.json must contain a list field: cases")
        cases = []

    indexed_case_dirs: set[Path] = set()
    for case in cases:
        if not isinstance(case, dict):
            errors.append("index.json cases must be objects")
            continue
        case_id = str(case.get("case_id") or "<missing_case_id>")
        case_manifest_path = _resolve_archive_reference(
            case.get("manifest_path"),
            archive_path,
        )
        if case_manifest_path is None or not case_manifest_path.exists():
            counters.missing_file_count += 1
            errors.append(f"{case_id}: manifest_path is missing or does not exist")
            continue
        case_manifest_path = case_manifest_path.resolve()
        if not _is_within(case_manifest_path, archive_path):
            errors.append(f"{case_id}: manifest_path escapes archive folder")
            continue

        case_dir = case_manifest_path.parent
        indexed_case_dirs.add(case_dir)
        _validate_required_files(case_dir, CASE_REQUIRED_FILES, counters, errors, prefix=case_id)
        case_manifest = _load_manifest(case_manifest_path, errors, label=f"{case_id} manifest")
        if case_manifest is not None:
            counters.manifest_count += 1
            counters.add(
                _validate_manifest_records(case_manifest, case_dir, case_manifest_path, errors)
            )
            _validate_manifest_review_flag(case_manifest, case_manifest_path, errors)
        _validate_index_case_checksums(case, case_dir, counters, errors, case_id)
        _validate_report_ed01_contract(
            case_dir / "report.json",
            errors,
            label=f"{case_id} report",
        )

    actual_case_dirs = {
        item.resolve()
        for item in archive_path.iterdir()
        if item.is_dir() and (item / "manifest.json").exists()
    }
    if len(cases) != len(actual_case_dirs):
        errors.append(
            "index.json case count does not match actual case folders with manifests: "
            f"{len(cases)} != {len(actual_case_dirs)}"
        )
    if indexed_case_dirs != actual_case_dirs:
        errors.append("index.json case manifest paths do not match actual case folders")

    index_consistency_status = "pass" if len(errors) == index_errors_before else "fail"
    return _build_result(
        archive_path=archive_path,
        counters=counters,
        index_consistency_status=index_consistency_status,
        warnings=warnings,
        errors=errors,
    )


def _load_manifest(
    manifest_path: Path,
    errors: list[str],
    *,
    label: str = "manifest",
) -> dict[str, Any] | None:
    if not manifest_path.exists():
        errors.append(f"missing {label}: {manifest_path}")
        return None
    manifest = _load_json_file(manifest_path, errors)
    if manifest is None:
        return None
    if not isinstance(manifest, dict):
        errors.append(f"{label} must be a JSON object: {manifest_path}")
        return None
    return manifest


def _load_json_file(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
        return None
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON file {path}: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"JSON file must contain an object: {path}")
        return None
    return payload


def _validate_report_ed01_contract(
    report_path: Path,
    errors: list[str],
    *,
    label: str = "report",
) -> None:
    report = _load_json_file(report_path, errors)
    if report is None:
        return
    errors.extend(
        f"{label} ED-01 contract: {error}"
        for error in public_report_contract_errors(report)
    )


def _validate_required_files(
    directory: Path,
    filenames: tuple[str, ...],
    counters: _ArchiveValidationCounters,
    errors: list[str],
    *,
    prefix: str | None = None,
) -> None:
    for filename in filenames:
        required_path = directory / filename
        if not required_path.exists():
            counters.missing_file_count += 1
            subject = f"{prefix}: " if prefix else ""
            errors.append(f"{subject}missing required archive file: {required_path}")


def _validate_manifest_records(
    manifest: dict[str, Any],
    archive_path: Path,
    manifest_path: Path,
    errors: list[str],
) -> _ArchiveValidationCounters:
    counters = _ArchiveValidationCounters()
    for field_name in ("input_files", "output_files"):
        records = manifest.get(field_name)
        if not isinstance(records, list):
            errors.append(f"{manifest_path}: {field_name} must be a list")
            continue
        for record in records:
            if not isinstance(record, dict):
                errors.append(f"{manifest_path}: {field_name} records must be objects")
                continue
            counters.add(
                _validate_manifest_file_record(record, archive_path, manifest_path, errors)
            )
    return counters


def _validate_manifest_file_record(
    record: dict[str, Any],
    archive_path: Path,
    manifest_path: Path,
    errors: list[str],
) -> _ArchiveValidationCounters:
    counters = _ArchiveValidationCounters()
    stored_path = record.get("path")
    expected_sha = record.get("sha256")
    if not isinstance(stored_path, str) or not stored_path:
        errors.append(f"{manifest_path}: file record has empty path")
        return counters
    if not isinstance(expected_sha, str) or not expected_sha:
        errors.append(f"{manifest_path}: file record for {stored_path} has empty sha256")
        return counters

    actual_path = _resolve_archive_reference(stored_path, archive_path)
    if actual_path is None or not actual_path.exists():
        counters.missing_file_count += 1
        errors.append(f"{manifest_path}: missing manifest file record: {stored_path}")
        return counters

    counters.checked_file_count += 1
    actual_sha = compute_file_sha256(actual_path)
    if actual_sha != expected_sha:
        counters.checksum_mismatch_count += 1
        errors.append(f"{manifest_path}: checksum mismatch for {stored_path}")
    return counters


def _validate_manifest_review_flag(
    manifest: dict[str, Any],
    manifest_path: Path,
    errors: list[str],
) -> None:
    if manifest.get("manifest_version") != MANIFEST_VERSION:
        errors.append(
            f"{manifest_path}: manifest_version must be {MANIFEST_VERSION!r}"
        )
    if manifest.get("completeness_status") != "incomplete":
        errors.append(f"{manifest_path}: completeness_status must be 'incomplete'")
    if manifest.get("evidence_status") != "needs_engineer_review":
        errors.append(
            f"{manifest_path}: evidence_status must be 'needs_engineer_review'"
        )
    if manifest.get("project_use_status") != "prohibited":
        errors.append(f"{manifest_path}: project_use_status must be 'prohibited'")
    if manifest.get("project_use") is not False:
        errors.append(f"{manifest_path}: project_use must be false")
    if manifest.get("requires_engineer_review") is not True:
        errors.append(f"{manifest_path}: requires_engineer_review must be true")


def _validate_index_case_checksums(
    case: dict[str, Any],
    case_dir: Path,
    counters: _ArchiveValidationCounters,
    errors: list[str],
    case_id: str,
) -> None:
    for field_name, filename in INDEX_CHECKSUM_FIELDS.items():
        expected_sha = case.get(field_name)
        if expected_sha is None:
            continue
        if not isinstance(expected_sha, str) or not expected_sha:
            errors.append(f"{case_id}: {field_name} must be a non-empty string or null")
            continue
        artifact_path = case_dir / filename
        if not artifact_path.exists():
            counters.missing_file_count += 1
            errors.append(f"{case_id}: indexed artifact is missing: {artifact_path}")
            continue
        counters.checked_file_count += 1
        actual_sha = compute_file_sha256(artifact_path)
        if actual_sha != expected_sha:
            counters.checksum_mismatch_count += 1
            errors.append(f"{case_id}: index checksum mismatch for {filename}")


def _resolve_archive_reference(value: Any, archive_path: Path) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    stored_path = Path(value)
    candidates = [stored_path] if stored_path.is_absolute() else [
        Path.cwd() / stored_path,
        archive_path / stored_path,
        archive_path / stored_path.name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0] if candidates else None


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _build_result(
    *,
    archive_path: Path,
    counters: _ArchiveValidationCounters,
    index_consistency_status: str,
    warnings: list[str],
    errors: list[str],
) -> ReportArchiveValidationResult:
    return ReportArchiveValidationResult(
        status="fail" if errors else "pass",
        archive_path=str(archive_path),
        manifest_count=counters.manifest_count,
        checked_file_count=counters.checked_file_count,
        missing_file_count=counters.missing_file_count,
        checksum_mismatch_count=counters.checksum_mismatch_count,
        index_consistency_status=index_consistency_status,
        warnings=tuple(warnings),
        errors=tuple(errors),
        requires_engineer_review=True,
    )
