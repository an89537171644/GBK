"""Material catalog audit helpers.

The audit report exposes current draft catalog values for engineering review.
It does not approve the values for final design use.
"""

from dataclasses import dataclass

from sp63_core.materials.concrete import CONCRETE_CATALOG
from sp63_core.materials.rebar import REBAR_CATALOG

AUDIT_STATUS = "draft_requires_engineer_review"
AUDIT_NOTE = (
    "value must be checked against SP 63 tables by an engineer; "
    "full normative text is not stored in repository"
)


@dataclass(frozen=True)
class MaterialAuditRow:
    """Single audited material property row."""

    material_type: str
    class_name: str
    property_name: str
    value: float
    unit: str
    usage: str
    audit_status: str
    requires_engineer_review: bool
    note: str


CONCRETE_PROPERTY_USAGE: dict[str, str] = {
    "Rb": "first limit state concrete compression",
    "Rbt": "first limit state concrete tension",
    "Rbser": "service limit state concrete compression",
    "Rbtser": "service limit state concrete tension",
    "Eb": "concrete elastic modulus",
}

REBAR_PROPERTY_USAGE: dict[str, str] = {
    "Rsn": "normative reinforcement tensile strength",
    "Rs": "first limit state reinforcement tension",
    "Rsser": "service limit state reinforcement tension",
    "Rsc_short": "short-term compression reinforcement resistance",
    "Rsc_long": "long-term compression reinforcement resistance",
    "Rsw": "transverse reinforcement resistance",
    "Es": "reinforcement elastic modulus",
}


def build_concrete_audit_rows() -> tuple[MaterialAuditRow, ...]:
    """Return audit rows for all draft concrete catalog properties."""
    rows: list[MaterialAuditRow] = []
    for concrete in CONCRETE_CATALOG.values():
        for property_name, usage in CONCRETE_PROPERTY_USAGE.items():
            rows.append(
                MaterialAuditRow(
                    material_type="concrete",
                    class_name=concrete.class_name,
                    property_name=property_name,
                    value=float(getattr(concrete, property_name)),
                    unit="MPa",
                    usage=usage,
                    audit_status=AUDIT_STATUS,
                    requires_engineer_review=True,
                    note=AUDIT_NOTE,
                )
            )
    return tuple(rows)


def build_rebar_audit_rows() -> tuple[MaterialAuditRow, ...]:
    """Return audit rows for all draft reinforcement catalog properties."""
    rows: list[MaterialAuditRow] = []
    for rebar in REBAR_CATALOG.values():
        for property_name, usage in REBAR_PROPERTY_USAGE.items():
            rows.append(
                MaterialAuditRow(
                    material_type="rebar",
                    class_name=rebar.class_name,
                    property_name=property_name,
                    value=float(getattr(rebar, property_name)),
                    unit="MPa",
                    usage=usage,
                    audit_status=AUDIT_STATUS,
                    requires_engineer_review=True,
                    note=AUDIT_NOTE,
                )
            )
    return tuple(rows)


def build_material_audit_rows() -> tuple[MaterialAuditRow, ...]:
    """Return concrete and reinforcement material audit rows."""
    return (*build_concrete_audit_rows(), *build_rebar_audit_rows())
