"""Feature preparation for the baseline As_required model."""

import pandas as pd

NUMERIC_FEATURES: tuple[str, ...] = ("b", "h", "h0", "M", "Q")
CATEGORICAL_FEATURES: tuple[str, ...] = (
    "concrete_class",
    "rebar_class",
    "stirrup_class",
)
TARGET_AS = "As_required"


def validate_training_dataframe(df: pd.DataFrame) -> None:
    """Validate that a dataset frame can train the baseline model."""
    required_columns = (*NUMERIC_FEATURES, *CATEGORICAL_FEATURES, TARGET_AS)
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")
    if df.empty:
        raise ValueError("training dataframe must not be empty")
    if df[list(required_columns)].isna().any().any():
        raise ValueError("training dataframe contains missing values")


def split_features_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Return feature frame and As_required target series."""
    validate_training_dataframe(df)
    feature_columns = [*NUMERIC_FEATURES, *CATEGORICAL_FEATURES]
    return df[feature_columns].copy(), df[TARGET_AS].copy()
