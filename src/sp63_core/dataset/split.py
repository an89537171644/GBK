"""Reproducible train/validation/test splitting for dataset cases."""

import random
from collections import defaultdict
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
    group_by: str | None = None,
) -> DatasetSplit:
    """Split cases reproducibly without ML dependencies."""
    if not cases:
        raise ValueError("cases must not be empty")
    ratio_sum = train_ratio + validation_ratio + test_ratio
    if abs(ratio_sum - 1.0) > 1e-6:
        raise ValueError("train, validation and test ratios must sum to 1.0")
    if train_ratio < 0 or validation_ratio < 0 or test_ratio < 0:
        raise ValueError("split ratios must be non-negative")

    if group_by is not None:
        return _split_grouped_cases(
            cases=cases,
            train_ratio=train_ratio,
            validation_ratio=validation_ratio,
            seed=seed,
            group_by=group_by,
        )

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


def _split_grouped_cases(
    *,
    cases: Sequence[DatasetCase],
    train_ratio: float,
    validation_ratio: float,
    seed: int,
    group_by: str,
) -> DatasetSplit:
    if group_by != "group_key":
        raise ValueError("only group_by='group_key' is supported")

    cases_by_group: dict[str, list[DatasetCase]] = defaultdict(list)
    for case in cases:
        cases_by_group[_get_group_value(case, group_by)].append(case)

    groups = list(cases_by_group)
    random.Random(seed).shuffle(groups)

    total_groups = len(groups)
    train_group_count = int(total_groups * train_ratio)
    validation_group_count = int(total_groups * validation_ratio)
    train_groups = set(groups[:train_group_count])
    validation_groups = set(
        groups[train_group_count : train_group_count + validation_group_count]
    )

    train: list[DatasetCase] = []
    validation: list[DatasetCase] = []
    test: list[DatasetCase] = []
    for case in cases:
        group_value = _get_group_value(case, group_by)
        if group_value in train_groups:
            train.append(case)
        elif group_value in validation_groups:
            validation.append(case)
        else:
            test.append(case)

    return DatasetSplit(
        train=tuple(train),
        validation=tuple(validation),
        test=tuple(test),
    )


def _get_group_value(case: DatasetCase, group_by: str) -> str:
    return str(getattr(case, group_by))
