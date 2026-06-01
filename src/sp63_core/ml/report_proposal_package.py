"""Advisory ML proposal package backed by deterministic SP63 verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.ml.proposal_safety import ML_PROPOSAL_WARNINGS
from sp63_core.ml.report_neural_safety_audit import (
    EXTERNAL_VALIDATION_WARNING,
    MATERIAL_VERIFICATION_WARNING,
    PREDICTION_MISMATCH_WARNING,
    SMALL_DATASET_WARNING,
    NeuralAdvisorySafetyAuditResult,
    build_neural_advisory_safety_audit,
)

ML_OUTPUT_NOT_DESIGN_DECISION = "ML output cannot be used as a design decision"
LOW_CONFIDENCE_THRESHOLD = 0.60


@dataclass(frozen=True)
class MLProposalPackageResult:
    """Packaged advisory ML proposal with deterministic safety status."""

    status: str
    proposal_status: str
    source_dataset: str
    input_json_path: str
    target: str
    feature_mode: str
    predicted_status: str | None
    prediction_confidence: float | None
    deterministic_strength_status: str
    deterministic_serviceability_status: str
    deterministic_overall_status: str
    prediction_matches_deterministic: bool | None
    advisory_signal_usable: bool
    safety_audit_status: str
    proposal_accepted: bool
    proposal_rejected: bool
    proposal_requires_review: bool
    rejection_reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    markdown: str
    json_data: dict[str, Any]
    deterministic_report_required: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    requires_engineer_review: bool = True
    neural_network_used: bool = False


def build_ml_proposal_package(
    *,
    dataset_path: Path,
    input_json_path: Path,
    dataset_format: str | None = None,
    target: str = "overall_status",
    feature_mode: str = "input_only",
    random_state: int = 42,
    hidden_layer_sizes: tuple[int, ...] = (16,),
    max_iter: int = 500,
) -> MLProposalPackageResult:
    """Build a review package for an advisory ML proposal."""
    safety_audit = build_neural_advisory_safety_audit(
        dataset_path=dataset_path,
        input_json_path=input_json_path,
        dataset_format=dataset_format,
        target=target,
        feature_mode=feature_mode,
        random_state=random_state,
        hidden_layer_sizes=hidden_layer_sizes,
        max_iter=max_iter,
    )
    rejection_reasons = _proposal_reasons(safety_audit)
    hard_rejected = _has_hard_rejection(safety_audit, rejection_reasons)
    proposal_status = _proposal_status(
        safety_audit=safety_audit,
        rejection_reasons=rejection_reasons,
        hard_rejected=hard_rejected,
    )
    proposal_accepted = proposal_status == "accepted"
    proposal_rejected = proposal_status == "rejected"
    proposal_requires_review = proposal_status == "review_required"
    status = {
        "accepted": "pass",
        "review_required": "review_required",
        "rejected": "fail",
    }[proposal_status]
    warnings = _package_warnings(safety_audit, proposal_accepted)
    json_data = _json_data(
        status=status,
        proposal_status=proposal_status,
        safety_audit=safety_audit,
        proposal_accepted=proposal_accepted,
        proposal_rejected=proposal_rejected,
        proposal_requires_review=proposal_requires_review,
        rejection_reasons=rejection_reasons,
        warnings=warnings,
    )
    markdown = _markdown_report(json_data)

    return MLProposalPackageResult(
        status=status,
        proposal_status=proposal_status,
        source_dataset=safety_audit.source_dataset,
        input_json_path=safety_audit.input_json_path,
        target=safety_audit.target,
        feature_mode=safety_audit.feature_mode,
        predicted_status=safety_audit.predicted_status,
        prediction_confidence=safety_audit.prediction_confidence,
        deterministic_strength_status=safety_audit.deterministic_strength_status,
        deterministic_serviceability_status=safety_audit.deterministic_serviceability_status,
        deterministic_overall_status=safety_audit.deterministic_overall_status,
        prediction_matches_deterministic=safety_audit.prediction_matches_deterministic,
        advisory_signal_usable=safety_audit.advisory_signal_usable,
        safety_audit_status=safety_audit.audit_status,
        proposal_accepted=proposal_accepted,
        proposal_rejected=proposal_rejected,
        proposal_requires_review=proposal_requires_review,
        rejection_reasons=rejection_reasons,
        warnings=warnings,
        errors=safety_audit.errors,
        markdown=markdown,
        json_data=json_data,
        deterministic_report_required=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        requires_engineer_review=True,
        neural_network_used=safety_audit.neural_network_used,
    )


def _proposal_reasons(
    safety_audit: NeuralAdvisorySafetyAuditResult,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if safety_audit.errors:
        reasons.append("deterministic verification failed or unavailable")
    if safety_audit.deterministic_overall_status == "fail":
        reasons.append("deterministic SP63 result is fail")
    if safety_audit.deterministic_overall_status == "review_or_fail":
        reasons.append("deterministic SP63 result requires review")
    if safety_audit.prediction_matches_deterministic is False:
        reasons.append(PREDICTION_MISMATCH_WARNING)
    if safety_audit.audit_status == "fail":
        reasons.extend(safety_audit.rejection_reasons)
    if safety_audit.predicted_status is None:
        reasons.append("target is missing or neural prediction was unavailable")
    if SMALL_DATASET_WARNING in safety_audit.warnings:
        reasons.append("dataset is too small for reliable ML proposal")
    if MATERIAL_VERIFICATION_WARNING in safety_audit.warnings:
        reasons.append("material verification is not provided")
    if EXTERNAL_VALIDATION_WARNING in safety_audit.warnings:
        reasons.append("external validation is not provided")
    reasons.append(ML_OUTPUT_NOT_DESIGN_DECISION)
    return tuple(dict.fromkeys(reasons))


def _has_hard_rejection(
    safety_audit: NeuralAdvisorySafetyAuditResult,
    rejection_reasons: tuple[str, ...],
) -> bool:
    hard_markers = (
        "deterministic verification failed or unavailable",
        "deterministic SP63 result is fail",
        "deterministic SP63 result requires review",
        PREDICTION_MISMATCH_WARNING,
        "target is missing or neural prediction was unavailable",
    )
    return (
        bool(safety_audit.errors)
        or safety_audit.audit_status == "fail"
        or any(marker in rejection_reasons for marker in hard_markers)
    )


def _proposal_status(
    *,
    safety_audit: NeuralAdvisorySafetyAuditResult,
    rejection_reasons: tuple[str, ...],
    hard_rejected: bool,
) -> str:
    if hard_rejected:
        return "rejected"
    accepted_conditions = (
        safety_audit.deterministic_overall_status == "pass"
        and safety_audit.prediction_matches_deterministic is True
        and safety_audit.audit_status != "fail"
        and not safety_audit.errors
        and safety_audit.ml_is_advisory_only
        and safety_audit.deterministic_checks_required
        and safety_audit.requires_engineer_review
    )
    review_reasons = tuple(
        reason for reason in rejection_reasons if reason != ML_OUTPUT_NOT_DESIGN_DECISION
    )
    low_confidence = (
        safety_audit.prediction_confidence is not None
        and safety_audit.prediction_confidence < LOW_CONFIDENCE_THRESHOLD
    )
    if accepted_conditions and not review_reasons and not safety_audit.warnings:
        return "accepted"
    if accepted_conditions or safety_audit.audit_status == "review_required" or low_confidence:
        return "review_required"
    return "rejected"


def _package_warnings(
    safety_audit: NeuralAdvisorySafetyAuditResult,
    proposal_accepted: bool,
) -> tuple[str, ...]:
    warnings = [
        *ML_PROPOSAL_WARNINGS,
        *safety_audit.warnings,
        ML_OUTPUT_NOT_DESIGN_DECISION,
    ]
    if proposal_accepted:
        warnings.append("ML proposal accepted as advisory signal only")
    return tuple(dict.fromkeys(warnings))


def _json_data(
    *,
    status: str,
    proposal_status: str,
    safety_audit: NeuralAdvisorySafetyAuditResult,
    proposal_accepted: bool,
    proposal_rejected: bool,
    proposal_requires_review: bool,
    rejection_reasons: tuple[str, ...],
    warnings: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "report_type": "ml_proposal_package",
        "status": status,
        "proposal_status": proposal_status,
        "source_dataset": safety_audit.source_dataset,
        "input_json_path": safety_audit.input_json_path,
        "target": safety_audit.target,
        "feature_mode": safety_audit.feature_mode,
        "predicted_status": safety_audit.predicted_status,
        "prediction_confidence": safety_audit.prediction_confidence,
        "class_probabilities": safety_audit.json_data.get("class_probabilities", {}),
        "deterministic_strength_status": safety_audit.deterministic_strength_status,
        "deterministic_serviceability_status": (
            safety_audit.deterministic_serviceability_status
        ),
        "deterministic_overall_status": safety_audit.deterministic_overall_status,
        "prediction_matches_deterministic": safety_audit.prediction_matches_deterministic,
        "advisory_signal_usable": safety_audit.advisory_signal_usable,
        "safety_audit_status": safety_audit.audit_status,
        "proposal_accepted": proposal_accepted,
        "proposal_rejected": proposal_rejected,
        "proposal_requires_review": proposal_requires_review,
        "rejection_reasons": list(rejection_reasons),
        "warnings": list(warnings),
        "errors": list(safety_audit.errors),
        "deterministic_report_required": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "requires_engineer_review": True,
        "neural_network_used": safety_audit.neural_network_used,
    }


def _markdown_report(data: dict[str, Any]) -> str:
    probabilities = data.get("class_probabilities") or {}
    rejection_reasons = data.get("rejection_reasons") or []
    warnings = data.get("warnings") or []
    errors = data.get("errors") or []
    lines = [
        "# ML Proposal Package — Advisory Only",
        "",
        (
            "ML proposal is advisory-only. It is not a design calculation. "
            "Deterministic SP63 verification and engineer review are mandatory."
        ),
        "",
        "## Input data",
        "",
        f"- dataset path: `{data['source_dataset']}`",
        f"- input_json path: `{data['input_json_path']}`",
        f"- target: `{data['target']}`",
        f"- feature_mode: `{data['feature_mode']}`",
        "",
        "## Neural advisory prediction",
        "",
        f"- predicted_status: `{data['predicted_status']}`",
        f"- prediction_confidence: `{data['prediction_confidence']}`",
        f"- class_probabilities: `{probabilities}`",
        f"- neural_network_used: `{data['neural_network_used']}`",
        "",
        "## Deterministic SP63 verification",
        "",
        f"- strength_status: `{data['deterministic_strength_status']}`",
        f"- serviceability_status: `{data['deterministic_serviceability_status']}`",
        f"- overall_status: `{data['deterministic_overall_status']}`",
        "",
        "## Safety audit",
        "",
        f"- safety_audit_status: `{data['safety_audit_status']}`",
        (
            "- prediction_matches_deterministic: "
            f"`{data['prediction_matches_deterministic']}`"
        ),
        f"- advisory_signal_usable: `{data['advisory_signal_usable']}`",
        "",
        "## Proposal decision",
        "",
        f"- proposal_status: `{data['proposal_status']}`",
        f"- proposal_accepted: `{data['proposal_accepted']}`",
        f"- proposal_rejected: `{data['proposal_rejected']}`",
        f"- proposal_requires_review: `{data['proposal_requires_review']}`",
        "",
        "## Rejection / review reasons",
        "",
        *(_bullet_lines(rejection_reasons) or ["- none"]),
        "",
        "## Warnings",
        "",
        *(_bullet_lines(warnings) or ["- none"]),
        "",
        "## Errors",
        "",
        *(_bullet_lines(errors) or ["- none"]),
        "",
        "## Limitations",
        "",
        "- ML is advisory-only",
        "- deterministic SP63 verification is mandatory",
        "- engineer review is mandatory",
        "- material verification remains separate",
        "- external validation remains separate",
        "- metrics and predictions are not production evidence",
        "- no certification is provided by this package",
        "",
    ]
    return "\n".join(lines)


def _bullet_lines(values: list[Any]) -> list[str]:
    return [f"- {value}" for value in values]
