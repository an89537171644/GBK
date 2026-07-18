"""Markdown/JSON report helpers for engineer material verification CSV files."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from sp63_core.materials.verification import (
    INDEPENDENT_ENGINEER_EVIDENCE_KIND,
    MATERIAL_VERIFICATION_EVIDENCE_KINDS,
    MATERIAL_VERIFICATION_STATUSES,
    MaterialVerificationRow,
    build_material_verification_report,
)

BASE_REQUIRED_FIELDS: tuple[str, ...] = (
    "material_type",
    "class_name",
    "property_name",
    "catalog_value",
    "unit",
    "verification_status",
    "evidence_kind",
    "requires_engineer_review",
)
ENGINEER_VERIFIED_REQUIRED_FIELDS: tuple[str, ...] = (
    "engineer_value",
    "engineer_name",
    "review_date",
    "source_note",
)


@dataclass(frozen=True)
class MaterialVerificationReviewRow:
    """Material verification row that still needs engineering review."""

    material_type: str
    class_name: str
    property_name: str
    verification_status: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class MaterialVerificationReportDocument:
    """Summary and Markdown body for an engineer-filled material verification CSV."""

    status: str
    total_rows: int
    engineer_verified_count: int
    needs_review_count: int
    draft_count: int
    missing_required_fields_count: int
    missing_required_rows_count: int
    value_mismatch_count: int
    status_counts: dict[str, int]
    needs_review_rows: tuple[MaterialVerificationReviewRow, ...]
    warnings: tuple[str, ...]
    markdown: str
    requires_engineer_review: bool = True


def build_material_verification_report_document(
    rows: tuple[Mapping[str, Any], ...],
) -> MaterialVerificationReportDocument:
    """Build a Markdown/JSON-ready report for an engineer-filled verification CSV."""
    gate_report = build_material_verification_report(rows)
    missing_required_fields_count = _missing_required_fields_count(rows)
    needs_review_rows = _needs_review_rows(rows, gate_report.rows)
    warnings = list(gate_report.warnings)
    if missing_required_fields_count:
        warnings.append("material verification CSV has missing required fields")
    if needs_review_rows:
        warnings.append("material verification CSV contains rows that need review")

    status = gate_report.status
    if missing_required_fields_count:
        status = "review_required"

    document_without_markdown = MaterialVerificationReportDocument(
        status=status,
        total_rows=gate_report.total_rows,
        engineer_verified_count=gate_report.engineer_verified_count,
        needs_review_count=gate_report.needs_review_count,
        draft_count=gate_report.draft_count,
        missing_required_fields_count=missing_required_fields_count,
        missing_required_rows_count=gate_report.missing_required_rows_count,
        value_mismatch_count=gate_report.value_mismatch_count,
        status_counts=gate_report.status_counts,
        needs_review_rows=needs_review_rows,
        warnings=tuple(dict.fromkeys(warnings)),
        markdown="",
        requires_engineer_review=status != "pass",
    )
    return MaterialVerificationReportDocument(
        **{
            **document_without_markdown.__dict__,
            "markdown": render_material_verification_markdown(document_without_markdown),
        }
    )


def render_material_verification_markdown(
    document: MaterialVerificationReportDocument,
) -> str:
    """Render a material verification document as Markdown."""
    lines = [
        "# Material Verification Report",
        "",
        "requires_engineer_review = "
        + ("true" if document.requires_engineer_review else "false"),
        "",
        "## Summary",
        "",
        "| metric | value |",
        "|---|---:|",
        f"| status | {document.status} |",
        f"| total_rows | {document.total_rows} |",
        f"| engineer_verified_count | {document.engineer_verified_count} |",
        f"| needs_review_count | {document.needs_review_count} |",
        f"| draft_count | {document.draft_count} |",
        f"| missing_required_fields_count | {document.missing_required_fields_count} |",
        f"| missing_required_rows_count | {document.missing_required_rows_count} |",
        f"| value_mismatch_count | {document.value_mismatch_count} |",
        "",
        "## Status Counts",
        "",
        "| verification_status | count |",
        "|---|---:|",
    ]
    for status in MATERIAL_VERIFICATION_STATUSES:
        lines.append(f"| {status} | {document.status_counts.get(status, 0)} |")

    lines.extend(
        [
            "",
            "## Needs Review Rows",
            "",
            "| material_type | class_name | property_name | status | reasons |",
            "|---|---|---|---|---|",
        ]
    )
    if document.needs_review_rows:
        for row in document.needs_review_rows:
            reasons = "; ".join(row.reasons)
            lines.append(
                "| "
                f"{row.material_type} | {row.class_name} | {row.property_name} | "
                f"{row.verification_status} | {reasons} |"
            )
    else:
        lines.append("| - | - | - | - | none |")

    lines.extend(
        [
            "",
            "## Warnings",
            "",
        ]
    )
    if document.warnings:
        lines.extend(f"- {warning}" for warning in document.warnings)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This report does not change material catalog values automatically.",
            "- Full SP 63 text is not stored in this repository.",
            "- Only evidence_kind=independent_engineer_evidence may accompany "
            "engineer_verified.",
            "- Engineer verification remains mandatory before final design use.",
        ]
    )
    return "\n".join(lines) + "\n"


def _missing_required_fields_count(rows: tuple[Mapping[str, Any], ...]) -> int:
    count = 0
    for row in rows:
        for field in BASE_REQUIRED_FIELDS:
            if _is_blank(row.get(field)):
                count += 1
        if str(row.get("verification_status") or "").strip().lower() == "engineer_verified":
            for field in ENGINEER_VERIFIED_REQUIRED_FIELDS:
                if _is_blank(row.get(field)):
                    count += 1
    return count


def _needs_review_rows(
    raw_rows: tuple[Mapping[str, Any], ...],
    parsed_rows: tuple[MaterialVerificationRow, ...],
) -> tuple[MaterialVerificationReviewRow, ...]:
    raw_reasons = {
        _row_key(row): _review_reasons_for_raw_row(row)
        for row in raw_rows
    }
    review_rows: list[MaterialVerificationReviewRow] = []
    for row in parsed_rows:
        if row.verification_status != "needs_review":
            continue
        key = (row.material_type, row.class_name, row.property_name)
        reasons = raw_reasons.get(key) or ("verification status requires review",)
        review_rows.append(
            MaterialVerificationReviewRow(
                material_type=row.material_type,
                class_name=row.class_name,
                property_name=row.property_name,
                verification_status=row.verification_status,
                reasons=tuple(dict.fromkeys(reasons)),
            )
        )
    return tuple(review_rows)


def _review_reasons_for_raw_row(row: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    for field in BASE_REQUIRED_FIELDS:
        if _is_blank(row.get(field)):
            reasons.append(f"missing {field}")
    status = str(row.get("verification_status") or "").strip().lower()
    if status not in MATERIAL_VERIFICATION_STATUSES:
        reasons.append("invalid verification_status")
    evidence_kind = str(row.get("evidence_kind") or "").strip().lower()
    if evidence_kind not in MATERIAL_VERIFICATION_EVIDENCE_KINDS:
        reasons.append("invalid evidence_kind")
    if status == "draft":
        reasons.append("verification_status is draft")
    if status == "needs_review":
        reasons.append("verification_status is needs_review")
    if status == "engineer_verified":
        if evidence_kind != INDEPENDENT_ENGINEER_EVIDENCE_KIND:
            reasons.append(
                "engineer_verified requires independent_engineer_evidence"
            )
        for field in ENGINEER_VERIFIED_REQUIRED_FIELDS:
            if _is_blank(row.get(field)):
                reasons.append(f"missing {field}")
    return tuple(reasons)


def _row_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("material_type") or "").strip(),
        str(row.get("class_name") or "").strip(),
        str(row.get("property_name") or "").strip(),
    )


def _is_blank(value: Any) -> bool:
    return str(value or "").strip() == ""
