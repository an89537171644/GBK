from sp63_core.materials import (
    build_concrete_audit_rows,
    build_material_audit_rows,
    build_rebar_audit_rows,
)
from sp63_core.materials.concrete import CONCRETE_CATALOG
from sp63_core.materials.rebar import REBAR_CATALOG

CONCRETE_PROPERTIES = {"Rb", "Rbt", "Rbser", "Rbtser", "Eb"}
REBAR_PROPERTIES = {
    "Rsn",
    "Rs",
    "Rsser",
    "Rsc_short",
    "Rsc_long",
    "Rsw",
    "Es",
}


def _properties_by_class(rows):
    result = {}
    for row in rows:
        result.setdefault(row.class_name, set()).add(row.property_name)
    return result


def test_concrete_audit_rows_cover_all_supported_classes():
    rows = build_concrete_audit_rows()
    properties_by_class = _properties_by_class(rows)

    assert set(properties_by_class) == set(CONCRETE_CATALOG)
    for class_name in CONCRETE_CATALOG:
        assert properties_by_class[class_name] == CONCRETE_PROPERTIES


def test_rebar_audit_rows_cover_all_supported_classes():
    rows = build_rebar_audit_rows()
    properties_by_class = _properties_by_class(rows)

    assert set(properties_by_class) == set(REBAR_CATALOG)
    for class_name in REBAR_CATALOG:
        assert properties_by_class[class_name] == REBAR_PROPERTIES


def test_material_audit_rows_are_positive_and_review_required():
    rows = build_material_audit_rows()

    assert rows
    for row in rows:
        assert row.value > 0
        assert row.unit == "MPa"
        assert row.requires_engineer_review is True
        assert row.audit_status == "draft_requires_engineer_review"


def test_material_audit_rows_combine_concrete_and_rebar():
    concrete_rows = build_concrete_audit_rows()
    rebar_rows = build_rebar_audit_rows()
    all_rows = build_material_audit_rows()

    assert len(all_rows) == len(concrete_rows) + len(rebar_rows)
    assert any(row.material_type == "concrete" for row in all_rows)
    assert any(row.material_type == "rebar" for row in all_rows)
