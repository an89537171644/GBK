from sp63_core.materials import (
    build_material_verification_report_document,
    build_material_verification_rows,
)


def test_material_verification_report_passes_for_complete_engineer_csv():
    document = build_material_verification_report_document(_engineer_verified_rows())

    assert document.status == "pass"
    assert document.total_rows == 51
    assert document.engineer_verified_count == 51
    assert document.needs_review_count == 0
    assert document.missing_required_fields_count == 0
    assert document.needs_review_rows == ()
    assert "Material Verification Report" in document.markdown
    assert "| engineer_verified_count | 51 |" in document.markdown


def test_material_verification_report_lists_needs_review_rows():
    rows = list(_engineer_verified_rows())
    rows[0] = {
        **rows[0],
        "verification_status": "needs_review",
        "source_note": "",
    }

    document = build_material_verification_report_document(tuple(rows))

    assert document.status == "review_required"
    assert document.needs_review_count == 1
    assert len(document.needs_review_rows) == 1
    assert document.needs_review_rows[0].class_name == rows[0]["class_name"]
    assert "verification_status is needs_review" in document.needs_review_rows[0].reasons
    assert "Needs Review Rows" in document.markdown


def test_material_verification_report_counts_missing_required_fields():
    rows = list(_engineer_verified_rows())
    rows[0] = {
        **rows[0],
        "engineer_name": "",
        "review_date": "",
        "source_note": "",
    }

    document = build_material_verification_report_document(tuple(rows))

    assert document.status == "review_required"
    assert document.missing_required_fields_count == 3
    assert document.needs_review_count == 1
    assert len(document.needs_review_rows) == 1
    assert "missing engineer_name" in document.needs_review_rows[0].reasons
    assert "missing review_date" in document.needs_review_rows[0].reasons
    assert "missing source_note" in document.needs_review_rows[0].reasons


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
                "engineer_comment": "independent verification test row",
                "requires_engineer_review": "false",
                "evidence_kind": "independent_engineer_evidence",
            }
        )
    return tuple(rows)
