"""Guided synthetic input generation for class-balanced report datasets."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.design import design_rectangular_element
from sp63_core.report import rectangular_design_input_from_mapping

GUIDED_SYNTHETIC_INPUT_GENERATOR = "guided_synthetic_inputs"
SUPPORTED_GUIDED_TARGET_CLASSES = ("pass", "fail", "review_or_fail")


@dataclass(frozen=True)
class GuidedSyntheticGenerationResult:
    """Result of deterministic-guided synthetic input generation."""

    status: str
    output_dir: str
    target_distribution_goal: dict[str, int]
    generated_count: int
    accepted_count: int
    rejected_count: int
    final_distribution: dict[str, int]
    seed: int
    max_attempts: int
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    synthetic_data_only: bool = True
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True


def generate_guided_synthetic_inputs(
    *,
    output_dir: Path,
    target_distribution_goal: Mapping[str, int],
    seed: int = 42,
    max_attempts: int = 1000,
    include_serviceability: bool = True,
) -> GuidedSyntheticGenerationResult:
    """Generate synthetic report inputs toward a requested deterministic status mix."""
    goal = _normalize_target_goal(target_distribution_goal)
    if max_attempts <= 0:
        raise ValueError("max_attempts must be positive")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    _remove_previous_guided_inputs(output)

    rng = random.Random(seed)
    final_distribution: Counter[str] = Counter()
    manifest_cases: list[dict[str, Any]] = []
    attempts = 0
    rejected_count = 0

    while attempts < max_attempts and not _goal_reached(goal, final_distribution):
        attempts += 1
        desired_status = _select_desired_status(goal, final_distribution, rng)
        payload = _build_guided_candidate_payload(
            rng=rng,
            desired_status=desired_status,
            attempt=attempts,
            include_serviceability=include_serviceability,
        )
        actual_status = _classify_candidate(payload)
        if final_distribution.get(actual_status, 0) >= goal.get(actual_status, 0):
            rejected_count += 1
            continue

        case_index = sum(final_distribution.values()) + 1
        case_id = f"case_{case_index:04d}"
        case_path = output / f"{case_id}.json"
        _write_json(case_path, payload)
        final_distribution[actual_status] += 1
        manifest_cases.append(
            {
                "case_id": case_id,
                "path": case_path.name,
                "sha256": _compute_file_sha256(case_path),
                "overall_status": actual_status,
                "desired_status": desired_status,
                "attempt": attempts,
                "input_summary": _input_summary(payload),
            }
        )

    readme_path = output / "README_GUIDED_SYNTHETIC.md"
    readme_path.write_text(
        _render_guided_synthetic_readme(
            target_distribution_goal=goal,
            final_distribution=dict(final_distribution),
            seed=seed,
            max_attempts=max_attempts,
            include_serviceability=include_serviceability,
        ),
        encoding="utf-8",
    )
    manifest = {
        "generator": GUIDED_SYNTHETIC_INPUT_GENERATOR,
        "target_distribution_goal": goal,
        "final_distribution": dict(final_distribution),
        "seed": seed,
        "max_attempts": max_attempts,
        "generated_count": attempts,
        "accepted_count": sum(final_distribution.values()),
        "rejected_count": rejected_count,
        "synthetic_data_only": True,
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "include_serviceability": include_serviceability,
        "readme": {
            "path": readme_path.name,
            "sha256": _compute_file_sha256(readme_path),
        },
        "cases": manifest_cases,
    }
    _write_json(output / "guided_synthetic_manifest.json", manifest)

    warnings: list[str] = []
    if not _goal_reached(goal, final_distribution):
        warnings.append("target distribution goal was not fully reached")
    if not include_serviceability and goal.get("review_or_fail", 0) > 0:
        warnings.append("review_or_fail target is unlikely without serviceability checks")

    status = "pass" if not warnings else "review_required"
    return GuidedSyntheticGenerationResult(
        status=status,
        output_dir=str(output),
        target_distribution_goal=goal,
        generated_count=attempts,
        accepted_count=sum(final_distribution.values()),
        rejected_count=rejected_count,
        final_distribution=dict(final_distribution),
        seed=seed,
        max_attempts=max_attempts,
        warnings=tuple(warnings),
        errors=(),
    )


def _normalize_target_goal(target_distribution_goal: Mapping[str, int]) -> dict[str, int]:
    unknown = tuple(
        sorted(
            class_name
            for class_name in target_distribution_goal
            if class_name not in SUPPORTED_GUIDED_TARGET_CLASSES
        )
    )
    if unknown:
        raise ValueError(
            "target_distribution_goal contains unsupported classes: " + ", ".join(unknown)
        )
    goal = {
        class_name: int(target_distribution_goal.get(class_name, 0))
        for class_name in SUPPORTED_GUIDED_TARGET_CLASSES
    }
    if any(count < 0 for count in goal.values()):
        raise ValueError("target_distribution_goal counts must be non-negative")
    if sum(goal.values()) <= 0:
        raise ValueError("target_distribution_goal must request at least one case")
    return goal


def _goal_reached(goal: dict[str, int], distribution: Counter[str]) -> bool:
    return all(
        distribution.get(class_name, 0) >= goal_count
        for class_name, goal_count in goal.items()
    )


def _select_desired_status(
    goal: dict[str, int],
    distribution: Counter[str],
    rng: random.Random,
) -> str:
    deficits = {
        class_name: goal_count - distribution.get(class_name, 0)
        for class_name, goal_count in goal.items()
        if goal_count > distribution.get(class_name, 0)
    }
    max_deficit = max(deficits.values())
    candidates = [class_name for class_name, deficit in deficits.items() if deficit == max_deficit]
    return rng.choice(candidates)


def _build_guided_candidate_payload(
    *,
    rng: random.Random,
    desired_status: str,
    attempt: int,
    include_serviceability: bool,
) -> dict[str, Any]:
    if desired_status == "pass":
        payload = _pass_candidate(rng)
    elif desired_status == "fail":
        payload = _fail_candidate(rng)
    elif desired_status == "review_or_fail":
        payload = _review_candidate(rng)
    else:
        raise ValueError("desired_status must be pass, fail, or review_or_fail")

    payload["load_duration"] = rng.choice(("short", "short", "short", "long"))
    if include_serviceability:
        _add_serviceability_fields(payload, rng=rng, desired_status=desired_status)
    return payload


def _pass_candidate(rng: random.Random) -> dict[str, Any]:
    return {
        "b": rng.choice((400, 450, 500)),
        "h": rng.choice((650, 700, 800, 900)),
        "cover": rng.choice((25, 30, 32)),
        "stirrup_diameter_for_geometry": rng.choice((6, 8)),
        "concrete_class": rng.choice(("B30", "B35")),
        "longitudinal_rebar_class": rng.choice(("A500", "A500", "A400")),
        "stirrup_rebar_class": rng.choice(("A400", "A240")),
        "M": rng.choice((40, 60, 80, 100, 120)) * 1_000_000,
        "Q": rng.choice((20, 35, 50, 65, 80)) * 1_000,
    }


def _fail_candidate(rng: random.Random) -> dict[str, Any]:
    return {
        "b": rng.choice((200, 250)),
        "h": rng.choice((300, 350, 400)),
        "cover": rng.choice((40, 45, 50)),
        "stirrup_diameter_for_geometry": rng.choice((10, 12)),
        "concrete_class": rng.choice(("B20", "B25")),
        "longitudinal_rebar_class": rng.choice(("A400", "A500")),
        "stirrup_rebar_class": rng.choice(("A240", "A400")),
        "M": rng.choice((350, 400, 450, 500, 550, 600)) * 1_000_000,
        "Q": rng.choice((220, 250, 300, 350, 400)) * 1_000,
    }


def _review_candidate(rng: random.Random) -> dict[str, Any]:
    moment_knm = rng.choice((80, 90, 100, 110, 120, 140))
    return {
        "b": rng.choice((300, 350, 400)),
        "h": rng.choice((500, 550, 600, 650)),
        "cover": rng.choice((30, 32, 35)),
        "stirrup_diameter_for_geometry": rng.choice((8, 10)),
        "concrete_class": rng.choice(("B25", "B30")),
        "longitudinal_rebar_class": rng.choice(("A500", "A400")),
        "stirrup_rebar_class": rng.choice(("A240", "A400")),
        "M": moment_knm * 1_000_000,
        "Q": rng.choice((40, 50, 60, 75, 90)) * 1_000,
    }


def _add_serviceability_fields(
    payload: dict[str, Any],
    *,
    rng: random.Random,
    desired_status: str,
) -> None:
    if desired_status == "pass":
        service_ratio = rng.choice((0.25, 0.3, 0.35))
        payload.update(
            {
                "Mser": round(payload["M"] * service_ratio, 3),
                "check_cracks": True,
                "check_crack_width": True,
                "check_deflection": True,
                "span": rng.choice((3000, 3500, 4000, 4500, 5000)),
                "acrc_limit": 0.3,
                "deflection_limit_ratio": 250,
            }
        )
        return
    if desired_status == "review_or_fail":
        payload.update(
            {
                "Mser": max(round(payload["M"] * rng.choice((0.75, 0.85, 0.95)), 3), 70_000_000),
                "check_cracks": True,
                "check_crack_width": False,
                "check_deflection": False,
                "span": rng.choice((6500, 7000, 7500, 8000, 8500, 9000)),
                "acrc_limit": 0.3,
                "deflection_limit_ratio": 250,
            }
        )
        return
    payload.update(
        {
            "Mser": round(payload["M"] * rng.choice((0.7, 0.8, 0.9)), 3),
            "check_cracks": True,
            "check_crack_width": True,
            "check_deflection": True,
            "span": rng.choice((7000, 8000, 9000)),
            "acrc_limit": 0.3,
            "deflection_limit_ratio": 250,
        }
    )


def _classify_candidate(payload: dict[str, Any]) -> str:
    design_input = rectangular_design_input_from_mapping(payload)
    result = design_rectangular_element(design_input)
    return result.overall_status


def _input_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "b": payload["b"],
        "h": payload["h"],
        "concrete_class": payload["concrete_class"],
        "longitudinal_rebar_class": payload["longitudinal_rebar_class"],
        "stirrup_rebar_class": payload["stirrup_rebar_class"],
        "M": payload["M"],
        "Q": payload["Q"],
        "Mser": payload.get("Mser"),
        "span": payload.get("span"),
        "check_cracks": payload.get("check_cracks", False),
        "check_crack_width": payload.get("check_crack_width", False),
        "check_deflection": payload.get("check_deflection", False),
    }


def _remove_previous_guided_inputs(output_dir: Path) -> None:
    for path in output_dir.glob("case_*.json"):
        path.unlink()
    for name in ("README_GUIDED_SYNTHETIC.md", "guided_synthetic_manifest.json"):
        path = output_dir / name
        if path.exists():
            path.unlink()


def _render_guided_synthetic_readme(
    *,
    target_distribution_goal: dict[str, int],
    final_distribution: dict[str, int],
    seed: int,
    max_attempts: int,
    include_serviceability: bool,
) -> str:
    return "\n".join(
        (
            "# Guided synthetic report input cases",
            "",
            "These files are anonymized synthetic design-report input cases generated",
            "for report-derived dataset balancing and ML smoke experiments.",
            "",
            f"- generator: `{GUIDED_SYNTHETIC_INPUT_GENERATOR}`",
            f"- target_distribution_goal: `{target_distribution_goal}`",
            f"- final_distribution: `{final_distribution}`",
            f"- seed: `{seed}`",
            f"- max_attempts: `{max_attempts}`",
            f"- include_serviceability: `{include_serviceability}`",
            "- synthetic_data_only: `true`",
            "- requires_engineer_review: `true`",
            "- ml_is_advisory_only: `true`",
            "- deterministic_checks_required: `true`",
            "",
            "Candidates are accepted only according to deterministic SP63 draft",
            "design statuses. ML does not guide generation and is not a design checker.",
            "",
            "Synthetic data does not replace material verification, manual checks, or",
            "external validation with engineer-filled SCAD/LIRA/Excel/manual values.",
            "Large generated report outputs should stay local and should not be committed.",
            "",
        )
    )


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _compute_file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
