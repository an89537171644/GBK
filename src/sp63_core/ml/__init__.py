"""Experimental ML sandbox exports."""

from sp63_core.ml.baseline import (
    BaselineModelBundle,
    load_baseline_model_bundle,
    predict_baseline_targets,
    save_baseline_model_bundle,
    train_baseline_models,
)
from sp63_core.ml.baseline_report import BaselineMLReport, build_baseline_ml_report
from sp63_core.ml.evaluate import evaluate_baseline_models, evaluate_ml_safety
from sp63_core.ml.features import build_feature_matrix
from sp63_core.ml.neural_surrogate import (
    NeuralSurrogateReport,
    build_neural_surrogate_report,
)
from sp63_core.ml.proposal import MLReinforcementProposal, proposal_from_prediction
from sp63_core.ml.proposal_safety import (
    MLProposal,
    MLProposalVerificationResult,
    verify_ml_proposal_with_deterministic_core,
)
from sp63_core.ml.quality import MLQualityGateResult, evaluate_ml_quality_gate
from sp63_core.ml.readiness import MLReadinessReport, build_ml_readiness_report
from sp63_core.ml.report_baseline import (
    ReportBaselineMLResult,
    build_report_baseline_ml_result,
)
from sp63_core.ml.safety import check_ml_prediction_safety, check_ml_proposal_safety

__all__ = [
    "BaselineModelBundle",
    "BaselineMLReport",
    "MLReadinessReport",
    "MLQualityGateResult",
    "MLReinforcementProposal",
    "MLProposal",
    "MLProposalVerificationResult",
    "NeuralSurrogateReport",
    "ReportBaselineMLResult",
    "build_feature_matrix",
    "build_baseline_ml_report",
    "build_ml_readiness_report",
    "build_neural_surrogate_report",
    "build_report_baseline_ml_result",
    "check_ml_prediction_safety",
    "check_ml_proposal_safety",
    "evaluate_baseline_models",
    "evaluate_ml_quality_gate",
    "evaluate_ml_safety",
    "load_baseline_model_bundle",
    "predict_baseline_targets",
    "proposal_from_prediction",
    "save_baseline_model_bundle",
    "train_baseline_models",
    "verify_ml_proposal_with_deterministic_core",
]
