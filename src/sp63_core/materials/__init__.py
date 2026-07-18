"""Draft material catalogs for MVP inputs.

The values are marked as requiring engineering review before use in final
calculation acceptance.
"""

from sp63_core.materials.audit import (
    MaterialAuditRow,
    build_concrete_audit_rows,
    build_material_audit_rows,
    build_rebar_audit_rows,
)
from sp63_core.materials.concrete import Concrete, get_concrete
from sp63_core.materials.rebar import (
    LONGITUDINAL_DIAMETERS,
    STIRRUP_DIAMETERS,
    Rebar,
    area_by_diameter,
    get_rebar,
)
from sp63_core.materials.uls_context import (
    NORMATIVE_PROFILE_ID,
    SUPPORTED_ULS_CONCRETE_CLASSES,
    SUPPORTED_ULS_LONGITUDINAL_REBAR_CLASSES,
    LoadCombination,
    LoadDuration,
    ULSMaterialContext,
    UnsupportedULSMaterialProfileError,
    resolve_uls_material_context,
)
from sp63_core.materials.verification import (
    INDEPENDENT_ENGINEER_EVIDENCE_KIND,
    MATERIAL_VERIFICATION_EVIDENCE_KINDS,
    MATERIAL_VERIFICATION_REQUIRED_COLUMNS,
    MATERIAL_VERIFICATION_STATUSES,
    MaterialVerificationEvidenceKind,
    MaterialVerificationReport,
    MaterialVerificationRow,
    build_material_verification_report,
    build_material_verification_rows,
)
from sp63_core.materials.verification_report import (
    MaterialVerificationReportDocument,
    MaterialVerificationReviewRow,
    build_material_verification_report_document,
    render_material_verification_markdown,
)

__all__ = [
    "Concrete",
    "LONGITUDINAL_DIAMETERS",
    "LoadCombination",
    "LoadDuration",
    "MaterialAuditRow",
    "INDEPENDENT_ENGINEER_EVIDENCE_KIND",
    "MATERIAL_VERIFICATION_EVIDENCE_KINDS",
    "MATERIAL_VERIFICATION_REQUIRED_COLUMNS",
    "MATERIAL_VERIFICATION_STATUSES",
    "NORMATIVE_PROFILE_ID",
    "SUPPORTED_ULS_CONCRETE_CLASSES",
    "SUPPORTED_ULS_LONGITUDINAL_REBAR_CLASSES",
    "MaterialVerificationReport",
    "MaterialVerificationEvidenceKind",
    "MaterialVerificationReportDocument",
    "MaterialVerificationReviewRow",
    "MaterialVerificationRow",
    "Rebar",
    "STIRRUP_DIAMETERS",
    "ULSMaterialContext",
    "UnsupportedULSMaterialProfileError",
    "area_by_diameter",
    "build_concrete_audit_rows",
    "build_material_audit_rows",
    "build_material_verification_report",
    "build_material_verification_report_document",
    "build_material_verification_rows",
    "build_rebar_audit_rows",
    "get_concrete",
    "get_rebar",
    "render_material_verification_markdown",
    "resolve_uls_material_context",
]
