"""Engineering review ZIP package for advisory ML proposals."""

from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from sp63_core.design import design_rectangular_element
from sp63_core.ml.report_neural_safety_audit import build_neural_advisory_safety_audit
from sp63_core.ml.report_proposal_package import build_ml_proposal_package
from sp63_core.report import build_rectangular_design_report
from sp63_core.report.design_report_input import load_rectangular_design_input_from_json
from sp63_core.report.manifest import compute_file_sha256

PACKAGE_REPORT_TYPE = "ml_proposal_engineering_review_package"
REQUIRED_PACKAGE_FILES = (
    "input.json",
    "deterministic_report.md",
    "deterministic_report.json",
    "deterministic_report.html",
    "neural_safety_audit.md",
    "neural_safety_audit.json",
    "ml_proposal_package.md",
    "ml_proposal_package.json",
    "README_REVIEW.md",
    "manifest.json",
)
MAIN_REVIEW_WARNING = (
    "ML proposal is advisory-only. It is not a design calculation. "
    "Deterministic SP63 verification and engineer review are mandatory."
)


@dataclass(frozen=True)
class MLProposalReviewPackageResult:
    """Result of creating an engineer-facing ML proposal review package."""

    status: str
    package_status: str
    output_dir: str
    zip_path: str | None
    source_dataset: str
    input_json_path: str
    proposal_status: str
    deterministic_overall_status: str
    prediction_matches_deterministic: bool | None
    advisory_signal_usable: bool
    manifest_path: str
    readme_path: str
    file_count: int
    zip_sha256: str | None
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    requires_engineer_review: bool = True


