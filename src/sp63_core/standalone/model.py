"""Typed public contract for the research-only standalone beam wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sp63_core.sections.orientation import TensionFace

STANDALONE_ELEMENT_TYPE = "rectangular_beam"
STANDALONE_LOAD_DURATION = "short"

StandaloneStatus = Literal["fail", "review_required", "outside_applicability"]


@dataclass(frozen=True, slots=True)
class StandaloneBeamInput:
    """Manual input for one rectangular-beam research case.

    The user-facing force units are kN and kN*m.  The controller converts them
    to the internal N and N*mm convention before invoking the existing core.
    """

    case_id: str
    b_mm: float
    h_mm: float
    cover_mm: float
    stirrup_diameter_mm: float
    concrete_class: str
    longitudinal_rebar_class: str
    stirrup_rebar_class: str
    moment_kNm: float
    shear_kN: float
    tension_face: TensionFace


@dataclass(frozen=True, slots=True)
class StandaloneRunResult:
    """Fail-closed result of one standalone research workflow run."""

    case_id: str
    status: StandaloneStatus
    preflight_status: str
    calculation_status: str
    evidence_status: str
    project_use: bool
    input_json_path: str | None
    standalone_input_path: str | None
    canonical_input_path: str | None
    latest_status_path: str | None
    report_dir: str | None
    report_index_path: str | None
    report_zip_path: str | None
    deterministic_report_zip_path: str | None
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    element_type: str = STANDALONE_ELEMENT_TYPE
    load_duration: str = STANDALONE_LOAD_DURATION
    status_scope: str = "public"
    completeness_status: str = "incomplete"
    project_use_status: str = "prohibited"
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    ml_included: bool = False
    reinforcement_selection_status: str = "diagnostic_only"
