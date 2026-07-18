"""Engineer verification helpers for draft material catalog values.

The verification gate records whether catalog values have been checked by an
engineer. It never changes material values automatically.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Any, Literal, cast

from sp63_core.materials.audit import MaterialAuditRow, build_material_audit_rows

MATERIAL_VERIFICATION_STATUSES = ("draft", "needs_review", "engineer_verified")
MaterialVerificationEvidenceKind = Literal[
    "not_provided",
    "synthetic_test_fixture",
    "independent_engineer_evidence",
]
MATERIAL_VERIFICATION_EVIDENCE_KINDS: tuple[MaterialVerificationEvidenceKind, ...] = (
    "not_provided",
    "synthetic_test_fixture",
    "independent_engineer_evidence",
)
INDEPENDENT_ENGINEER_EVIDENCE_KIND = "independent_engineer_evidence"
DEFAULT_MATERIAL_VERIFICATION_STATUS = "draft"
DEFAULT_MATERIAL_VERIFICATION_EVIDENCE_KIND = "not_provided"
MATERIAL_VERIFICATION_REQUIRED_COLUMNS: tuple[str, ...] = (
    "material_type",
    "class_name",
    "property_name",
    "catalog_value",
    "unit",
    "verification_status",
    "engineer_value",
    "engineer_name",
    "review_date",
    "source_note",
    "engineer_comment",
    "requires_engineer_review",
    "evidence_kind",
)
MATERIAL_VERIFICATION_WARNING = (
    "material catalog values remain draft until an engineer verifies every "
    "required property against SP 63 tables"
)
MATERIAL_VERIFICATION_NOTE = (
    "engineer must verify the catalog value against SP 63 tables; full "
    "normative text is not stored in repository"
)
SYNTHETIC_NON_EVIDENCE_WARNING = (
    "synthetic material verification rows are test-only non-evidence and do not "
    "constitute engineer sign-off"
)
CATALOG_VALUE_TOLERANCE = 1e-9


@dataclass(frozen=True)
class MaterialVerificationRow:
    """Single material property verification row."""

    material_type: str
    class_name: str
    property_name: str
    catalog_value: float
    unit: str
    verification_status: str
    engineer_value: float | None
    delta: float | None
    engineer_name: str
    review_date: str
    source_note: str
    engineer_comment: str
    evidence_kind: MaterialVerificationEvidenceKind
    requires_engineer_review: bool
    note: str


@dataclass(frozen=True)
class MaterialVerificationReport:
    """Summary of engineer verification status for material catalog values."""

    total_rows: int
    required_rows_count: int
    provided_rows_count: int
    engineer_verified_count: int
    draft_count: int
    needs_review_count: int
    missing_required_rows_count: int
    invalid_rows_count: int
    value_mismatch_count: int
    status_counts: dict[str, int]
    status: str
    warnings: tuple[str, ...]
    rows: tuple[MaterialVerificationRow, ...]
    requires_engineer_review: bool = True


def build_material_verification_rows() -> tuple[MaterialVerificationRow, ...]:
    """Return draft verification rows for every current material catalog property."""
    return tuple(
        _row_from_audit_row(audit_row, DEFAULT_MATERIAL_VERIFICATION_STATUS)
        for audit_row in build_material_audit_rows()
    )


def build_material_verification_report(
    csv_rows: tuple[Mapping[str, Any], ...] | None = None,
) -> MaterialVerificationReport:
    """Build an engineer verification report from current catalog or CSV rows."""
    expected_rows = _expected_audit_rows_by_key()
    invalid_rows_count = 0
    value_mismatch_count = 0
    missing_required_rows_count = 0
    warnings: list[str] = []

    if csv_rows is None:
        rows = build_material_verification_rows()
        warnings.append(MATERIAL_VERIFICATION_WARNING)
    else:
        parsed_rows: list[MaterialVerificationRow] = []
        seen_keys: set[tuple[str, str, str]] = set()
        for raw_row in csv_rows:
            missing_columns = [
                column
                for column in MATERIAL_VERIFICATION_REQUIRED_COLUMNS
                if column not in raw_row
            ]
            if missing_columns:
                invalid_rows_count += 1
                warnings.append(
                    "material verification CSV row is missing columns: "
                    + ", ".join(missing_columns)
                )
                continue

            material_type = str(raw_row["material_type"]).strip()
            class_name = str(raw_row["class_name"]).strip()
            property_name = str(raw_row["property_name"]).strip()
            key = (material_type, class_name, property_name)
            audit_row = expected_rows.get(key)
            if audit_row is None:
                invalid_rows_count += 1
                warnings.append(
                    "material verification CSV contains unsupported row "
                    f"{material_type}/{class_name}/{property_name}"
                )
                continue
            if key in seen_keys:
                invalid_rows_count += 1
                warnings.append(
                    "material verification CSV contains duplicate row "
                    f"{material_type}/{class_name}/{property_name}"
                )
                continue
            seen_keys.add(key)

            verification_status = _normalize_verification_status(
                raw_row["verification_status"]
            )
            if verification_status is None:
                invalid_rows_count += 1
                verification_status = "needs_review"
            requested_engineer_verified = verification_status == "engineer_verified"

            catalog_value = _parse_optional_float(raw_row["catalog_value"])
            if catalog_value is None:
                invalid_rows_count += 1
                catalog_value = float(audit_row.value)
                verification_status = "needs_review"
            if abs(catalog_value - float(audit_row.value)) > CATALOG_VALUE_TOLERANCE:
                value_mismatch_count += 1
                verification_status = "needs_review"

            engineer_value = _parse_optional_float(raw_row["engineer_value"])
            engineer_name = str(raw_row["engineer_name"] or "").strip()
            review_date = str(raw_row["review_date"] or "").strip()
            source_note = str(raw_row["source_note"] or "").strip()
            engineer_comment = str(raw_row["engineer_comment"] or "").strip()
            evidence_kind = _normalize_evidence_kind(raw_row["evidence_kind"])
            unit = str(raw_row["unit"] or "").strip()
            raw_requires_engineer_review = _parse_required_bool(
                raw_row["requires_engineer_review"]
            )
            if unit != audit_row.unit:
                invalid_rows_count += 1
                verification_status = "needs_review"
            raw_review_flag_is_inconsistent = (
                raw_requires_engineer_review is None
                or (requested_engineer_verified and raw_requires_engineer_review)
                or (
                    not requested_engineer_verified
                    and raw_requires_engineer_review is False
                )
            )
            if raw_review_flag_is_inconsistent:
                invalid_rows_count += 1
                verification_status = "needs_review"
            if evidence_kind is None:
                invalid_rows_count += 1
                verification_status = "needs_review"
                evidence_kind = DEFAULT_MATERIAL_VERIFICATION_EVIDENCE_KIND
            if requested_engineer_verified:
                if evidence_kind != INDEPENDENT_ENGINEER_EVIDENCE_KIND:
                    invalid_rows_count += 1
                    verification_status = "needs_review"
                if engineer_value is None:
                    invalid_rows_count += 1
                    verification_status = "needs_review"
                elif abs(engineer_value - float(audit_row.value)) > CATALOG_VALUE_TOLERANCE:
                    value_mismatch_count += 1
                    verification_status = "needs_review"
                if not source_note:
                    invalid_rows_count += 1
                    verification_status = "needs_review"
                if not engineer_name:
                    invalid_rows_count += 1
                    verification_status = "needs_review"
                if not review_date or not _is_iso_date(review_date):
                    invalid_rows_count += 1
                    verification_status = "needs_review"

            parsed_rows.append(
                MaterialVerificationRow(
                    material_type=material_type,
                    class_name=class_name,
                    property_name=property_name,
                    catalog_value=float(audit_row.value),
                    unit=audit_row.unit,
                    verification_status=verification_status,
                    engineer_value=engineer_value,
                    delta=(
                        None
                        if engineer_value is None
                        else engineer_value - float(audit_row.value)
                    ),
                    engineer_name=engineer_name,
                    review_date=review_date,
                    source_note=source_note,
                    engineer_comment=engineer_comment,
                    evidence_kind=evidence_kind,
                    requires_engineer_review=verification_status != "engineer_verified",
                    note=MATERIAL_VERIFICATION_NOTE,
                )
            )

        missing_required_rows_count = len(set(expected_rows) - seen_keys)
        if missing_required_rows_count:
            warnings.append("material verification CSV is missing required catalog rows")
        if invalid_rows_count:
            warnings.append("material verification CSV has invalid or incomplete rows")
        if value_mismatch_count:
            warnings.append(
                "engineer-filled material values do not match current catalog values"
            )
        if any("duplicate row" in warning for warning in warnings):
            warnings.append("duplicate material verification evidence was rejected")
        if any(
            row.evidence_kind == "synthetic_test_fixture" for row in parsed_rows
        ):
            warnings.append(SYNTHETIC_NON_EVIDENCE_WARNING)
        if any(row.verification_status != "engineer_verified" for row in parsed_rows):
            warnings.append(MATERIAL_VERIFICATION_WARNING)
        rows = tuple(parsed_rows)

    status_counts = _status_counts(rows)
    engineer_verified_count = status_counts["engineer_verified"]
    draft_count = status_counts["draft"]
    needs_review_count = status_counts["needs_review"]
    status = "pass"
    if (
        missing_required_rows_count
        or invalid_rows_count
        or value_mismatch_count
        or draft_count
        or needs_review_count
        or engineer_verified_count != len(expected_rows)
    ):
        status = "review_required"
    if not rows:
        status = "review_required"
        warnings.append("material verification report has no rows")

    return MaterialVerificationReport(
        total_rows=len(rows),
        required_rows_count=len(expected_rows),
        provided_rows_count=0 if csv_rows is None else len(csv_rows),
        engineer_verified_count=engineer_verified_count,
        draft_count=draft_count,
        needs_review_count=needs_review_count,
        missing_required_rows_count=missing_required_rows_count,
        invalid_rows_count=invalid_rows_count,
        value_mismatch_count=value_mismatch_count,
        status_counts=status_counts,
        status=status,
        warnings=tuple(dict.fromkeys(warnings)),
        rows=rows,
        requires_engineer_review=status != "pass",
    )


def _row_from_audit_row(
    audit_row: MaterialAuditRow,
    verification_status: str,
) -> MaterialVerificationRow:
    return MaterialVerificationRow(
        material_type=audit_row.material_type,
        class_name=audit_row.class_name,
        property_name=audit_row.property_name,
        catalog_value=float(audit_row.value),
        unit=audit_row.unit,
        verification_status=verification_status,
        engineer_value=None,
        delta=None,
        engineer_name="",
        review_date="",
        source_note="",
        engineer_comment="",
        evidence_kind=DEFAULT_MATERIAL_VERIFICATION_EVIDENCE_KIND,
        requires_engineer_review=True,
        note=MATERIAL_VERIFICATION_NOTE,
    )


def _expected_audit_rows_by_key() -> dict[tuple[str, str, str], MaterialAuditRow]:
    return {
        (row.material_type, row.class_name, row.property_name): row
        for row in build_material_audit_rows()
    }


def _normalize_verification_status(value: Any) -> str | None:
    status = str(value or "").strip().lower()
    if status in MATERIAL_VERIFICATION_STATUSES:
        return status
    return None


def _normalize_evidence_kind(value: Any) -> MaterialVerificationEvidenceKind | None:
    evidence_kind = str(value or "").strip().lower()
    if evidence_kind in MATERIAL_VERIFICATION_EVIDENCE_KINDS:
        return cast(MaterialVerificationEvidenceKind, evidence_kind)
    return None


def _parse_optional_float(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    return parsed if isfinite(parsed) else None


def _is_iso_date(value: str) -> bool:
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value and parsed <= date.today()


def _parse_required_bool(value: Any) -> bool | None:
    if value is True or value is False:
        return value
    normalized = str(value or "").strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    return None


def _status_counts(rows: tuple[MaterialVerificationRow, ...]) -> dict[str, int]:
    counts = {status: 0 for status in MATERIAL_VERIFICATION_STATUSES}
    for row in rows:
        counts[row.verification_status] = counts.get(row.verification_status, 0) + 1
    return counts
