"""End-to-end engineering workflow runner.

This module orchestrates existing report, archive, ZIP, and advisory ML
readiness helpers. It does not change deterministic calculation logic.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from sp63_core.design import design_rectangular_element
from sp63_core.ml import build_engineering_ml_readiness_bundle
from sp63_core.report import (
    build_rectangular_design_report,
    build_report_manifest,
    build_review_readme_for_single_bundle,
    export_report_archive_to_zip,
    load_rectangular_design_input_from_json,
    validate_report_bundle,
    write_report_manifest_json,
)
from sp63_core.workflows.input_preflight import run_input_preflight
from sp63_core.workflows.static_report_index import build_static_workflow_report_index

WORKFLOW_WARNING = (
    "This workflow does not certify the design. Deterministic SP63 verification "
    "and engineer review are mandatory. ML, if included, is advisory-only."
)
ML_DATASET_MISSING_WARNING = "ML readiness requested but dataset_path was not provided"


@dataclass(frozen=True)
class EngineeringWorkflowResult:
    """Summary of the end-to-end engineering workflow run."""

    status: str
    workflow_status: str
    input_json_path: str
    output_dir: str
    deterministic_report_status: str
    archive_validation_status: str
    zip_status: str
    ml_readiness_status: str | None
    ml_ready_for_research: bool | None
    ml_ready_for_engineering_review: bool | None
    ml_ready_for_project_use: bool | None
    files_created: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    completeness_status: str = "incomplete"
    evidence_status: str = "needs_engineer_review"
    project_use_status: str = "prohibited"
    project_use: bool = False
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    index_status: str | None = None
    index_path: str | None = None
    preflight_status: str | None = None
    preflight_report_json_path: str | None = None
    preflight_report_markdown_path: str | None = None
    preflight_errors_count: int = 0
    preflight_warnings_count: int = 0


def run_engineering_workflow(
    *,
    input_json_path: Path,
    output_dir: Path,
    dataset_path: Path | None = None,
    dataset_format: str | None = None,
    external_validation_csv: Path | None = None,
    material_verification_csv: Path | None = None,
    include_ml_readiness: bool = False,
    create_zip: bool = True,
    with_index: bool = False,
    with_preflight: bool = False,
) -> EngineeringWorkflowResult:
    """Run the deterministic report workflow and optional advisory ML readiness."""
    input_path = Path(input_json_path)
    root_output = Path(output_dir)
    deterministic_dir = root_output / "deterministic_report"
    ml_output_dir = root_output / "ml_readiness"
    zip_path = root_output / "deterministic_report.zip"

    root_output.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = [WORKFLOW_WARNING]
    errors: list[str] = []
    files_created: list[str] = []

    deterministic_report_status = "not_run"
    archive_validation_status = "not_run"
    zip_status = "skipped"
    ml_readiness_status: str | None = None
    ml_ready_for_research: bool | None = None
    ml_ready_for_engineering_review: bool | None = None
    ml_ready_for_project_use: bool | None = False

    preflight_status: str | None = None
    preflight_report_json_path: str | None = None
    preflight_report_markdown_path: str | None = None
    preflight_errors_count = 0
    preflight_warnings_count = 0

    if with_preflight:
        preflight_result = run_input_preflight(input_path, output_dir=root_output)
        preflight_status = preflight_result.preflight_status
        preflight_report_json_path = str(root_output / "input_preflight_report.json")
        preflight_report_markdown_path = str(root_output / "input_preflight_report.md")
        preflight_errors_count = preflight_result.error_count
        preflight_warnings_count = preflight_result.warning_count
        _append_existing(
            files_created,
            (
                root_output / "input_preflight_report.json",
                root_output / "input_preflight_report.md",
            ),
        )
        warnings.extend(f"preflight: {warning}" for warning in preflight_result.warnings)
        errors.extend(f"preflight: {error}" for error in preflight_result.errors)

    if preflight_status == "fail":
        deterministic_report_status = "skipped"
        archive_validation_status = "skipped"
        zip_status = "skipped"
    else:
        try:
            report = _build_and_write_deterministic_report(
                input_json_path=input_path,
                output_dir=deterministic_dir,
                files_created=files_created,
            )
            deterministic_report_status = report.status
        except (OSError, ValueError) as exc:
            errors.append(f"deterministic report failed: {exc}")

    if not errors:
        archive_validation = validate_report_bundle(deterministic_dir)
        archive_validation_status = archive_validation.status
        warnings.extend(archive_validation.warnings)
        errors.extend(f"archive validation: {error}" for error in archive_validation.errors)

    if not errors and create_zip:
        zip_result = export_report_archive_to_zip(
            source_path=deterministic_dir,
            zip_path=zip_path,
        )
        zip_status = zip_result.status
        warnings.extend(zip_result.warnings)
        errors.extend(f"zip export: {error}" for error in zip_result.errors)
        if zip_path.exists():
            files_created.append(str(zip_path))

    if include_ml_readiness:
        if preflight_status == "fail":
            ml_readiness_status = "skipped"
        elif dataset_path is None:
            ml_readiness_status = "not_run"
            warnings.append(ML_DATASET_MISSING_WARNING)
        else:
            ml_result = build_engineering_ml_readiness_bundle(
                dataset_path=Path(dataset_path),
                output_dir=ml_output_dir,
                dataset_format=dataset_format,
                external_validation_csv=external_validation_csv,
                material_verification_csv=material_verification_csv,
            )
            ml_readiness_status = ml_result.status
            ml_ready_for_research = ml_result.ml_ready_for_research
            ml_ready_for_engineering_review = ml_result.ml_ready_for_engineering_review
            ml_ready_for_project_use = ml_result.ml_ready_for_project_use
            warnings.extend(ml_result.warnings)
            errors.extend(f"ml readiness: {error}" for error in ml_result.errors)
            _append_existing(
                files_created,
                (
                    ml_output_dir / "engineering_ml_readiness.md",
                    ml_output_dir / "engineering_ml_readiness.json",
                    ml_output_dir / "engineering_ml_readiness_matrix.csv",
                    ml_output_dir / "README_REVIEW.md",
                ),
            )

    workflow_status = _workflow_status(
        errors=errors,
        deterministic_report_status=deterministic_report_status,
        archive_validation_status=archive_validation_status,
        zip_status=zip_status,
        ml_readiness_status=ml_readiness_status,
        include_ml_readiness=include_ml_readiness,
        preflight_status=preflight_status,
    )

    summary_json_path = root_output / "workflow_summary.json"
    summary_markdown_path = root_output / "workflow_summary.md"
    workflow_readme_path = root_output / "README_WORKFLOW.md"
    files_created.extend(
        str(path) for path in (summary_json_path, summary_markdown_path, workflow_readme_path)
    )

    result = EngineeringWorkflowResult(
        status=workflow_status,
        workflow_status=workflow_status,
        input_json_path=str(input_path),
        output_dir=str(root_output),
        deterministic_report_status=deterministic_report_status,
        archive_validation_status=archive_validation_status,
        zip_status=zip_status,
        ml_readiness_status=ml_readiness_status,
        ml_ready_for_research=ml_ready_for_research,
        ml_ready_for_engineering_review=ml_ready_for_engineering_review,
        ml_ready_for_project_use=ml_ready_for_project_use,
        files_created=tuple(dict.fromkeys(files_created)),
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        preflight_status=preflight_status,
        preflight_report_json_path=preflight_report_json_path,
        preflight_report_markdown_path=preflight_report_markdown_path,
        preflight_errors_count=preflight_errors_count,
        preflight_warnings_count=preflight_warnings_count,
    )

    summary_json_path.write_text(
        json.dumps(_workflow_summary_payload(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary_markdown_path.write_text(_render_workflow_summary_markdown(result), encoding="utf-8")
    workflow_readme_path.write_text(
        _render_workflow_readme(
            result,
            deterministic_dir=deterministic_dir,
            zip_path=zip_path,
            ml_output_dir=ml_output_dir if include_ml_readiness and dataset_path else None,
            index_path=Path(result.index_path) if result.index_path else None,
        ),
        encoding="utf-8",
    )

    if with_index:
        index_result = build_static_workflow_report_index(
            workflow_dir=root_output,
            output_path=root_output / "index.html",
        )
        files_created_with_index = tuple(
            dict.fromkeys((*result.files_created, index_result.output_path))
        )
        warnings_with_index = tuple(dict.fromkeys((*result.warnings, *index_result.warnings)))
        errors_with_index = tuple(
            dict.fromkeys(
                (
                    *result.errors,
                    *(f"static report index: {error}" for error in index_result.errors),
                )
            )
        )
        workflow_status_with_index = _workflow_status_with_index(
            workflow_status=result.workflow_status,
            index_status=index_result.index_status,
            index_errors=index_result.errors,
        )
        result = replace(
            result,
            status=workflow_status_with_index,
            workflow_status=workflow_status_with_index,
            index_status=index_result.index_status,
            index_path=index_result.output_path,
            files_created=files_created_with_index,
            warnings=warnings_with_index,
            errors=errors_with_index,
        )
        summary_json_path.write_text(
            json.dumps(_workflow_summary_payload(result), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        summary_markdown_path.write_text(
            _render_workflow_summary_markdown(result),
            encoding="utf-8",
        )
        workflow_readme_path.write_text(
            _render_workflow_readme(
                result,
                deterministic_dir=deterministic_dir,
                zip_path=zip_path,
                ml_output_dir=ml_output_dir if include_ml_readiness and dataset_path else None,
                index_path=Path(result.index_path) if result.index_path else None,
            ),
            encoding="utf-8",
        )

    return result


def _build_and_write_deterministic_report(
    *,
    input_json_path: Path,
    output_dir: Path,
    files_created: list[str],
) -> Any:
    design_input = load_rectangular_design_input_from_json(input_json_path)
    design_result = design_rectangular_element(design_input)
    report = build_rectangular_design_report(design_result, include_html=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = output_dir / "report.md"
    json_path = output_dir / "report.json"
    html_path = output_dir / "report.html"
    input_copy_path = output_dir / "input.json"
    manifest_path = output_dir / "manifest.json"
    readme_path = output_dir / "README_REVIEW.md"

    markdown_path.write_text(report.markdown, encoding="utf-8")
    json_path.write_text(
        json.dumps(_design_report_payload(report), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    html_path.write_text(report.html or "", encoding="utf-8")
    shutil.copyfile(input_json_path, input_copy_path)

    output_paths = (markdown_path, json_path, html_path, input_copy_path)
    manifest = build_report_manifest(
        report_type=report.report_type,
        command="engineering-workflow deterministic-report",
        input_paths=(input_json_path,),
        output_paths=output_paths,
        status=report.status,
        strength_status=report.strength_status,
        serviceability_status=report.serviceability_status,
        overall_status=report.overall_status,
        warnings_count=len(report.warnings),
        metadata={"workflow": "engineering-workflow"},
        completeness_status=report.completeness_status,
        evidence_status=report.evidence_status,
        project_use_status=report.project_use_status,
    )
    write_report_manifest_json(manifest, manifest_path)
    readme_path.write_text(
        build_review_readme_for_single_bundle(
            bundle_path=output_dir,
            manifest_path=manifest_path,
        ),
        encoding="utf-8",
    )
    manifest = build_report_manifest(
        report_type=report.report_type,
        command="engineering-workflow deterministic-report",
        input_paths=(input_json_path,),
        output_paths=(*output_paths, readme_path),
        status=report.status,
        strength_status=report.strength_status,
        serviceability_status=report.serviceability_status,
        overall_status=report.overall_status,
        warnings_count=len(report.warnings),
        metadata={"workflow": "engineering-workflow"},
        completeness_status=report.completeness_status,
        evidence_status=report.evidence_status,
        project_use_status=report.project_use_status,
    )
    write_report_manifest_json(manifest, manifest_path)

    files_created.extend(
        str(path)
        for path in (
            input_copy_path,
            markdown_path,
            json_path,
            html_path,
            manifest_path,
            readme_path,
        )
    )
    return report


def _design_report_payload(report: Any) -> dict[str, Any]:
    data = report.json_data
    return {
        "command": "engineering-workflow deterministic-report",
        "source": "input_json",
        "report_type": report.report_type,
        "status": report.status,
        "strength_status": report.strength_status,
        "serviceability_status": report.serviceability_status,
        "overall_status": report.overall_status,
        "status_scope": report.status_scope,
        "completeness_status": report.completeness_status,
        "evidence_status": report.evidence_status,
        "project_use_status": report.project_use_status,
        "project_use": report.project_use,
        "requires_engineer_review": report.requires_engineer_review,
        "warnings": list(report.warnings),
        "input_data": data["input_data"],
        "materials": data["materials"],
        "geometry": data["geometry"],
        "reinforcement": data["reinforcement"],
        "checks": data["checks"],
        "limitations": data["limitations"],
        "report": data,
    }


def _workflow_status(
    *,
    errors: list[str],
    deterministic_report_status: str,
    archive_validation_status: str,
    zip_status: str,
    ml_readiness_status: str | None,
    include_ml_readiness: bool,
    preflight_status: str | None,
) -> str:
    if preflight_status == "fail":
        return "fail"
    if errors or archive_validation_status == "fail" or zip_status == "fail":
        return "fail"
    if preflight_status == "review_required":
        return "review_required"
    if deterministic_report_status == "fail":
        return "review_required"
    if include_ml_readiness and ml_readiness_status in {"fail", "review_required", "not_run"}:
        return "review_required"
    return "review_required"


def _workflow_status_with_index(
    *,
    workflow_status: str,
    index_status: str,
    index_errors: tuple[str, ...],
) -> str:
    if index_errors or index_status == "fail":
        return "fail"
    if workflow_status == "fail":
        return "fail"
    if workflow_status == "review_required" or index_status == "review_required":
        return "review_required"
    return workflow_status


def _workflow_summary_payload(result: EngineeringWorkflowResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["report_type"] = "engineering_workflow_summary"
    return payload


def _render_workflow_summary_markdown(result: EngineeringWorkflowResult) -> str:
    lines = [
        "# Engineering Workflow Summary",
        "",
        WORKFLOW_WARNING,
        "",
        "requires_engineer_review = true",
        f"completeness_status = {result.completeness_status}",
        f"evidence_status = {result.evidence_status}",
        f"project_use_status = {result.project_use_status}",
        f"project_use = {str(result.project_use).lower()}",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "",
        "## Input",
        "",
        f"- input_json_path: `{result.input_json_path}`",
        f"- output_dir: `{result.output_dir}`",
        "",
        "## Statuses",
        "",
        f"- workflow_status: `{result.workflow_status}`",
        f"- preflight_status: `{result.preflight_status}`",
        f"- preflight_errors_count: `{result.preflight_errors_count}`",
        f"- preflight_warnings_count: `{result.preflight_warnings_count}`",
        f"- preflight_report_json_path: `{result.preflight_report_json_path}`",
        f"- preflight_report_markdown_path: `{result.preflight_report_markdown_path}`",
        f"- deterministic_report_status: `{result.deterministic_report_status}`",
        f"- archive_validation_status: `{result.archive_validation_status}`",
        f"- zip_status: `{result.zip_status}`",
        f"- ml_readiness_status: `{result.ml_readiness_status}`",
        f"- ml_ready_for_research: `{result.ml_ready_for_research}`",
        f"- ml_ready_for_engineering_review: `{result.ml_ready_for_engineering_review}`",
        f"- ml_ready_for_project_use: `{result.ml_ready_for_project_use}`",
        f"- index_status: `{result.index_status}`",
        f"- index_path: `{result.index_path}`",
        "",
        "## Created Files",
        "",
        *_bullet_lines(result.files_created),
        "",
        "## Warnings",
        "",
        *_bullet_lines(result.warnings),
        "",
        "## Errors",
        "",
        *_bullet_lines(result.errors),
        "",
        "## Limitations",
        "",
        "- The workflow does not certify a design.",
        "- Material verification remains a separate engineer gate.",
        "- External validation remains a separate engineer gate.",
        "- ML readiness is optional and advisory-only.",
        "- Project use is not approved by this workflow.",
    ]
    return "\n".join(lines) + "\n"


def _render_workflow_readme(
    result: EngineeringWorkflowResult,
    *,
    deterministic_dir: Path,
    zip_path: Path,
    ml_output_dir: Path | None,
    index_path: Path | None,
) -> str:
    lines = [
        "# Engineering Workflow Runner",
        "",
        "This folder contains outputs from an end-to-end draft-MVP engineering workflow.",
        "It does not certify the design and does not approve project use.",
        "",
        "## Folder Contents",
        "",
        f"- deterministic report bundle: `{deterministic_dir}`",
        f"- deterministic report ZIP: `{zip_path}`",
        "- input preflight report: `input_preflight_report.json` and "
        "`input_preflight_report.md` when `--with-preflight` is used",
        "- workflow summary: `workflow_summary.json` and `workflow_summary.md`",
        "- workflow review guide: `README_WORKFLOW.md`",
    ]
    if ml_output_dir is None:
        lines.append("- ML readiness: not run")
    else:
        lines.append(f"- ML readiness bundle: `{ml_output_dir}`")
    if index_path is None:
        lines.append("- static report index: not generated")
    else:
        lines.append(f"- static report index: `{index_path}`")

    lines.extend(
        [
            "",
            "## Verify Deterministic Report Archive",
            "",
            "```bash",
            f"python -m sp63_core report-archive-validate --path {deterministic_dir} --json",
            "```",
            "",
            "## Verify ZIP Package",
            "",
            "```bash",
            "python -m sp63_core report-archive-zip "
            f"--path {deterministic_dir} --output {zip_path} --json",
            "```",
            "",
            "## Reproduce Deterministic Report",
            "",
            "```bash",
            "python -m sp63_core design-report "
            f"--input-json {deterministic_dir / 'input.json'} "
            f"--bundle-output {deterministic_dir}",
            "```",
            "",
            "## Current Workflow Status",
            "",
            f"- workflow_status: `{result.workflow_status}`",
            f"- completeness_status: `{result.completeness_status}`",
            f"- evidence_status: `{result.evidence_status}`",
            f"- project_use_status: `{result.project_use_status}`",
            f"- project_use: `{result.project_use}`",
            f"- preflight_status: `{result.preflight_status}`",
            f"- preflight_errors_count: `{result.preflight_errors_count}`",
            f"- preflight_warnings_count: `{result.preflight_warnings_count}`",
            f"- deterministic_report_status: `{result.deterministic_report_status}`",
            f"- archive_validation_status: `{result.archive_validation_status}`",
            f"- zip_status: `{result.zip_status}`",
            f"- ml_readiness_status: `{result.ml_readiness_status}`",
            f"- ml_ready_for_project_use: `{result.ml_ready_for_project_use}`",
            f"- index_status: `{result.index_status}`",
            f"- index_path: `{result.index_path}`",
            "",
            "## Required Warnings",
            "",
            "- Engineer review is mandatory.",
            "- Deterministic SP63 checks are mandatory.",
            "- ML is advisory-only and is not a design checker.",
            "- External validation is a separate workflow.",
            "- Material verification is a separate workflow.",
            "- Project use is not approved by this workflow.",
            "- Full SP 63 text is not included.",
        ]
    )
    return "\n".join(lines) + "\n"


def _append_existing(files_created: list[str], paths: tuple[Path, ...]) -> None:
    files_created.extend(str(path) for path in paths if path.exists())


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]
