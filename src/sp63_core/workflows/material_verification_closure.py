"""Material verification closure workflow for v0.9 review gates."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from sp63_core.materials import build_material_verification_report
from sp63_core.materials.audit import build_material_audit_rows

MATERIAL_VERIFICATION_CLOSURE_WARNING = (
    "material verification closure is an engineering review gate only. It does "
    "not update material catalog values or approve project use."
)
REJECTED_VERIFICATION_STATUSES = {"reject", "rejected", "fail", "failed"}


@dataclass(frozen=True)
class MaterialVerificationClosureResult:
    """Material verification closure result."""

    status: str
    closure_status: str
    material_verification_csv: str | None
    output_dir: str | None
    required_material_keys: tuple[str, ...]
    verified_material_keys: tuple[str, ...]
    missing_material_keys: tuple[str, ...]
    rejected_material_keys: tuple[str, ...]
    review_required_material_keys: tuple[str, ...]
    coverage_ratio: float
    material_ready_for_engineering_review: bool
    material_ready_for_project_use: bool
    generated_files: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True


def build_material_verification_closure(
    *,
    material_verification_csv: Path | None = None,
    output_dir: Path | None = None,
) -> MaterialVerificationClosureResult:
    """Build material verification closure evidence without changing catalogs."""
    required_keys = _required_material_keys()
    warnings: list[str] = [MATERIAL_VERIFICATION_CLOSURE_WARNING]
    errors: list[str] = []
    verified_keys: tuple[str, ...] = ()
    missing_keys = required_keys
    rejected_keys: tuple[str, ...] = ()
    review_required_keys: tuple[str, ...] = ()
    csv_path = None if material_verification_csv is None else Path(material_verification_csv)

    if csv_path is None:
        warnings.append("material verification CSV is not provided")
    else:
        try:
            rows = _load_material_verification_csv(csv_path)
            verification_report = build_material_verification_report(rows)
            warnings.extend(verification_report.warnings)
            verified_keys = tuple(
                _material_key(row.material_type, row.class_name, row.property_name)
                for row in verification_report.rows
                if row.verification_status == "engineer_verified"
            )
            rejected_keys = _rejected_material_keys(rows)
            present_keys = tuple(
                _material_key(row.material_type, row.class_name, row.property_name)
                for row in verification_report.rows
            )
            missing_keys = tuple(key for key in required_keys if key not in present_keys)
            review_required_keys = tuple(
                key
                for key in required_keys
                if key not in verified_keys and key not in missing_keys and key not in rejected_keys
            )
            if missing_keys:
                warnings.append("material verification CSV does not cover every catalog row")
            if review_required_keys:
                warnings.append("material verification CSV has rows still requiring review")
            if rejected_keys:
                errors.append("material verification CSV contains rejected material rows")
        except (FileNotFoundError, ValueError, OSError) as exc:
            errors.append(f"material verification CSV cannot be read: {exc}")
            warnings.append("material verification CSV could not be used for closure")

    coverage_ratio = 0.0 if not required_keys else len(verified_keys) / len(required_keys)
    complete_verified_coverage = (
        bool(required_keys)
        and not missing_keys
        and not rejected_keys
        and not review_required_keys
        and len(verified_keys) == len(required_keys)
    )
    material_ready_for_engineering_review = complete_verified_coverage and not errors
    status = _closure_status(
        errors=errors,
        csv_present=csv_path is not None,
        complete_verified_coverage=complete_verified_coverage,
    )

    result = MaterialVerificationClosureResult(
        status=status,
        closure_status=status,
        material_verification_csv=None if csv_path is None else str(csv_path),
        output_dir=None if output_dir is None else str(Path(output_dir)),
        required_material_keys=required_keys,
        verified_material_keys=tuple(sorted(dict.fromkeys(verified_keys))),
        missing_material_keys=tuple(sorted(dict.fromkeys(missing_keys))),
        rejected_material_keys=tuple(sorted(dict.fromkeys(rejected_keys))),
        review_required_material_keys=tuple(sorted(dict.fromkeys(review_required_keys))),
        coverage_ratio=coverage_ratio,
        material_ready_for_engineering_review=material_ready_for_engineering_review,
        material_ready_for_project_use=False,
        generated_files=(),
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(dict.fromkeys(errors)),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
    )
    if output_dir is None:
        return result
    return _write_material_verification_closure(Path(output_dir), result)


def render_material_verification_closure_markdown(
    result: MaterialVerificationClosureResult,
) -> str:
    """Render a material verification closure report as Markdown."""
    lines = [
        "# Material Verification Closure",
        "",
        MATERIAL_VERIFICATION_CLOSURE_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "material_ready_for_project_use = false",
        "",
        "## Summary",
        "",
        f"- closure_status: `{result.closure_status}`",
        f"- material_verification_csv: `{result.material_verification_csv or 'not_provided'}`",
        f"- required_material_keys: `{len(result.required_material_keys)}`",
        f"- verified_material_keys: `{len(result.verified_material_keys)}`",
        f"- missing_material_keys: `{len(result.missing_material_keys)}`",
        f"- rejected_material_keys: `{len(result.rejected_material_keys)}`",
        f"- review_required_material_keys: `{len(result.review_required_material_keys)}`",
        f"- coverage_ratio: `{result.coverage_ratio:.6g}`",
        "- material_ready_for_engineering_review: "
        f"`{str(result.material_ready_for_engineering_review).lower()}`",
        "- material_ready_for_project_use: "
        f"`{str(result.material_ready_for_project_use).lower()}`",
        "",
        "## Missing Material Keys",
        "",
        *_bullet_lines(result.missing_material_keys),
        "",
        "## Rejected Material Keys",
        "",
        *_bullet_lines(result.rejected_material_keys),
        "",
        "## Review Required Material Keys",
        "",
        *_bullet_lines(result.review_required_material_keys),
        "",
        "## Warnings",
        "",
        *_bullet_lines(result.warnings),
        "",
        "## Errors",
        "",
        *_bullet_lines(result.errors),
    ]
    return "\n".join(lines) + "\n"


def _write_material_verification_closure(
    output_dir: Path,
    result: MaterialVerificationClosureResult,
) -> MaterialVerificationClosureResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "material_verification_closure.json"
    markdown_path = output_dir / "material_verification_closure.md"
    readme_path = output_dir / "README_MATERIAL_VERIFICATION_CLOSURE.md"
    generated_files = (str(json_path), str(markdown_path), str(readme_path))
    result_with_files = MaterialVerificationClosureResult(
        **{**result.__dict__, "output_dir": str(output_dir), "generated_files": generated_files}
    )
    json_path.write_text(
        json.dumps(
            {"report_type": "material_verification_closure", **result_with_files.__dict__},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    markdown = render_material_verification_closure_markdown(result_with_files)
    markdown_path.write_text(markdown, encoding="utf-8")
    readme_path.write_text(_render_readme(result_with_files), encoding="utf-8")
    return result_with_files


def _render_readme(result: MaterialVerificationClosureResult) -> str:
    return "\n".join(
        [
            "# Material Verification Closure Package",
            "",
            "This package records material verification closure evidence for engineer review.",
            "",
            f"- closure_status: `{result.closure_status}`",
            "- material_ready_for_engineering_review: "
            f"`{str(result.material_ready_for_engineering_review).lower()}`",
            "- material_ready_for_project_use: `false`",
            "",
            "The package does not update material catalog values and does not approve project use.",
            "Engineer review remains mandatory.",
            "",
        ]
    )


def _load_material_verification_csv(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("material verification CSV is missing header")
        return tuple(dict(row) for row in reader)


def _required_material_keys() -> tuple[str, ...]:
    return tuple(
        sorted(
            _material_key(row.material_type, row.class_name, row.property_name)
            for row in build_material_audit_rows()
        )
    )


def _rejected_material_keys(rows: tuple[dict[str, str], ...]) -> tuple[str, ...]:
    rejected: list[str] = []
    for row in rows:
        status = str(row.get("verification_status") or "").strip().lower()
        if status in REJECTED_VERIFICATION_STATUSES:
            rejected.append(
                _material_key(
                    str(row.get("material_type") or "").strip(),
                    str(row.get("class_name") or "").strip(),
                    str(row.get("property_name") or "").strip(),
                )
            )
    return tuple(rejected)


def _closure_status(
    *,
    errors: list[str],
    csv_present: bool,
    complete_verified_coverage: bool,
) -> str:
    if errors:
        return "fail"
    if not csv_present or not complete_verified_coverage:
        return "review_required"
    return "pass"


def _material_key(material_type: str, class_name: str, property_name: str) -> str:
    return f"{material_type}:{class_name}:{property_name}"


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- `{value}`" for value in values] if values else ["- none"]
