from sp63_core.validation import build_scad_lira_comparison_template


def test_scad_lira_comparison_template_contains_required_fields():
    rows = build_scad_lira_comparison_template()

    assert rows
    row = rows[0]
    assert "local_axes_id" in row
    assert "moment_axis" in row
    assert "tension_face" in row
    assert "load_duration" in row
    assert "scad_As" in row
    assert "lira_As" in row
    assert "engineer_comment" in row
    assert "accepted" in row
    assert row["completeness_status"] == "incomplete"
    assert row["evidence_status"] == "needs_engineer_review"
    assert row["project_use_status"] == "prohibited"
    assert row["project_use"] == "false"
    assert row["requires_engineer_review"] == "true"
