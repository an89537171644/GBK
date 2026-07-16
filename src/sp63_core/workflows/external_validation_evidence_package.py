"""External validation evidence package for engineering review."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from sp63_core.validation.external_report import (
    ExternalValidationSummary,
    build_external_validation_summary,
    load_external_validation_csv,
)

EXTERNAL_EVIDENCE_WARNING = (
    "External validation evidence package is a review scaffold only. Real "
    "manual, Excel, SCAD, or LIRA values must be filled by an engineer."
)
NO_EXTERNAL_CSV_WARNING = (
    "external validation CSV was not provided; package remains review_required"
)
EXTERNAL_TEMPLATE_SOURCE = Path(
    "docs/validation/templates/external_validation_engineer_input_template.csv"
)
EXTERNAL_CHECKLIST_SOURCE = Path("docs/validation/external_validation_engineer_checklist.md")


@dataclass(frozen=True)
class ExternalValidationEvidencePackageResult:
    """Result of creating an external validation evidence package."""

    status: str
    evidence_status: str
    output_dir: str
    generated_files: tuple[str, ...]
    template_path: str
    checklist_path: str
    summary_json_path: str
    summary_markdown_path: str
    manifest_path: str
    source_csv_path: str | None
    strict_mode: bool
    total_cases: int
    accepted_cases: int
    review_cases: int
    failed_cases: int
    missing_external_values_count: int
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_external_validation_evidence_package(
    *,
    output_dir: Path,
    external_validation_csv: Path | None = None,
    strict_mode: bool = True,
) -> ExternalValidationEvidencePackageResult:
    """Create external validation evidence templates and optional CSV summary."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    template_path = output_path / "external_validation_engineer_input_template.csv"
    checklist_path = output_path / "external_validation_engineer_checklist.md"
    summary_json_path = output_path / "external_validation_evidence_summary.json"
    summary_markdown_path = output_path / "external_validation_evidence_summary.md"
    manifest_path = output_path / "external_validation_evidence_manifest.json"

    warnings: list[str] = [EXTERNAL_EVIDENCE_WARNING]
    errors: list[str] = []
    generated_files: list[Path] = []

    for source, target in (
        (EXTERNAL_TEMPLATE_SOURCE, template_path),
        (EXTERNAL_CHECKLIST_SOURCE, checklist_path),
    ):
        if not source.exists():
            errors.append(f"external validation evidence source missing: {source}")
            continue
        shutil.copyfile(source, target)
        generated_files.append(target)

    summary = _build_summary(
        external_validation_csv=external_validation_csv,
        strict_mode=strict_mode,
        warnings=warnings,
        errors=errors,
    )
    status = _package_status(
        summary=summary,
        errors=tuple(errors),
        csv_path=external_validation_csv,
    )
    summary_payload = {
        "report_type": "external_validation_evidence_package",
        "status": status,
        "evidence_status": status,
        "source_csv_path": str(external_validation_csv) if external_validation_csv else None,
        "strict_mode": strict_mode,
        "summary": asdict(summary),
        "warnings": list(dict.fromkeys([*warnings, *summary.warnings])),
        "errors": errors,
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "ml_ready_for_project_use": False,
    }
    summary_json_path.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary_markdown_path.write_text(
        _render_summary_markdown(status=status, summary=summary, warnings=tuple(warnings)),
        encoding="utf-8",
    )
    generated_files.extend([summary_json_path, summary_markdown_path])

    manifest = _build_manifest(
        output_dir=output_path,
        generated_files=tuple(generated_files),
        status=status,
        warnings=tuple(dict.fromkeys([*warnings, *summary.warnings])),
        errors=tuple(errors),
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    generated_files.append(manifest_path)

    return ExternalValidationEvidencePackageResult(
        status=status,
        evidence_status=status,
        output_dir=str(output_path),
        generated_files=tuple(str(path) for path in generated_files),
        template_path=str(template_path),
        checklist_path=str(checklist_path),
        summary_json_path=str(summary_json_path),
        summary_markdown_path=str(summary_markdown_path),
        manifest_path=str(manifest_path),
        source_csv_path=str(external_validation_csv) if external_validation_csv else None,
        strict_mode=strict_mode,
        total_cases=summary.total_cases,
        accepted_cases=summary.accepted_cases,
        review_cases=summary.review_cases,
        failed_cases=summary.failed_cases,
        missing_external_values_count=summary.missing_external_values_count,
        warnings=tuple(dict.fromkeys([*warnings, *summary.warnings])),
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )


def _build_summary(
    *,
    external_validation_csv: Path | None,
    strict_mode: bool,
    warnings: list[str],
    errors: list[str],
) -> ExternalValidationSummary:
    if external_validation_csv is None:
        warnings.append(NO_EXTERNAL_CSV_WARNING)
        return build_external_validation_summary((), strict_mode=strict_mode)
    csv_path = Path(external_validation_csv)
    if not csv_path.exists():
        errors.append(f"external validation CSV missing: {csv_path}")
        return build_external_validation_summary((), strict_mode=strict_mode)
    try:
        rows = load_external_validation_csv(csv_path)
    except (OSError, ValueError) as exc:
        errors.append(f"external validation CSV cannot be read: {exc}")
        return build_external_validation_summary((), strict_mode=strict_mode)
    return build_external_validation_summary(rows, strict_mode=strict_mode)


def _package_status(
    *,
    summary: ExternalValidationSummary,
    errors: tuple[str, ...],
    csv_path: Path | None,
) -> str:
    if errors or summary.status == "fail":
        return "fail"
    if csv_path is None or summary.status == "review_required":
        return "review_required"
    return "pass"


def _render_summary_markdown(
    *,
    status: str,
    summary: ExternalValidationSummary,
    warnings: tuple[str, ...],
) -> str:
    all_warnings = tuple(dict.fromkeys([*warnings, *summary.warnings]))
    lines = [
        "# External Validation Evidence Package",
        "",
        EXTERNAL_EVIDENCE_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Summary",
        "",
        f"- status: `{status}`",
        f"- strict_mode: `{summary.strict_mode}`",
        f"- total_cases: `{summary.total_cases}`",
        f"- accepted_cases: `{summary.accepted_cases}`",
        f"- review_cases: `{summary.review_cases}`",
        f"- failed_cases: `{summary.failed_cases}`",
        f"- missing_external_values_count: `{summary.missing_external_values_count}`",
        "",
        "## Warnings",
        "",
        *(_bullet_lines(all_warnings)),
    ]
    return "\n".join(lines) + "\n"


def _build_manifest(
    *,
    output_dir: Path,
    generated_files: tuple[Path, ...],
    status: str,
    warnings: tuple[str, ...],
    errors: tuple[str, ...],
) -> dict[str, object]:
    return {
        "report_type": "external_validation_evidence_manifest",
        "status": status,
        "evidence_status": status,
        "output_dir": str(output_dir),
        "files": [
            {
                "path": str(path),
                "relative_path": path.relative_to(output_dir).as_posix(),
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            }
            for path in generated_files
            if path.exists()
        ],
        "source_files": {
            "template": str(EXTERNAL_TEMPLATE_SOURCE),
            "checklist": str(EXTERNAL_CHECKLIST_SOURCE),
        },
        "warnings": list(warnings),
        "errors": list(errors),
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "ml_ready_for_project_use": False,
    }


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
