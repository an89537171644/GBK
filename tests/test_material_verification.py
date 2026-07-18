import csv
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
    assert {row.evidence_kind for row in verification_rows} == {"not_provided"}
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


def test_material_verification_rejects_non_finite_engineer_values():
    for non_finite in ("NaN", "Infinity", "-Infinity"):
        csv_rows = tuple(
            {**row, "engineer_value": non_finite} for row in _engineer_verified_rows()
        )

        report = build_material_verification_report(csv_rows)

        assert report.status == "review_required"
        assert report.engineer_verified_count == 0
        assert report.needs_review_count == report.required_rows_count
        assert report.requires_engineer_review is True


def test_material_verification_rejects_non_finite_catalog_values():
    for non_finite in ("NaN", "Infinity", "-Infinity"):
        csv_rows = list(_engineer_verified_rows())
        csv_rows[0] = {**csv_rows[0], "catalog_value": non_finite}

        report = build_material_verification_report(tuple(csv_rows))

        assert report.status == "review_required"
        assert report.rows[0].verification_status == "needs_review"
        assert report.requires_engineer_review is True


def test_material_verification_rejects_wrong_unit_and_invalid_date():
    csv_rows = list(_engineer_verified_rows())
    csv_rows[0] = {**csv_rows[0], "unit": "Pa", "review_date": "not-a-date"}

    report = build_material_verification_report(tuple(csv_rows))

    assert report.status == "review_required"
    assert report.invalid_rows_count == 2
    assert report.rows[0].verification_status == "needs_review"


def test_material_verification_rejects_future_review_date():
    csv_rows = tuple(
        {**row, "review_date": "9999-12-31"} for row in _engineer_verified_rows()
    )

    report = build_material_verification_report(csv_rows)

    assert report.status == "review_required"
    assert report.engineer_verified_count == 0
    assert report.requires_engineer_review is True


def test_material_verification_honors_raw_requires_engineer_review_flag():
    csv_rows = tuple(
        {**row, "requires_engineer_review": "true"}
        for row in _engineer_verified_rows()
    )

    report = build_material_verification_report(csv_rows)

    assert report.status == "review_required"
    assert report.engineer_verified_count == 0
    assert all(row.requires_engineer_review for row in report.rows)


def test_material_verification_rejects_duplicate_evidence_rows():
    csv_rows = _engineer_verified_rows()

    report = build_material_verification_report((*csv_rows, csv_rows[0]))

    assert report.status == "review_required"
    assert report.invalid_rows_count == 1
    assert report.provided_rows_count == report.required_rows_count + 1
    assert any("duplicate" in warning for warning in report.warnings)


def test_material_verification_rejects_synthetic_evidence():
    csv_rows = list(_engineer_verified_rows())
    csv_rows[0] = {
        **csv_rows[0],
        "evidence_kind": "synthetic_test_fixture",
    }

    report = build_material_verification_report(tuple(csv_rows))

    assert report.status == "review_required"
    assert report.rows[0].verification_status == "needs_review"
    assert any("test-only non-evidence" in warning for warning in report.warnings)


def test_material_verification_requires_typed_independent_evidence():
    for evidence_kind in ("", "not_provided", "unknown_kind"):
        csv_rows = list(_engineer_verified_rows())
        csv_rows[0] = {**csv_rows[0], "evidence_kind": evidence_kind}

        report = build_material_verification_report(tuple(csv_rows))

        assert report.status == "review_required"
        assert report.rows[0].verification_status == "needs_review"
        assert report.requires_engineer_review is True


def test_independent_evidence_comment_may_describe_synthetic_comparison():
    csv_rows = tuple(
        {
            **row,
            "source_note": "controlled source; no synthetic data used as evidence",
            "engineer_comment": "synthetic benchmark was considered separately",
        }
        for row in _engineer_verified_rows()
    )

    report = build_material_verification_report(csv_rows)

    assert report.status == "pass"
    assert report.engineer_verified_count == report.required_rows_count


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


def test_shared_sample_is_synthetic_non_evidence_after_step3_recheck():
    fixture = Path("tests/fixtures/material_verification_sample.csv")
    with fixture.open(encoding="utf-8", newline="") as csv_file:
        rows = tuple(dict(row) for row in csv.DictReader(csv_file))

    report = build_material_verification_report(rows)
    step3_rows = tuple(
        row
        for row in report.rows
        if (row.material_type, row.class_name, row.property_name)
        in {
            ("concrete", "B15", "Rbtser"),
            ("rebar", "A400", "Rsn"),
            ("rebar", "A400", "Rs"),
            ("rebar", "A400", "Rsser"),
            ("rebar", "A400", "Rsc_short"),
            ("rebar", "A400", "Rsc_long"),
        }
    )

    assert report.status == "review_required"
    assert report.engineer_verified_count == 0
    assert report.needs_review_count == report.required_rows_count
    assert any("test-only non-evidence" in warning for warning in report.warnings)
    assert all(row.verification_status == "needs_review" for row in report.rows)
    assert all(row.verification_status == "needs_review" for row in step3_rows)
    assert all(row.engineer_name == "" and row.review_date == "" for row in step3_rows)
    assert all(row.requires_engineer_review is True for row in step3_rows)


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
                "engineer_comment": "independent verification row",
                "requires_engineer_review": "false",
                "evidence_kind": "independent_engineer_evidence",
            }
        )
    return tuple(rows)
