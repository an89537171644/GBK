from pathlib import Path

from sp63_core.materials import (
    MATERIAL_VERIFICATION_REQUIRED_COLUMNS,
    build_material_audit_rows,
    build_material_verification_report,
    build_material_verification_rows,
)


def test_material_verification_rows_cover_current_catalog():
    audit_rows = build_material_audit_rows()
    verification_rows = build_material_verification_rows()

    assert len(verification_rows) == len(audit_rows)
    assert {row.verification_status for row in verification_rows} == {"draft"}
    assert all(row.requires_engineer_review is True for row in verification_rows)
    assert {row.unit for row in verification_rows} == {"MPa"}


def test_material_verification_default_report_is_review_required():
    report = build_material_verification_report()

    assert report.status == "review_required"
    assert report.total_rows == report.required_rows_count
    assert report.draft_count == report.required_rows_count
    assert report.engineer_verified_count == 0
    assert report.needs_review_count == 0
    assert report.requires_engineer_review is True


def test_material_verification_engineer_verified_report_passes():
    csv_rows = _engineer_verified_rows()
    report = build_material_verification_report(csv_rows)

    assert report.status == "pass"
    assert report.provided_rows_count == report.required_rows_count
    assert report.engineer_verified_count == report.required_rows_count
    assert report.draft_count == 0
    assert report.needs_review_count == 0
    assert report.requires_engineer_review is False


def test_material_verification_value_mismatch_requires_review():
    csv_rows = list(_engineer_verified_rows())
    csv_rows[0] = {**csv_rows[0], "engineer_value": str(float(csv_rows[0]["catalog_value"]) + 1)}

    report = build_material_verification_report(tuple(csv_rows))

    assert report.status == "review_required"
    assert report.value_mismatch_count == 1
    assert report.needs_review_count == 1
    assert any("do not match current catalog values" in warning for warning in report.warnings)


def test_material_verification_engineer_verified_requires_reviewer_metadata():
    csv_rows = list(_engineer_verified_rows())
    csv_rows[0] = {
        **csv_rows[0],
        "engineer_name": "",
        "review_date": "",
        "source_note": "",
    }

    report = build_material_verification_report(tuple(csv_rows))

    assert report.status == "review_required"
    assert report.invalid_rows_count == 3
    assert report.needs_review_count == 1
    assert report.rows[0].verification_status == "needs_review"


def test_material_verification_missing_rows_require_review():
    csv_rows = _engineer_verified_rows()[1:]

    report = build_material_verification_report(csv_rows)

    assert report.status == "review_required"
    assert report.missing_required_rows_count == 1
    assert any("missing required catalog rows" in warning for warning in report.warnings)


def test_material_verification_templates_exist():
    repo_root = Path(__file__).resolve().parents[1]
    csv_template = repo_root / "docs/materials/templates/material_catalog_verification_template.csv"
    markdown_template = repo_root / "docs/materials/material_catalog_engineer_verification.md"

    assert csv_template.exists()
    assert markdown_template.exists()
    header = csv_template.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert tuple(header) == MATERIAL_VERIFICATION_REQUIRED_COLUMNS
    assert "engineer_verified" in markdown_template.read_text(encoding="utf-8")


def _engineer_verified_rows() -> tuple[dict[str, str], ...]:
    rows = []
    for row in build_material_verification_rows():
        rows.append(
            {
                "material_type": row.material_type,
                "class_name": row.class_name,
                "property_name": row.property_name,
                "catalog_value": str(row.catalog_value),
                "unit": row.unit,
                "verification_status": "engineer_verified",
                "engineer_value": str(row.catalog_value),
                "engineer_name": "Test Engineer",
                "review_date": "2026-05-30",
                "source_note": "engineer checked SP 63 table reference; no full text stored",
                "engineer_comment": "synthetic test row",
                "requires_engineer_review": "false",
            }
        )
    return tuple(rows)
