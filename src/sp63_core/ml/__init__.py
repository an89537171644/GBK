"""Baseline ML helpers for draft SP 63 surrogate experiments."""

from sp63_core.ml.baseline import (
    BaselineTrainingResult,
    load_baseline_model,
    mean_absolute_percentage_error_safe,
    predict_as_required,
    train_baseline_as_model,
)
from sp63_core.ml.features import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TARGET_AS,
    split_features_target,
    validate_training_dataframe,
)
from sp63_core.ml.neural import NeuralTrainingResult, train_neural_as_model
from sp63_core.ml.safe_suggestions import (
    SafeLongitudinalSuggestion,
    suggest_checked_longitudinal_options,
)

__all__ = [
    "CATEGORICAL_FEATURES",
    "NUMERIC_FEATURES",
    "TARGET_AS",
    "BaselineTrainingResult",
    "NeuralTrainingResult",
    "SafeLongitudinalSuggestion",
    "load_baseline_model",
    "mean_absolute_percentage_error_safe",
    "predict_as_required",
    "split_features_target",
    "suggest_checked_longitudinal_options",
    "train_baseline_as_model",
    "train_neural_as_model",
    "validate_training_dataframe",
]
