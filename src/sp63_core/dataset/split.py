"""Reproducible train/validation/test splitting for dataset cases."""

import random
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from sp63_core.dataset.generator import DatasetCase, export_dataset_csv


@dataclass(frozen=True)
class DatasetSplit:
    """Train/validation/test dataset partitions."""

    train: tuple[DatasetCase, ...]
    validation: tuple[DatasetCase, ...]
    test: tuple[DatasetCase, ...]


def split_dataset_cases(
    cases: Sequence[DatasetCase],
    *,
    train_ratio: float = 0.70,
    validation_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> DatasetSplit:
    """Split cases reproducibly without ML dependencies."""
    if not cases:
        raise ValueError("cases must not be empty")
    ratio_sum = train_ratio + validation_ratio + test_ratio
    if abs(ratio_sum - 1.0) > 1e-6:
        raise ValueError("train, validation and test ratios must sum to 1.0")
    if train_ratio < 0 or validation_ratio < 0 or test_ratio < 0:
        raise ValueError("split ratios must be non-negative")

    shuffled_cases = list(cases)
    random.Random(seed).shuffle(shuffled_cases)

    total = len(shuffled_cases)
    train_count = int(total * train_ratio)
    validation_count = int(total * validation_ratio)
    train_end = train_count
    validation_end = train_end + validation_count

    return DatasetSplit(
        train=tuple(shuffled_cases[:train_end]),
        validation=tuple(shuffled_cases[train_end:validation_end]),
        test=tuple(shuffled_cases[validation_end:]),
    )


def export_dataset_split_csv(
    split: DatasetSplit,
    output_dir: str | Path,
    *,
    prefix: str = "dataset_v001",
) -> dict[str, Path]:
    """Export train, validation and test CSV files."""
    base_dir = Path(output_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "train": base_dir / f"{prefix}_train.csv",
        "validation": base_dir / f"{prefix}_validation.csv",
        "test": base_dir / f"{prefix}_test.csv",
    }
    export_dataset_csv(split.train, paths["train"])
    export_dataset_csv(split.validation, paths["validation"])
    export_dataset_csv(split.test, paths["test"])
    return paths
