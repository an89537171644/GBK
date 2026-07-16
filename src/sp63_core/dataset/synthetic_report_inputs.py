"""Synthetic input generation for report-derived ML smoke datasets."""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SYNTHETIC_REPORT_INPUT_GENERATOR = "synthetic_report_inputs"
SYNTHETIC_DATASET_WARNING = (
    "Synthetic report inputs are deterministic smoke data only and do not replace "
    "external engineering validation."
)


@dataclass(frozen=True)
class SyntheticReportInputGenerationResult:
    """Result of generating synthetic design-report input JSON files."""

    status: str
    output_dir: str
    case_count: int
    generated_count: int
    skipped_count: int
    seed: int
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    completeness_status: str = "incomplete"
    evidence_status: str = "needs_engineer_review"
    project_use_status: str = "prohibited"
    project_use: bool = False
    requires_engineer_review: bool = True
    synthetic_data_only: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True


def generate_synthetic_report_inputs(
    *,
    output_dir: Path,
    case_count: int = 300,
    seed: int = 42,
    include_serviceability: bool = True,
) -> SyntheticReportInputGenerationResult:
    """Generate reproducible synthetic rectangular design-report input cases."""
    if case_count <= 0:
        raise ValueError("case_count must be positive")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    _remove_previous_generated_inputs(output)

    rng = random.Random(seed)
    generated_paths: list[Path] = []
    manifest_cases: list[dict[str, Any]] = []

    for index in range(1, case_count + 1):
        case_id = f"case_{index:04d}"
        payload = _build_case_payload(
            rng=rng,
            index=index,
            include_serviceability=include_serviceability,
        )
        case_path = output / f"{case_id}.json"
        _write_json(case_path, payload)
        generated_paths.append(case_path)
        manifest_cases.append(
            {
                "case_id": case_id,
                "path": case_path.name,
                "sha256": _compute_file_sha256(case_path),
                "input_summary": {
                    "b": payload["b"],
                    "h": payload["h"],
                    "concrete_class": payload["concrete_class"],
                    "longitudinal_rebar_class": payload["longitudinal_rebar_class"],
                    "stirrup_rebar_class": payload["stirrup_rebar_class"],
                    "local_axes_id": payload["local_axes_id"],
                    "moment_axis": payload["moment_axis"],
                    "tension_face": payload["tension_face"],
                    "load_duration": payload["load_duration"],
                    "M": payload["M"],
                    "Q": payload["Q"],
                    "Mser": payload.get("Mser"),
                    "span": payload.get("span"),
                    "check_cracks": payload.get("check_cracks", False),
                    "check_crack_width": payload.get("check_crack_width", False),
                    "check_deflection": payload.get("check_deflection", False),
                },
            }
        )

    readme_path = output / "README_SYNTHETIC.md"
    readme_path.write_text(
        _render_synthetic_readme(
            case_count=case_count,
            seed=seed,
            include_serviceability=include_serviceability,
        ),
        encoding="utf-8",
    )
    manifest = {
        "generator": SYNTHETIC_REPORT_INPUT_GENERATOR,
        "case_count": case_count,
        "seed": seed,
        "synthetic_data_only": True,
        "completeness_status": "incomplete",
        "evidence_status": "needs_engineer_review",
        "project_use_status": "prohibited",
        "project_use": False,
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
    _write_json(output / "synthetic_manifest.json", manifest)

    warnings: tuple[str, ...] = ()
    if not include_serviceability:
        warnings = ("serviceability fields and checks were disabled",)

    return SyntheticReportInputGenerationResult(
        status="pass",
        output_dir=str(output),
        case_count=case_count,
        generated_count=len(generated_paths),
        skipped_count=0,
        seed=seed,
        warnings=warnings,
        errors=(),
    )


def _build_case_payload(
    *,
    rng: random.Random,
    index: int,
    include_serviceability: bool,
) -> dict[str, Any]:
    b = rng.choice((200, 250, 300, 350, 400, 450, 500))
    h = rng.choice((300, 350, 400, 450, 500, 550, 600, 700, 800, 900))
    cover = rng.choice((25, 30, 32, 35, 40, 45, 50))
    stirrup_diameter = rng.choice((6, 8, 10, 12))
    concrete_class = rng.choice(("B20", "B25", "B30", "B35"))
    longitudinal_rebar_class = rng.choice(("A400", "A500"))
    stirrup_rebar_class = rng.choice(("A240", "A400"))
    moment_knm = rng.choice(
        (20, 35, 50, 75, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500)
    )
    shear_kn = rng.choice((20, 35, 50, 75, 100, 125, 150, 200, 250, 300))

    payload: dict[str, Any] = {
        "b": b,
        "h": h,
        "cover": cover,
        "stirrup_diameter_for_geometry": stirrup_diameter,
        "concrete_class": concrete_class,
        "longitudinal_rebar_class": longitudinal_rebar_class,
        "stirrup_rebar_class": stirrup_rebar_class,
        "M": moment_knm * 1_000_000,
        "Q": shear_kn * 1_000,
        "local_axes_id": f"synthetic-report-case-{index:04d}",
        "moment_axis": "local_z",
        "tension_face": "local_y_min",
        "load_duration": "short",
    }

    if include_serviceability:
        service_ratio = rng.uniform(0.3, 0.8)
        pattern = index % 5
        check_cracks = pattern in (1, 2, 3, 4)
        check_crack_width = pattern in (2, 3)
        check_deflection = pattern in (3, 4)
        payload.update(
            {
                "Mser": round(payload["M"] * service_ratio, 3),
                "check_cracks": check_cracks,
                "check_crack_width": check_crack_width,
                "check_deflection": check_deflection,
                "span": rng.choice((3000, 4000, 5000, 6000, 7000, 8000, 9000)),
                "acrc_limit": 0.3,
                "deflection_limit_ratio": 250,
            }
        )

    return payload


def _remove_previous_generated_inputs(output_dir: Path) -> None:
    for path in output_dir.glob("case_*.json"):
        path.unlink()
    for name in ("README_SYNTHETIC.md", "synthetic_manifest.json"):
        path = output_dir / name
        if path.exists():
            path.unlink()


def _render_synthetic_readme(
    *,
    case_count: int,
    seed: int,
    include_serviceability: bool,
) -> str:
    serviceability_text = (
        "Serviceability fields are included with mixed crack, crack-width, and "
        "deflection flags."
        if include_serviceability
        else "Serviceability fields are disabled for this generated set."
    )
    return "\n".join(
        (
            "# Synthetic report input cases",
            "",
            "These files are anonymized synthetic design-report input cases generated for",
            "report-derived dataset and ML smoke experiments.",
            "",
            f"- generator: `{SYNTHETIC_REPORT_INPUT_GENERATOR}`",
            f"- case_count: `{case_count}`",
            f"- seed: `{seed}`",
            "- synthetic_data_only: `true`",
            "- completeness_status: `incomplete`",
            "- evidence_status: `needs_engineer_review`",
            "- project_use_status: `prohibited`",
            "- project_use: `false`",
            "- requires_engineer_review: `true`",
            "- ml_is_advisory_only: `true`",
            "- deterministic_checks_required: `true`",
            f"- serviceability: {serviceability_text}",
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
