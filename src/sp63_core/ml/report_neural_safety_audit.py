"""Safety audit for advisory neural predictions verified by SP63 core."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.ml.report_neural_prediction import (
    ADVISORY_PREDICTION_WARNINGS,
    build_neural_advisory_prediction,
)

MANDATORY_SAFETY_WARNINGS: tuple[str, ...] = ADVISORY_PREDICTION_WARNINGS
SMALL_DATASET_WARNING = "dataset is too small for reliable advisory prediction"
DETERMINISTIC_DERIVED_WARNING = (
    "deterministic-derived features may leak design decisions and must not be used "
    "for project ML decisions without review"
)
MATERIAL_VERIFICATION_WARNING = (
    "material verification remains separate and must be checked by an engineer"
)
EXTERNAL_VALIDATION_WARNING = (
    "external validation remains separate and must be checked by an engineer"
)
PREDICTION_MISMATCH_WARNING = (
    "neural advisory prediction differs from deterministic SP63 result"
)


@dataclass(frozen=True)
class NeuralAdvisorySafetyAuditResult:
    """Engineer-facing audit for one advisory neural prediction."""

    status: str
    audit_status: str
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


def build_neural_advisory_safety_audit(
    *,
    dataset_path: Path,
    input_json_path: Path,
    dataset_format: str | None = None,
    target: str = "overall_status",
    feature_mode: str = "input_only",
    random_state: int = 42,
    hidden_layer_sizes: tuple[int, ...] = (16,),
    max_iter: int = 500,
) -> NeuralAdvisorySafetyAuditResult:
    """Build a safety audit around the K48 neural advisory prediction."""
    prediction = build_neural_advisory_prediction(
        dataset_path=dataset_path,
        input_json_path=input_json_path,
        dataset_format=dataset_format,
        target=target,
        feature_mode=feature_mode,
        hidden_layer_sizes=hidden_layer_sizes,
        max_iter=max_iter,
        random_state=random_state,
    )
    warnings = list(prediction.warnings)
    warnings.extend(MANDATORY_SAFETY_WARNINGS)
    warnings.extend((MATERIAL_VERIFICATION_WARNING, EXTERNAL_VALIDATION_WARNING))
    if feature_mode == "deterministic_derived":
        warnings.append(DETERMINISTIC_DERIVED_WARNING)
    warnings = list(dict.fromkeys(warnings))

    rejection_reasons = _build_rejection_reasons(
        errors=prediction.errors,
        predicted_status=prediction.predicted_status,
        deterministic_overall_status=prediction.deterministic_overall_status,
        prediction_matches_deterministic=prediction.prediction_matches_deterministic,
    )
    advisory_signal_usable = (
        not prediction.errors
        and prediction.predicted_status is not None
        and prediction.prediction_matches_deterministic is True
        and prediction.deterministic_overall_status == "pass"
        and prediction.ml_is_advisory_only
        and prediction.deterministic_checks_required
        and prediction.requires_engineer_review
    )
    audit_status = _audit_status(
        rejection_reasons=rejection_reasons,
        warnings=tuple(warnings),
        prediction_matches_deterministic=prediction.prediction_matches_deterministic,
        deterministic_overall_status=prediction.deterministic_overall_status,
    )
    status = _overall_status(audit_status, tuple(warnings), prediction.errors)
    json_data = _json_data(
        status=status,
        audit_status=audit_status,
        prediction=prediction,
        advisory_signal_usable=advisory_signal_usable,
        rejection_reasons=tuple(rejection_reasons),
        warnings=tuple(warnings),
    )
    markdown = _markdown_report(json_data)

    return NeuralAdvisorySafetyAuditResult(
        status=status,
        audit_status=audit_status,
        source_dataset=prediction.source_dataset,
        input_json_path=prediction.input_json_path,
        target=prediction.target,
        feature_mode=prediction.feature_mode,
        predicted_status=prediction.predicted_status,
        prediction_confidence=prediction.prediction_confidence,
        deterministic_strength_status=prediction.deterministic_strength_status,
        deterministic_serviceability_status=prediction.deterministic_serviceability_status,
        deterministic_overall_status=prediction.deterministic_overall_status,
        prediction_matches_deterministic=prediction.prediction_matches_deterministic,
        advisory_signal_usable=advisory_signal_usable,
        rejection_reasons=tuple(rejection_reasons),
        warnings=tuple(warnings),
        errors=prediction.errors,
        markdown=markdown,
        json_data=json_data,
        deterministic_report_required=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        requires_engineer_review=True,
        neural_network_used=prediction.neural_network_used,
    )


def _build_rejection_reasons(
    *,
    errors: tuple[str, ...],
    predicted_status: str | None,
    deterministic_overall_status: str,
    prediction_matches_deterministic: bool | None,
) -> list[str]:
    reasons: list[str] = []
    for error in errors:
        reasons.append(f"K48 neural advisory prediction returned error: {error}")
    if predicted_status is None:
        reasons.append("neural advisory prediction was not produced")
    if deterministic_overall_status in {"fail", "review_or_fail"}:
        reasons.append(f"deterministic overall status is {deterministic_overall_status}")
    if prediction_matches_deterministic is False:
        reasons.append(PREDICTION_MISMATCH_WARNING)
    return list(dict.fromkeys(reasons))


def _audit_status(
    *,
    rejection_reasons: list[str],
    warnings: tuple[str, ...],
    prediction_matches_deterministic: bool | None,
    deterministic_overall_status: str,
) -> str:
    if rejection_reasons:
        return "fail"
    if prediction_matches_deterministic is not True or deterministic_overall_status != "pass":
        return "fail"
    review_markers = (
        SMALL_DATASET_WARNING,
        DETERMINISTIC_DERIVED_WARNING,
        MATERIAL_VERIFICATION_WARNING,
        EXTERNAL_VALIDATION_WARNING,
        "metrics and predictions are not production evidence",
    )
    if any(marker in warnings for marker in review_markers):
        return "review_required"
    return "pass"


def _overall_status(
    audit_status: str,
    warnings: tuple[str, ...],
    errors: tuple[str, ...],
) -> str:
    if errors or audit_status == "fail":
        return "fail"
    if warnings or audit_status == "review_required":
        return "review_required"
    return "pass"


def _json_data(
    *,
    status: str,
    audit_status: str,
    prediction,
    advisory_signal_usable: bool,
    rejection_reasons: tuple[str, ...],
    warnings: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "report_type": "neural_advisory_safety_audit",
        "status": status,
        "audit_status": audit_status,
        "source_dataset": prediction.source_dataset,
        "input_json_path": prediction.input_json_path,
        "target": prediction.target,
        "feature_mode": prediction.feature_mode,
        "predicted_status": prediction.predicted_status,
        "prediction_confidence": prediction.prediction_confidence,
        "class_probabilities": prediction.class_probabilities,
        "deterministic_strength_status": prediction.deterministic_strength_status,
        "deterministic_serviceability_status": (
            prediction.deterministic_serviceability_status
        ),
        "deterministic_overall_status": prediction.deterministic_overall_status,
        "prediction_matches_deterministic": prediction.prediction_matches_deterministic,
        "advisory_signal_usable": advisory_signal_usable,
        "rejection_reasons": list(rejection_reasons),
        "warnings": list(warnings),
        "errors": list(prediction.errors),
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "deterministic_report_required": True,
        "neural_network_used": prediction.neural_network_used,
    }


def _markdown_report(data: dict[str, Any]) -> str:
    probabilities = data.get("class_probabilities") or {}
    rejection_reasons = data.get("rejection_reasons") or []
    warnings = data.get("warnings") or []
    errors = data.get("errors") or []
    lines = [
        "# Neural Advisory Safety Audit",
        "",
        (
            "This audit is advisory-only. It is not a design calculation. "
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
        f"- deterministic_strength_status: `{data['deterministic_strength_status']}`",
        (
            "- deterministic_serviceability_status: "
            f"`{data['deterministic_serviceability_status']}`"
        ),
        f"- deterministic_overall_status: `{data['deterministic_overall_status']}`",
        "",
        "## Comparison",
        "",
        (
            "- prediction_matches_deterministic: "
            f"`{data['prediction_matches_deterministic']}`"
        ),
        f"- advisory_signal_usable: `{data['advisory_signal_usable']}`",
        f"- audit_status: `{data['audit_status']}`",
        f"- status: `{data['status']}`",
        "",
        "## Rejection reasons",
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
        "- small datasets are not reliable production ML evidence",
        "- metrics and predictions are not production evidence",
        "- ML is advisory-only",
        "- deterministic SP63 verification is mandatory",
        "- engineer review is required",
        "- material verification and external validation remain separate",
        "",
    ]
    return "\n".join(lines)


def _bullet_lines(values: list[Any]) -> list[str]:
    return [f"- {value}" for value in values]
