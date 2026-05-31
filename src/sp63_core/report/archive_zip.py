"""ZIP export and validation helpers for report archives."""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

from sp63_core.report.archive_validation import (
    validate_batch_report_archive,
    validate_report_bundle,
)
from sp63_core.report.manifest import compute_file_sha256

ZIP_SKIP_FILENAMES = {"Thumbs.db", ".DS_Store", "desktop.ini"}
SINGLE_ZIP_REQUIRED_FILES = (
    "manifest.json",
    "README_REVIEW.md",
    "report.md",
    "report.json",
    "report.html",
    "input.json",
)
BATCH_ZIP_REQUIRED_FILES = ("manifest.json", "README_REVIEW.md", "index.md", "index.json")
CASE_ZIP_REQUIRED_FILES = ("manifest.json", "report.md", "report.json", "report.html", "input.json")


@dataclass(frozen=True)
class ReportArchiveZipResult:
    """Result of exporting or validating a report archive ZIP file."""

    status: str
    source_path: str
    zip_path: str
    file_count: int
    zip_sha256: str
    validation_status: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True


def export_report_archive_to_zip(
    *,
    source_path: Path,
    zip_path: Path,
    validate_before_zip: bool = True,
    validate_after_zip: bool = True,
) -> ReportArchiveZipResult:
    """Export a single or batch report archive directory into a ZIP file."""
    source = Path(source_path)
    output = Path(zip_path)
    warnings: list[str] = []
    errors: list[str] = []

    if not source.exists():
        errors.append(f"source archive path does not exist: {source}")
    elif not source.is_dir():
        errors.append(f"source archive path is not a directory: {source}")
    if errors:
        return _build_zip_result(
            source_path=source,
            zip_path=output,
            file_count=0,
            zip_sha256="",
            validation_status="not_checked",
            warnings=warnings,
            errors=errors,
        )

    if validate_before_zip:
        source_validation = (
            validate_batch_report_archive(source)
            if (source / "index.json").exists()
            else validate_report_bundle(source)
        )
        if source_validation.status != "pass":
            errors.extend(f"source validation: {error}" for error in source_validation.errors)
            return _build_zip_result(
                source_path=source,
                zip_path=output,
                file_count=0,
                zip_sha256="",
                validation_status=source_validation.status,
                warnings=warnings,
                errors=errors,
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    file_count = _write_archive_zip(source, output)
    zip_sha256 = compute_zip_sha256(output)

    validation_status = "not_checked"
    if validate_after_zip:
        zip_validation = validate_report_zip(output)
        validation_status = zip_validation.validation_status
        errors.extend(zip_validation.errors)
        warnings.extend(zip_validation.warnings)

    return _build_zip_result(
        source_path=source,
        zip_path=output,
        file_count=file_count,
        zip_sha256=zip_sha256,
        validation_status=validation_status,
        warnings=warnings,
        errors=errors,
    )


def compute_zip_sha256(path: Path) -> str:
    """Compute SHA256 checksum for a ZIP file."""
    return compute_file_sha256(Path(path))


def validate_report_zip(path: Path) -> ReportArchiveZipResult:
    """Validate a report archive ZIP without extracting it."""
    zip_path = Path(path)
    warnings: list[str] = []
    errors: list[str] = []
    entries: list[str] = []

    if not zip_path.exists():
        errors.append(f"ZIP path does not exist: {zip_path}")
        return _build_zip_result(
            source_path=Path(""),
            zip_path=zip_path,
            file_count=0,
            zip_sha256="",
            validation_status="fail",
            warnings=warnings,
            errors=errors,
        )

    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            bad_file = archive.testzip()
            if bad_file is not None:
                errors.append(f"ZIP internal CRC check failed for: {bad_file}")
            entries = [name for name in archive.namelist() if not name.endswith("/")]
    except zipfile.BadZipFile as exc:
        errors.append(f"invalid ZIP file: {exc}")

    for entry in entries:
        if _is_unsafe_zip_entry(entry):
            errors.append(f"unsafe ZIP entry path: {entry}")

    if entries:
        _validate_expected_zip_entries(entries, errors)
    elif not errors:
        errors.append("ZIP archive contains no files")

    validation_status = "fail" if errors else "pass"
    return _build_zip_result(
        source_path=Path(""),
        zip_path=zip_path,
        file_count=len(entries),
        zip_sha256=compute_zip_sha256(zip_path) if zip_path.exists() else "",
        validation_status=validation_status,
        warnings=warnings,
        errors=errors,
    )


def _write_archive_zip(source: Path, output: Path) -> int:
    file_count = 0
    output_resolved = output.resolve()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(source.rglob("*")):
            if not file_path.is_file():
                continue
            if _should_skip_file(file_path):
                continue
            if file_path.resolve() == output_resolved:
                continue
            archive_name = file_path.relative_to(source).as_posix()
            if _is_unsafe_zip_entry(archive_name):
                continue
            archive.write(file_path, archive_name)
            file_count += 1
    return file_count


def _should_skip_file(path: Path) -> bool:
    name = path.name
    return name in ZIP_SKIP_FILENAMES or name.endswith(".tmp") or name.endswith("~")


def _is_unsafe_zip_entry(name: str) -> bool:
    normalized = name.replace("\\", "/")
    posix_path = PurePosixPath(normalized)
    windows_path = PureWindowsPath(name)
    return (
        normalized.startswith("/")
        or posix_path.is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.drive)
        or any(part in {"", ".", ".."} for part in posix_path.parts)
    )


def _validate_expected_zip_entries(entries: list[str], errors: list[str]) -> None:
    entry_set = set(entries)
    if "manifest.json" not in entry_set:
        errors.append("ZIP archive must contain root manifest.json")
    if "index.json" in entry_set:
        _validate_required_entry_set(entry_set, BATCH_ZIP_REQUIRED_FILES, errors)
        case_dirs = sorted(
            {
                entry.split("/", 1)[0]
                for entry in entries
                if "/" in entry and entry.split("/", 1)[0].startswith("case_")
            }
        )
        if not case_dirs:
            errors.append("batch ZIP archive must contain case folders")
        for case_dir in case_dirs:
            expected = tuple(f"{case_dir}/{filename}" for filename in CASE_ZIP_REQUIRED_FILES)
            _validate_required_entry_set(entry_set, expected, errors)
    else:
        _validate_required_entry_set(entry_set, SINGLE_ZIP_REQUIRED_FILES, errors)


def _validate_required_entry_set(
    entry_set: set[str],
    required_entries: tuple[str, ...],
    errors: list[str],
) -> None:
    for required_entry in required_entries:
        if required_entry not in entry_set:
            errors.append(f"ZIP archive is missing required entry: {required_entry}")


def _build_zip_result(
    *,
    source_path: Path,
    zip_path: Path,
    file_count: int,
    zip_sha256: str,
    validation_status: str,
    warnings: list[str],
    errors: list[str],
) -> ReportArchiveZipResult:
    return ReportArchiveZipResult(
        status="fail" if errors else "pass",
        source_path=str(source_path),
        zip_path=str(zip_path),
        file_count=file_count,
        zip_sha256=zip_sha256,
        validation_status=validation_status,
        warnings=tuple(warnings),
        errors=tuple(errors),
        requires_engineer_review=True,
    )
