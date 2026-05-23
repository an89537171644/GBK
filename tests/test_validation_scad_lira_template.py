from sp63_core.validation import build_scad_lira_comparison_template


def test_scad_lira_comparison_template_contains_required_fields():
    rows = build_scad_lira_comparison_template()

    assert rows
    row = rows[0]
    assert "scad_As" in row
    assert "lira_As" in row
    assert "engineer_comment" in row
    assert "accepted" in row