def build_ml_proposal_review_package(
    *,
    dataset_path: Path,
    input_json_path: Path,
    output_dir: Path,
    dataset_format: str | None = None,
    target: str = "overall_status",
    feature_mode: str = "input_only",
    create_zip: bool = True,
    random_state: int = 42,
    hidden_layer_sizes: tuple[int, ...] = (16,),
    max_iter: int = 500,
) -> MLProposalReviewPackageResult:
    """Build an engineer review folder and optional ZIP for one ML proposal."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    input_json = Path(input_json_path)
    dataset = Path(dataset_path)
    errors: list[str] = []

    deterministic_report = _build_deterministic_report(input_json)
    neural_safety_audit = build_neural_advisory_safety_audit(
        dataset_path=dataset,
        dataset_format=dataset_format,
        input_json_path=input_json,
        target=target,
        feature_mode=feature_mode,
        random_state=random_state,
        hidden_layer_sizes=hidden_layer_sizes,
        max_iter=max_iter,
    )
    proposal_package = build_ml_proposal_package(
        dataset_path=dataset,
        dataset_format=dataset_format,
        input_json_path=input_json,
        target=target,
        feature_mode=feature_mode,
        random_state=random_state,
        hidden_layer_sizes=hidden_layer_sizes,
        max_iter=max_iter,
    )

    _write_package_files(
        output=output,
        input_json_path=input_json,
        deterministic_report=deterministic_report,
        neural_safety_audit=neural_safety_audit,
        proposal_package=proposal_package,
    )
    readme_path = output / "README_REVIEW.md"
    readme_path.write_text(
        _build_review_readme(
            output_dir=output,
            dataset_path=dataset,
            input_json_path=input_json,
            proposal_package=proposal_package,
        ),
        encoding="utf-8",
    )

    manifest_path = output / "manifest.json"
    manifest = _build_manifest(
        output=output,
        dataset_path=dataset,
        input_json_path=input_json,
        target=target,
        feature_mode=feature_mode,
        create_zip=create_zip,
        deterministic_report=deterministic_report,
        neural_safety_audit=neural_safety_audit,
        proposal_package=proposal_package,
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    zip_path: Path | None = None
    zip_sha256: str | None = None
    if create_zip:
        zip_path = output.with_suffix(".zip")
        file_count = _write_package_zip(output, zip_path)
        zip_sha256 = compute_file_sha256(zip_path)
        errors.extend(_validate_package_zip(zip_path))
    else:
        file_count = _count_package_files(output)

    warnings = tuple(
        dict.fromkeys(
            (
                *proposal_package.warnings,
                *neural_safety_audit.warnings,
                MAIN_REVIEW_WARNING,
                "ZIP and manifest packaging do not certify the design",
            )
        )
    )
    package_status = "fail" if errors else proposal_package.status
    return MLProposalReviewPackageResult(
        status=package_status,
        package_status=package_status,
        output_dir=str(output),
        zip_path=None if zip_path is None else str(zip_path),
        source_dataset=str(dataset),
        input_json_path=str(input_json),
        proposal_status=proposal_package.proposal_status,
        deterministic_overall_status=proposal_package.deterministic_overall_status,
        prediction_matches_deterministic=proposal_package.prediction_matches_deterministic,
        advisory_signal_usable=proposal_package.advisory_signal_usable,
        manifest_path=str(manifest_path),
        readme_path=str(readme_path),
        file_count=file_count,
        zip_sha256=zip_sha256,
        warnings=warnings,
        errors=tuple(errors),
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        requires_engineer_review=True,
    )


def _build_deterministic_report(input_json_path: Path):
    design_input = load_rectangular_design_input_from_json(input_json_path)
    design_result = design_rectangular_element(design_input)
    return build_rectangular_design_report(design_result, include_html=True)


def _write_package_files(
    *,
    output: Path,
    input_json_path: Path,
    deterministic_report,
    neural_safety_audit,
    proposal_package,
) -> None:
    shutil.copyfile(input_json_path, output / "input.json")
    (output / "deterministic_report.md").write_text(
        deterministic_report.markdown,
        encoding="utf-8",
    )
    (output / "deterministic_report.json").write_text(
        json.dumps(deterministic_report.json_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output / "deterministic_report.html").write_text(
        deterministic_report.html or "",
        encoding="utf-8",
    )
    (output / "neural_safety_audit.md").write_text(
        neural_safety_audit.markdown,
        encoding="utf-8",
    )
    (output / "neural_safety_audit.json").write_text(
        json.dumps(neural_safety_audit.json_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output / "ml_proposal_package.md").write_text(
        proposal_package.markdown,
        encoding="utf-8",
    )
    (output / "ml_proposal_package.json").write_text(
        json.dumps(proposal_package.json_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _build_manifest(
    *,
    output: Path,
    dataset_path: Path,
    input_json_path: Path,
    target: str,
    feature_mode: str,
    create_zip: bool,
    deterministic_report,
    neural_safety_audit,
    proposal_package,
) -> dict[str, Any]:
    return {
        "manifest_version": "1",
        "report_type": PACKAGE_REPORT_TYPE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "command": (
            "python -m sp63_core ml-proposal-review-package "
            f"--dataset {dataset_path} --input-json {input_json_path} "
            f"--output-dir {output}"
        ),
        "source_dataset": str(dataset_path),
        "input_json_path": str(input_json_path),
        "target": target,
        "feature_mode": feature_mode,
        "create_zip": create_zip,
        "status": proposal_package.status,
        "package_status": proposal_package.status,
        "proposal_status": proposal_package.proposal_status,
        "deterministic_strength_status": proposal_package.deterministic_strength_status,
        "deterministic_serviceability_status": proposal_package.deterministic_serviceability_status,
        "deterministic_overall_status": proposal_package.deterministic_overall_status,
        "prediction_matches_deterministic": proposal_package.prediction_matches_deterministic,
        "advisory_signal_usable": proposal_package.advisory_signal_usable,
        "safety_audit_status": proposal_package.safety_audit_status,
        "warnings_count": len(proposal_package.warnings) + len(neural_safety_audit.warnings),
        "files": _manifest_file_records(output),
        "metadata": {
            "deterministic_report_status": deterministic_report.status,
            "neural_safety_audit_status": neural_safety_audit.audit_status,
            "ml_proposal_package_status": proposal_package.status,
            "proposal_accepted": proposal_package.proposal_accepted,
            "proposal_rejected": proposal_package.proposal_rejected,
            "proposal_requires_review": proposal_package.proposal_requires_review,
            "zip_and_manifest_do_not_certify_design": True,
            "material_verification_separate": True,
            "external_validation_separate": True,
        },
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
    }


def _manifest_file_records(output: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for filename in REQUIRED_PACKAGE_FILES:
        path = output / filename
        if not path.exists():
            continue
        records.append(
            {
                "path": filename,
                "sha256": compute_file_sha256(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return records


def _build_review_readme(
    *,
    output_dir: Path,
    dataset_path: Path,
    input_json_path: Path,
    proposal_package,
) -> str:
    lines = [
        "# ML Proposal Engineering Review Package",
        "",
        "requires_engineer_review = true",
        "",
        "## Main warning",
        "",
        MAIN_REVIEW_WARNING,
        "",
        "## Package contents",
        "",
        "- `input.json` - original design input.",
        "- `deterministic_report.md/json/html` - deterministic SP63 design report.",
        "- `neural_safety_audit.md/json` - K49 neural advisory safety audit.",
        "- `ml_proposal_package.md/json` - K50 advisory proposal package.",
        "- `manifest.json` - SHA256 manifest and reproducibility metadata.",
        "- `README_REVIEW.md` - this engineer review guide.",
        "",
        "## Final statuses",
        "",
        f"- proposal_status: `{proposal_package.proposal_status}`",
        f"- deterministic_strength_status: `{proposal_package.deterministic_strength_status}`",
        (
            "- deterministic_serviceability_status: "
            f"`{proposal_package.deterministic_serviceability_status}`"
        ),
        f"- deterministic_overall_status: `{proposal_package.deterministic_overall_status}`",
        (
            "- prediction_matches_deterministic: "
            f"`{proposal_package.prediction_matches_deterministic}`"
        ),
        f"- advisory_signal_usable: `{proposal_package.advisory_signal_usable}`",
        "",
        "## How to verify package",
        "",
        "1. Check `manifest.json` and compare every listed SHA256 checksum.",
        "2. Check the ZIP SHA256 reported by the CLI when ZIP output is enabled.",
        "3. Re-run the deterministic report from `input.json`:",
        "",
        "```bash",
        f"python -m sp63_core design-report --input-json {output_dir / 'input.json'} "
        f"--bundle-output {output_dir / 'deterministic_reproduced'}",
        "```",
        "",
        "4. Re-run the ML proposal package:",
        "",
        "```bash",
        "python -m sp63_core ml-proposal-package "
        f"--dataset {dataset_path} --input-json {input_json_path} --json",
        "```",
        "",
        "## Limitations",
        "",
        "- ML is advisory-only.",
        "- Deterministic SP63 verification is mandatory.",
        "- Engineer review is mandatory.",
        "- Material verification remains separate.",
        "- External validation remains separate.",
        "- Metrics and predictions are not production evidence.",
        "- ZIP and manifest packaging do not certify the design.",
        "- No certification is provided by this package.",
        "- Full SP 63 text is not included.",
        "",
    ]
    return "\n".join(lines)


def _write_package_zip(source: Path, zip_path: Path) -> int:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    file_count = 0
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename in REQUIRED_PACKAGE_FILES:
            path = source / filename
            if not path.exists() or not path.is_file():
                continue
            if _is_unsafe_zip_entry(filename):
                continue
            archive.write(path, filename)
            file_count += 1
    return file_count


def _validate_package_zip(zip_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            bad_file = archive.testzip()
            if bad_file is not None:
                errors.append(f"ZIP internal CRC check failed for: {bad_file}")
            entries = [name for name in archive.namelist() if not name.endswith("/")]
    except zipfile.BadZipFile as exc:
        return [f"invalid ZIP file: {exc}"]

    entry_set = set(entries)
    for entry in entries:
        if _is_unsafe_zip_entry(entry):
            errors.append(f"unsafe ZIP entry path: {entry}")
    for filename in REQUIRED_PACKAGE_FILES:
        if filename not in entry_set:
            errors.append(f"ZIP archive is missing required entry: {filename}")
    return errors


def _count_package_files(output: Path) -> int:
    return sum(1 for filename in REQUIRED_PACKAGE_FILES if (output / filename).is_file())


def _is_unsafe_zip_entry(name: str) -> bool:
    normalized = name.replace("\\", "/")
    posix_path = PurePosixPath(normalized)
    windows_path = PureWindowsPath(name)
    return (
        normalized.startswith("/")
        or posix_path.is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.drive)
        or any(part in {"", ".", ".."} for part in posix_path.parts)
    )
