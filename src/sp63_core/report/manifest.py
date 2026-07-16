"""Manifest and checksum helpers for report bundles."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MANIFEST_VERSION = "2"


@dataclass(frozen=True)
class ReportArtifactManifest:
    """Reproducibility metadata for a generated report artifact bundle."""

    manifest_version: str
    report_type: str
    generated_at_utc: str
    command: str
    input_files: tuple[dict[str, Any], ...]
    output_files: tuple[dict[str, Any], ...]
    status: str
    strength_status: str | None
    serviceability_status: str | None
    overall_status: str | None
    warnings_count: int
    metadata: dict[str, Any] = field(default_factory=dict)
    completeness_status: str = "incomplete"
    evidence_status: str = "needs_engineer_review"
    project_use_status: str = "prohibited"
    project_use: bool = False
    requires_engineer_review: bool = True


def compute_file_sha256(path: Path) -> str:
    """Compute SHA256 checksum for a file."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_report_manifest(
    *,
    report_type: str,
    command: str,
    input_paths: Iterable[Path],
    output_paths: Iterable[Path],
    status: str,
    strength_status: str | None = None,
    serviceability_status: str | None = None,
    overall_status: str | None = None,
    warnings_count: int = 0,
    metadata: dict[str, Any] | None = None,
    completeness_status: str = "incomplete",
    evidence_status: str = "needs_engineer_review",
    project_use_status: str = "prohibited",
) -> ReportArtifactManifest:
    """Build manifest metadata for existing input and output files."""
    return ReportArtifactManifest(
        manifest_version=MANIFEST_VERSION,
        report_type=report_type,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        command=command,
        input_files=tuple(_file_record(path) for path in input_paths),
        output_files=tuple(_file_record(path) for path in output_paths),
        status=status,
        strength_status=strength_status,
        serviceability_status=serviceability_status,
        overall_status=overall_status,
        warnings_count=warnings_count,
        metadata={} if metadata is None else dict(metadata),
        completeness_status=completeness_status,
        evidence_status=evidence_status,
        project_use_status=project_use_status,
        project_use=False,
        requires_engineer_review=True,
    )


def write_report_manifest_json(
    manifest: ReportArtifactManifest,
    output_path: Path,
) -> None:
    """Write a report manifest as formatted JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(asdict(manifest), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def report_manifest_as_dict(manifest: ReportArtifactManifest) -> dict[str, Any]:
    """Return a JSON-ready manifest dictionary."""
    return asdict(manifest)


def _file_record(path: Path) -> dict[str, Any]:
    file_path = Path(path)
    return {
        "path": str(file_path),
        "sha256": compute_file_sha256(file_path),
        "size_bytes": file_path.stat().st_size,
    }
