"""Command line entry point for the SP 63 MVP scaffold."""

import csv
import json as jsonlib
import shutil
import webbrowser
from argparse import ArgumentParser, Namespace
from dataclasses import asdict
from pathlib import Path
from typing import Any

from sp63_core.checks import (
    check_bending_rectangular,
    check_curvature_deflection_rectangular,
    check_normal_crack_formation_rectangular,
    check_normal_crack_width_rectangular,
    check_shear_rectangular,
)
from sp63_core.dataset import (
    DATASET_COLUMNS,
    DATASET_VERSION,
    SUPPORTED_REPORT_DATASET_TARGETS,
    DatasetCase,
    analyze_synthetic_dataset_balance,
    build_dataset_report,
    build_report_dataset_feature_set,
    build_stratified_split_summary,
    diagnostic_dataset_warnings,
    diagnostic_status_counts,
    diagnostic_unique_group_count,
    export_dataset_csv,
    export_dataset_from_report_archive,
    export_dataset_report_json,
    export_dataset_split_csv,
    generate_dataset_cases,
    generate_diagnostic_dataset_cases,
    generate_guided_synthetic_inputs,
    generate_synthetic_report_inputs,
    load_report_dataset_rows,
    run_report_dataset_quality_gate,
    split_dataset_cases,
    split_diagnostic_dataset_by_group,
)
from sp63_core.design import RectangularDesignInput, design_rectangular_element
from sp63_core.materials import (
    MATERIAL_VERIFICATION_REQUIRED_COLUMNS,
    SUPPORTED_ULS_LONGITUDINAL_REBAR_CLASSES,
    build_material_audit_rows,
    build_material_verification_report,
    build_material_verification_report_document,
    get_concrete,
    get_rebar,
)
from sp63_core.ml import (
    MLProposal,
    build_baseline_ml_report,
    build_benchmark_model_comparison,
    build_benchmark_trend_report,
    build_engineering_ml_readiness_bundle,
    build_ml_proposal_package,
    build_ml_proposal_review_package,
    build_ml_readiness_report,
    build_neural_advisory_prediction,
    build_neural_advisory_safety_audit,
    build_neural_surrogate_report,
    build_report_baseline_ml_result,
    build_report_neural_surrogate_result,
    discover_benchmark_reports,
    evaluate_baseline_models,
    evaluate_ml_external_validation_readiness,
    evaluate_ml_material_verification_readiness,
    evaluate_ml_quality_gate,
    evaluate_ml_safety,
    render_ml_external_readiness_markdown,
    render_ml_material_readiness_markdown,
    render_readiness_matrix_csv,
    run_synthetic_ml_benchmark,
    save_baseline_model_bundle,
    train_baseline_models,
    verify_ml_proposal_with_deterministic_core,
)
from sp63_core.rebar import select_longitudinal_rebar, select_transverse_rebar
from sp63_core.report import (
    build_batch_design_reports,
    build_rectangular_design_report,
    build_report_manifest,
    build_review_readme_for_single_bundle,
    export_report_archive_to_zip,
    load_rectangular_design_input_from_json,
    validate_batch_report_archive,
    validate_report_bundle,
    write_report_manifest_json,
)
from sp63_core.sections import RectangularBendingOrientation, RectangularSection
from sp63_core.validation import (
    EXTERNAL_VALIDATION_COLUMNS,
    EXTERNAL_VALUES_REQUIRED_WARNING,
    build_external_comparison_rows,
    build_external_validation_summary,
    compute_external_deltas,
    evaluate_acceptance_gates,
    export_acceptance_report_json,
    export_external_comparison_csv,
    export_external_comparison_with_deltas_csv,
    load_external_comparison_csv,
    run_bending_golden_cases,
    run_crack_formation_golden_cases,
    run_crack_width_golden_cases,
    run_deflection_golden_cases,
    run_design_golden_cases,
    run_manual_verification_cases,
    run_shear_golden_cases,
    run_step3_bending_benchmark_cases,
    validate_dataset_cases,
)
from sp63_core.validation import (
    load_external_validation_csv as load_external_validation_rows_csv,
)
from sp63_core.workflows import (
    build_agent_sprint_guard,
    build_cli_status_contract,
    build_diagnostics_catalog,
    build_docs_audit_report,
    build_engineer_review_packet,
    build_engineering_gui_planning_decision,
    build_engineering_handoff_package,
    build_engineering_interface_contract,
    build_evidence_templates_package,
    build_external_validation_evidence_package,
    build_freeze_remediation_plan,
    build_input_form_schema,
    build_json_output_contract,
    build_launcher_scripts_package,
    build_material_verification_closure,
    build_next_release_roadmap,
    build_portable_package,
    build_project_template_package,
    build_release_acceptance_checklist,
    build_release_artifact_manifest,
    build_release_bundle,
    build_release_candidate_report,
    build_release_notes_package,
    build_review_signoff_templates,
    build_static_input_form_preview,
    build_static_launcher_dashboard,
    build_static_workflow_report_index,
    build_traceability_matrix,
    build_user_manual_index,
    build_v09_final_audit,
    build_v09_freeze_report,
    build_v09_readiness_gate,
    build_v09_release_candidate_package,
    build_v09_review_build,
    build_v09_review_closure,
    build_v10_gap_report,
    build_windows_smoke_plan,
    render_cli_status_contract_markdown,
    render_docs_audit_markdown,
    render_engineer_review_packet_markdown,
    render_freeze_remediation_plan_markdown,
    render_json_output_contract_markdown,
    render_material_verification_closure_markdown,
    render_next_release_roadmap_markdown,
    render_release_acceptance_checklist_markdown,
    render_self_check_markdown,
    render_traceability_matrix_markdown,
    render_v09_freeze_report_markdown,
    render_v09_package_verification_markdown,
    render_v09_release_candidate_package_markdown,
    render_v09_review_build_markdown,
    render_v09_review_closure_markdown,
    render_v10_gap_report_markdown,
    run_clean_demo_and_verify,
    run_clean_demo_workflow,
    run_engineering_workflow,
    run_engineering_workflow_batch,
    run_engineering_workflow_self_check,
    run_input_preflight,
    run_protected_files_guard,
    run_user_acceptance_smoke,
    verify_clean_demo_artifacts,
    verify_v09_release_candidate_package,
)


def build_parser() -> ArgumentParser:
    """Build the CLI argument parser."""
    parser = ArgumentParser(description="Run SP 63 MVP calculation scenarios.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bending = subparsers.add_parser("bending", help="check rectangular bending capacity")
    _add_section_arguments(bending)
    _add_orientation_arguments(bending)
    _add_material_arguments(bending, include_rebar=True)
    bending.add_argument("--as-area", type=float, required=True, help="tensile area As, mm2")
    bending.add_argument("--moment", type=float, required=True, help="bending moment, N*mm")
    bending.add_argument("--load-duration", choices=("short", "long"), required=True)
    bending.add_argument("--json", action="store_true", help="print JSON output")
    bending.set_defaults(handler=_handle_bending)

    shear = subparsers.add_parser("shear", help="check rectangular shear capacity")
    _add_section_arguments(shear)
    _add_material_arguments(shear, include_stirrup_rebar=True)
    shear.add_argument("--Q", type=float, required=True, help="shear force, N")
    shear.add_argument(
        "--Asw",
        type=float,
        required=True,
        help="transverse reinforcement area, mm2",
    )
    shear.add_argument("--sw", type=float, required=True, help="stirrup spacing, mm")
    shear.add_argument("--json", action="store_true", help="print JSON output")
    shear.set_defaults(handler=_handle_shear)

    cracking = subparsers.add_parser(
        "crack-formation",
        help="check normal crack formation for a rectangular section",
    )
    _add_section_arguments(cracking)
    _add_material_arguments(cracking)
    cracking.add_argument(
        "--moment-ser",
        type=float,
        required=True,
        help="service bending moment, N*mm",
    )
    cracking.add_argument("--json", action="store_true", help="print JSON output")
    cracking.set_defaults(handler=_handle_crack_formation)

    crack_width = subparsers.add_parser(
        "crack-width",
        help="check draft normal crack width for a rectangular section",
    )
    _add_section_arguments(crack_width)
    _add_material_arguments(crack_width, include_rebar=True)
    crack_width.add_argument(
        "--moment-ser",
        type=float,
        required=True,
        help="service bending moment, N*mm",
    )
    crack_width.add_argument("--as-area", type=float, required=True, help="tensile area As, mm2")
    crack_width.add_argument("--acrc-limit", type=float, default=0.3, help="crack width limit, mm")
    crack_width.add_argument("--json", action="store_true", help="print JSON output")
    crack_width.set_defaults(handler=_handle_crack_width)

    deflection = subparsers.add_parser(
        "deflection",
        help="check draft curvature and deflection for a rectangular section",
    )
    _add_section_arguments(deflection)
    _add_material_arguments(deflection, include_rebar=True)
    deflection.add_argument(
        "--moment-ser",
        type=float,
        required=True,
        help="service bending moment, N*mm",
    )
    deflection.add_argument("--as-area", type=float, required=True, help="tensile area As, mm2")
    deflection.add_argument("--span", type=float, required=True, help="beam span, mm")
    deflection.add_argument(
        "--deflection-limit",
        type=float,
        default=None,
        help="deflection limit, mm",
    )
    deflection.add_argument(
        "--deflection-limit-ratio",
        type=float,
        default=250.0,
        help="span divisor for default deflection limit",
    )
    deflection.add_argument(
        "--loading-scheme",
        default="simply_supported_uniform",
        help="draft loading scheme",
    )
    deflection.add_argument("--json", action="store_true", help="print JSON output")
    deflection.set_defaults(handler=_handle_deflection)

    longitudinal = subparsers.add_parser(
        "select-longitudinal", help="select longitudinal reinforcement"
    )
    _add_section_arguments(longitudinal)
    _add_orientation_arguments(longitudinal)
    _add_material_arguments(longitudinal, include_rebar=True)
    longitudinal.add_argument("--moment", type=float, required=True, help="bending moment, N*mm")
    longitudinal.add_argument("--load-duration", choices=("short", "long"), required=True)
    longitudinal.add_argument("--max-results", type=int, default=5)
    longitudinal.add_argument("--json", action="store_true", help="print JSON output")
    longitudinal.set_defaults(handler=_handle_select_longitudinal)

    transverse = subparsers.add_parser(
        "select-transverse", help="select transverse reinforcement"
    )
    _add_section_arguments(transverse)
    _add_material_arguments(transverse, include_stirrup_rebar=True)
    transverse.add_argument("--Q", type=float, required=True, help="shear force, N")
    transverse.add_argument("--max-results", type=int, default=5)
    transverse.add_argument("--json", action="store_true", help="print JSON output")
    transverse.set_defaults(handler=_handle_select_transverse)

    design = subparsers.add_parser(
        "design-rectangular", help="run end-to-end rectangular element design"
    )
    _add_design_arguments(design)
    design.add_argument("--json", action="store_true", help="print JSON output")
    design.set_defaults(handler=_handle_design_rectangular)

    design_report = subparsers.add_parser(
        "design-report",
        help="export a draft rectangular design calculation report",
    )
    design_report.add_argument("--json", action="store_true", help="print JSON report output")
    design_report.add_argument("--markdown", action="store_true", help="print Markdown report")
    design_report.add_argument("--html", action="store_true", help="print static HTML report")
    design_report.add_argument("--input-json", help="rectangular design report input JSON")
    design_report.add_argument("--output", help="optional report output path")
    design_report.add_argument(
        "--bundle-output",
        help="optional directory for report.md, report.json, and report.html",
    )
    design_report.add_argument(
        "--no-manifest",
        action="store_true",
        help="do not write manifest.json for bundle output",
    )
    design_report.set_defaults(handler=_handle_design_report)

    design_report_batch = subparsers.add_parser(
        "design-report-batch",
        help="export draft rectangular design calculation reports for multiple JSON inputs",
    )
    design_report_batch.add_argument(
        "--input-dir",
        help="directory containing rectangular design report JSON inputs",
    )
    design_report_batch.add_argument(
        "--input-json",
        action="append",
        default=[],
        help="rectangular design report input JSON; may be repeated",
    )
    design_report_batch.add_argument(
        "--output-dir",
        required=True,
        help="directory for batch case report bundles and index files",
    )
    design_report_batch.add_argument("--json", action="store_true", help="print JSON summary")
    design_report_batch.set_defaults(handler=_handle_design_report_batch)

    synthetic_report_inputs = subparsers.add_parser(
        "synthetic-report-inputs",
        help="generate reproducible synthetic design-report input JSON cases",
    )
    synthetic_report_inputs.add_argument(
        "--output-dir",
        required=True,
        help="output directory for synthetic input JSON cases",
    )
    synthetic_report_inputs.add_argument("--case-count", type=int, default=300)
    synthetic_report_inputs.add_argument("--seed", type=int, default=42)
    synthetic_report_inputs.add_argument(
        "--no-serviceability",
        action="store_true",
        help="omit serviceability fields and checks from generated cases",
    )
    synthetic_report_inputs.add_argument("--json", action="store_true", help="print JSON output")
    synthetic_report_inputs.set_defaults(handler=_handle_synthetic_report_inputs)

    guided_synthetic_inputs = subparsers.add_parser(
        "guided-synthetic-inputs",
        help="generate deterministic-guided synthetic input JSON cases by target status",
    )
    guided_synthetic_inputs.add_argument(
        "--output-dir",
        required=True,
        help="output directory for guided synthetic input JSON cases",
    )
    guided_synthetic_inputs.add_argument("--target-pass", type=int, default=50)
    guided_synthetic_inputs.add_argument("--target-fail", type=int, default=50)
    guided_synthetic_inputs.add_argument("--target-review", type=int, default=50)
    guided_synthetic_inputs.add_argument("--seed", type=int, default=42)
    guided_synthetic_inputs.add_argument("--max-attempts", type=int, default=1000)
    guided_synthetic_inputs.add_argument(
        "--no-serviceability",
        action="store_true",
        help="omit serviceability fields and checks from generated candidates",
    )
    guided_synthetic_inputs.add_argument("--json", action="store_true", help="print JSON output")
    guided_synthetic_inputs.set_defaults(handler=_handle_guided_synthetic_inputs)

    report_archive_validate = subparsers.add_parser(
        "report-archive-validate",
        help="validate integrity of generated report bundle archives",
    )
    report_archive_validate.add_argument(
        "--path",
        required=True,
        help="single report bundle or batch report archive directory",
    )
    report_archive_validate.add_argument(
        "--batch",
        action="store_true",
        help="treat the path as a batch report archive",
    )
    report_archive_validate.add_argument("--json", action="store_true", help="print JSON output")
    report_archive_validate.set_defaults(handler=_handle_report_archive_validate)

    report_archive_zip = subparsers.add_parser(
        "report-archive-zip",
        help="export a generated report archive directory to a validated ZIP file",
    )
    report_archive_zip.add_argument(
        "--path",
        required=True,
        help="single report bundle or batch report archive directory",
    )
    report_archive_zip.add_argument("--output", required=True, help="output ZIP path")
    report_archive_zip.add_argument(
        "--batch",
        action="store_true",
        help="source path is a batch archive; auto-detected when index.json exists",
    )
    report_archive_zip.add_argument("--json", action="store_true", help="print JSON output")
    report_archive_zip.set_defaults(handler=_handle_report_archive_zip)

    engineering_workflow = subparsers.add_parser(
        "engineering-workflow",
        help="run deterministic report, archive, ZIP, and optional ML readiness workflow",
    )
    engineering_workflow.add_argument(
        "--input-json",
        required=True,
        help="rectangular design report input JSON",
    )
    engineering_workflow.add_argument(
        "--output-dir",
        required=True,
        help="output directory for workflow files",
    )
    engineering_workflow.add_argument(
        "--include-ml-readiness",
        action="store_true",
        help="include advisory engineering ML readiness bundle",
    )
    engineering_workflow.add_argument("--dataset", help="report-derived ML dataset path")
    engineering_workflow.add_argument(
        "--format",
        choices=("jsonl", "json", "csv"),
        help="dataset format for ML readiness; inferred when omitted",
    )
    engineering_workflow.add_argument(
        "--external-validation-csv",
        help="engineer-filled external validation CSV for ML readiness",
    )
    engineering_workflow.add_argument(
        "--material-verification-csv",
        help="engineer-filled material verification CSV for ML readiness",
    )
    engineering_workflow.add_argument(
        "--no-zip",
        action="store_true",
        help="skip deterministic report ZIP creation",
    )
    engineering_workflow.add_argument(
        "--with-index",
        action="store_true",
        help="create a static HTML index for generated workflow files",
    )
    engineering_workflow.add_argument(
        "--with-preflight",
        action="store_true",
        help="run input JSON preflight before deterministic workflow",
    )
    engineering_workflow.add_argument("--json", action="store_true", help="print JSON output")
    engineering_workflow.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown workflow summary",
    )
    engineering_workflow.set_defaults(handler=_handle_engineering_workflow)

    engineering_workflow_batch = subparsers.add_parser(
        "engineering-workflow-batch",
        help="run engineering workflow for every JSON file in an input directory",
    )
    engineering_workflow_batch.add_argument(
        "--input-dir",
        required=True,
        help="directory containing input JSON files",
    )
    engineering_workflow_batch.add_argument(
        "--output-dir",
        required=True,
        help="output directory for batch workflow files",
    )
    engineering_workflow_batch.add_argument(
        "--with-preflight",
        action="store_true",
        help="run preflight for each case before deterministic workflow",
    )
    engineering_workflow_batch.add_argument(
        "--with-index",
        action="store_true",
        help="create static HTML indexes for each case",
    )
    engineering_workflow_batch.add_argument(
        "--no-zip",
        action="store_true",
        help="skip deterministic report ZIP creation for each case",
    )
    engineering_workflow_batch.add_argument("--json", action="store_true", help="print JSON output")
    engineering_workflow_batch.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown batch workflow summary",
    )
    engineering_workflow_batch.set_defaults(handler=_handle_engineering_workflow_batch)

    engineering_report_index = subparsers.add_parser(
        "engineering-report-index",
        help="create a static HTML index for an engineering workflow output folder",
    )
    engineering_report_index.add_argument(
        "--workflow-dir",
        required=True,
        help="existing engineering workflow output directory",
    )
    engineering_report_index.add_argument(
        "--output",
        help="output HTML file path; defaults to <workflow-dir>/index.html",
    )
    engineering_report_index.add_argument(
        "--title",
        default="Engineering Workflow Report Index",
        help="title for the generated static HTML index",
    )
    engineering_report_index.add_argument(
        "--open-in-browser",
        action="store_true",
        help="open generated index with Python webbrowser; no web server is started",
    )
    engineering_report_index.add_argument("--json", action="store_true", help="print JSON output")
    engineering_report_index.set_defaults(handler=_handle_engineering_report_index)

    engineering_workflow_self_check = subparsers.add_parser(
        "engineering-workflow-self-check",
        help="run a smoke self-check for the engineering workflow runner",
    )
    engineering_workflow_self_check.add_argument(
        "--output-dir",
        required=True,
        help="output directory for self-check artifacts",
    )
    engineering_workflow_self_check.add_argument(
        "--include-ml-readiness",
        action="store_true",
        help="include advisory ML readiness in the self-check",
    )
    engineering_workflow_self_check.add_argument(
        "--dataset",
        help="report-derived ML dataset path for optional ML readiness",
    )
    engineering_workflow_self_check.add_argument(
        "--external-validation-csv",
        help="engineer-filled external validation CSV for optional ML readiness",
    )
    engineering_workflow_self_check.add_argument(
        "--material-verification-csv",
        help="engineer-filled material verification CSV for optional ML readiness",
    )
    engineering_workflow_self_check.add_argument(
        "--cleanup",
        action="store_true",
        help="remove temporary workflow output folders after the self-check",
    )
    engineering_workflow_self_check.add_argument(
        "--json",
        action="store_true",
        help="print JSON output",
    )
    engineering_workflow_self_check.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown self-check report",
    )
    engineering_workflow_self_check.set_defaults(handler=_handle_engineering_workflow_self_check)

    clean_demo_workflow = subparsers.add_parser(
        "clean-demo-workflow",
        help="run a clean deterministic demo workflow and write review artifacts",
    )
    clean_demo_workflow.add_argument(
        "--output-dir",
        required=True,
        help="output directory for clean demo workflow artifacts",
    )
    clean_demo_workflow.add_argument("--json", action="store_true", help="print JSON output")
    clean_demo_workflow.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown clean demo workflow summary",
    )
    clean_demo_workflow.set_defaults(handler=_handle_clean_demo_workflow)

    clean_demo_verify = subparsers.add_parser(
        "clean-demo-verify",
        help="verify clean demo generated user-facing artifacts",
    )
    clean_demo_verify.add_argument(
        "--workflow-dir",
        help="existing clean demo workflow directory to verify",
    )
    clean_demo_verify.add_argument(
        "--run",
        action="store_true",
        help="run clean demo workflow before verification",
    )
    clean_demo_verify.add_argument(
        "--output-dir",
        help="output directory for --run mode",
    )
    clean_demo_verify.add_argument("--json", action="store_true", help="print JSON output")
    clean_demo_verify.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown verification report",
    )
    clean_demo_verify.set_defaults(handler=_handle_clean_demo_verify)

    engineering_handoff_package = subparsers.add_parser(
        "engineering-handoff-package",
        help="create a portable engineering handoff package for review",
    )
    engineering_handoff_package.add_argument(
        "--output-dir",
        required=True,
        help="output directory for handoff package files",
    )
    engineering_handoff_package.add_argument(
        "--json",
        action="store_true",
        help="print JSON output",
    )
    engineering_handoff_package.set_defaults(handler=_handle_engineering_handoff_package)

    launcher_scripts = subparsers.add_parser(
        "launcher-scripts",
        help="create lightweight CLI launcher scripts for engineering review",
    )
    launcher_scripts.add_argument(
        "--output-dir",
        required=True,
        help="output directory for launcher scripts",
    )
    launcher_scripts.add_argument(
        "--json",
        action="store_true",
        help="print JSON output",
    )
    launcher_scripts.set_defaults(handler=_handle_launcher_scripts)

    external_validation_evidence = subparsers.add_parser(
        "external-validation-evidence-package",
        help="create an external validation evidence package and optional CSV summary",
    )
    external_validation_evidence.add_argument(
        "--output-dir",
        required=True,
        help="output directory for external validation evidence package",
    )
    external_validation_evidence.add_argument(
        "--external-validation-csv",
        help="engineer-filled external validation CSV to summarize",
    )
    external_validation_evidence.add_argument(
        "--strict",
        action="store_true",
        help="run strict summary checks when a CSV is provided",
    )
    external_validation_evidence.add_argument(
        "--json",
        action="store_true",
        help="print JSON output",
    )
    external_validation_evidence.set_defaults(
        handler=_handle_external_validation_evidence_package
    )

    engineering_interface_contract = subparsers.add_parser(
        "engineering-interface-contract",
        help="write or print the future GUI/desktop wrapper interface contract",
    )
    engineering_interface_contract.add_argument(
        "--output-dir",
        help="output directory for interface contract files",
    )
    engineering_interface_contract.add_argument(
        "--no-output-files",
        action="store_true",
        help="do not write contract files even when --output-dir is provided",
    )
    engineering_interface_contract.add_argument(
        "--json",
        action="store_true",
        help="print JSON summary",
    )
    engineering_interface_contract.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown contract",
    )
    engineering_interface_contract.set_defaults(handler=_handle_engineering_interface_contract)

    engineering_gui_planning = subparsers.add_parser(
        "engineering-gui-planning",
        help="write or print the planning-only GUI technology decision",
    )
    engineering_gui_planning.add_argument(
        "--output-dir",
        help="output directory for GUI planning decision files",
    )
    engineering_gui_planning.add_argument(
        "--no-output-files",
        action="store_true",
        help="do not write planning files even when --output-dir is provided",
    )
    engineering_gui_planning.add_argument(
        "--json",
        action="store_true",
        help="print JSON summary",
    )
    engineering_gui_planning.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown planning decision",
    )
    engineering_gui_planning.set_defaults(handler=_handle_engineering_gui_planning)

    input_form_schema = subparsers.add_parser(
        "input-form-schema",
        help="write or print future UI input JSON form schema and validation hints",
    )
    input_form_schema.add_argument(
        "--output-dir",
        help="output directory for input_form_schema.json and input_form_schema.md",
    )
    input_form_schema.add_argument(
        "--no-output-files",
        action="store_true",
        help="do not write schema files even when --output-dir is provided",
    )
    input_form_schema.add_argument(
        "--json",
        action="store_true",
        help="print JSON summary",
    )
    input_form_schema.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown schema",
    )
    input_form_schema.set_defaults(handler=_handle_input_form_schema)

    input_preflight = subparsers.add_parser(
        "input-preflight",
        help="validate an engineering input JSON before running workflow commands",
    )
    input_preflight.add_argument(
        "--input-json",
        required=True,
        help="engineering input JSON file to validate",
    )
    input_preflight.add_argument(
        "--output-dir",
        help="output directory for input_preflight_report.json and input_preflight_report.md",
    )
    input_preflight.add_argument(
        "--no-output-files",
        action="store_true",
        help="do not write preflight files even when --output-dir is provided",
    )
    input_preflight.add_argument(
        "--json",
        action="store_true",
        help="print JSON summary",
    )
    input_preflight.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown preflight report",
    )
    input_preflight.set_defaults(handler=_handle_input_preflight)

    input_form_preview = subparsers.add_parser(
        "input-form-preview",
        help="write or print a static HTML preview of the engineering input form schema",
    )
    input_form_preview.add_argument(
        "--output-dir",
        help="output directory for input_form_preview artifacts",
    )
    input_form_preview.add_argument(
        "--no-output-files",
        action="store_true",
        help="do not write preview files even when --output-dir is provided",
    )
    input_form_preview.add_argument(
        "--json",
        action="store_true",
        help="print JSON summary",
    )
    input_form_preview.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown review note",
    )
    input_form_preview.set_defaults(handler=_handle_input_form_preview)

    diagnostics_catalog = subparsers.add_parser(
        "diagnostics-catalog",
        help="write or print human-friendly workflow diagnostics catalog",
    )
    diagnostics_catalog.add_argument(
        "--output-dir",
        help="output directory for diagnostics_catalog.json and diagnostics_catalog.md",
    )
    diagnostics_catalog.add_argument(
        "--no-output-files",
        action="store_true",
        help="do not write catalog files even when --output-dir is provided",
    )
    diagnostics_catalog.add_argument("--json", action="store_true", help="print JSON summary")
    diagnostics_catalog.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown diagnostics catalog",
    )
    diagnostics_catalog.set_defaults(handler=_handle_diagnostics_catalog)

    docs_audit = subparsers.add_parser(
        "docs-audit",
        help="audit local documentation links and required CLI examples",
    )
    docs_audit.add_argument(
        "--output-dir",
        help="optional output directory for docs_audit_report.json/md",
    )
    docs_audit.add_argument("--json", action="store_true", help="print JSON output")
    docs_audit.add_argument("--markdown", action="store_true", help="print Markdown output")
    docs_audit.set_defaults(handler=_handle_docs_audit)

    evidence_templates = subparsers.add_parser(
        "evidence-templates",
        help="create external validation and material verification template package",
    )
    evidence_templates.add_argument(
        "--output-dir",
        required=True,
        help="output directory for evidence template package",
    )
    evidence_templates.add_argument("--json", action="store_true", help="print JSON output")
    evidence_templates.set_defaults(handler=_handle_evidence_templates)

    project_template = subparsers.add_parser(
        "project-template",
        help="create a project handoff template with input and evidence files",
    )
    project_template.add_argument(
        "--output-dir",
        required=True,
        help="output directory for project template package",
    )
    project_template.add_argument("--json", action="store_true", help="print JSON output")
    project_template.set_defaults(handler=_handle_project_template)

    protected_files_check = subparsers.add_parser(
        "protected-files-check",
        help="check whether protected calculation/material files changed",
    )
    protected_files_check.add_argument(
        "--base-ref",
        default="main",
        help="base git ref for protected-files diff",
    )
    protected_files_check.add_argument(
        "--head-ref",
        default="HEAD",
        help="head git ref for protected-files diff",
    )
    protected_files_check.add_argument(
        "--allow-review-required",
        action="store_true",
        help="record review_required as explicitly allowed by caller",
    )
    protected_files_check.add_argument("--json", action="store_true", help="print JSON output")
    protected_files_check.set_defaults(handler=_handle_protected_files_check)

    user_manual_index = subparsers.add_parser(
        "user-manual-index",
        help="check and print the user manual package index",
    )
    user_manual_index.add_argument(
        "--manual-dir",
        default="docs/user_manual",
        help="manual directory to check",
    )
    user_manual_index.add_argument(
        "--output-dir",
        help="output directory for user_manual_index.json and user_manual_index.md",
    )
    user_manual_index.add_argument("--json", action="store_true", help="print JSON output")
    user_manual_index.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown manual index",
    )
    user_manual_index.set_defaults(handler=_handle_user_manual_index)

    release_candidate_report = subparsers.add_parser(
        "release-candidate-report",
        help="build a draft release candidate review report",
    )
    release_candidate_report.add_argument(
        "--output-dir",
        required=True,
        help="output directory for release candidate report files",
    )
    release_candidate_report.add_argument(
        "--version",
        default="0.9.0-rc1",
        help="release candidate version label",
    )
    release_candidate_report.add_argument("--json", action="store_true", help="print JSON output")
    release_candidate_report.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown release candidate report",
    )
    release_candidate_report.set_defaults(handler=_handle_release_candidate_report)

    release_manifest = subparsers.add_parser(
        "release-manifest",
        help="build release artifact manifest and version metadata",
    )
    release_manifest.add_argument(
        "--output-dir",
        required=True,
        help="output directory for release artifact manifest files",
    )
    release_manifest.add_argument(
        "--version",
        default="0.9.0-rc1",
        help="release version label",
    )
    release_manifest.add_argument("--json", action="store_true", help="print JSON output")
    release_manifest.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown release artifact manifest",
    )
    release_manifest.set_defaults(handler=_handle_release_manifest)

    release_bundle = subparsers.add_parser(
        "release-bundle",
        help="build review-only v0.9 release bundle ZIP",
    )
    release_bundle.add_argument(
        "--output-dir",
        required=True,
        help="output directory for release bundle artifacts",
    )
    release_bundle.add_argument(
        "--version",
        default="0.9.0-rc1",
        help="release bundle version label",
    )
    release_bundle.add_argument("--json", action="store_true", help="print JSON output")
    release_bundle.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown release bundle report",
    )
    release_bundle.set_defaults(handler=_handle_release_bundle)

    traceability_matrix = subparsers.add_parser(
        "traceability-matrix",
        help="write or print feature/CLI/docs/tests traceability matrix",
    )
    traceability_matrix.add_argument(
        "--output-dir",
        help="output directory for traceability_matrix.json/md",
    )
    traceability_matrix.add_argument("--json", action="store_true", help="print JSON output")
    traceability_matrix.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown traceability matrix",
    )
    traceability_matrix.set_defaults(handler=_handle_traceability_matrix)

    release_notes = subparsers.add_parser(
        "release-notes",
        help="build v0.9 engineering release notes package",
    )
    release_notes.add_argument(
        "--output-dir",
        required=True,
        help="output directory for release notes package",
    )
    release_notes.add_argument(
        "--version",
        default="0.9.0-rc1",
        help="release notes version label",
    )
    release_notes.add_argument("--json", action="store_true", help="print JSON output")
    release_notes.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown release notes",
    )
    release_notes.set_defaults(handler=_handle_release_notes)

    user_acceptance_smoke = subparsers.add_parser(
        "user-acceptance-smoke",
        help="run v0.9 user acceptance smoke suite",
    )
    user_acceptance_smoke.add_argument(
        "--output-dir",
        required=True,
        help="output directory for user acceptance smoke artifacts",
    )
    user_acceptance_smoke.add_argument(
        "--version",
        default="0.9.0-rc1",
        help="version label used by nested release manifest smoke",
    )
    user_acceptance_smoke.add_argument("--json", action="store_true", help="print JSON output")
    user_acceptance_smoke.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown user acceptance smoke summary",
    )
    user_acceptance_smoke.set_defaults(handler=_handle_user_acceptance_smoke)

    v09_readiness = subparsers.add_parser(
        "v09-readiness",
        help="build v0.9 readiness gate report",
    )
    v09_readiness.add_argument(
        "--output-dir",
        required=True,
        help="output directory for v0.9 readiness artifacts",
    )
    v09_readiness.add_argument(
        "--version",
        default="0.9.0-rc1",
        help="version label used by nested release artifacts",
    )
    v09_readiness.add_argument("--json", action="store_true", help="print JSON output")
    v09_readiness.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown v0.9 readiness report",
    )
    v09_readiness.set_defaults(handler=_handle_v09_readiness)

    v09_final_audit = subparsers.add_parser(
        "v09-final-audit",
        help="build final v0.9 release-preparation audit report",
    )
    v09_final_audit.add_argument(
        "--output-dir",
        required=True,
        help="output directory for final v0.9 audit artifacts",
    )
    v09_final_audit.add_argument(
        "--version",
        default="0.9.0-rc1",
        help="version label used by nested audit artifacts",
    )
    v09_final_audit.add_argument("--json", action="store_true", help="print JSON output")
    v09_final_audit.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown final v0.9 audit report",
    )
    v09_final_audit.set_defaults(handler=_handle_v09_final_audit)

    v10_gap_report = subparsers.add_parser(
        "v10-gap-report",
        help="build v1.0 gap and risk report",
    )
    v10_gap_report.add_argument(
        "--output-dir",
        required=True,
        help="output directory for v1.0 gap report artifacts",
    )
    v10_gap_report.add_argument("--json", action="store_true", help="print JSON output")
    v10_gap_report.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown v1.0 gap report",
    )
    v10_gap_report.set_defaults(handler=_handle_v10_gap_report)

    v09_freeze_report = subparsers.add_parser(
        "v09-freeze-report",
        help="build final v0.9 freeze report",
    )
    v09_freeze_report.add_argument(
        "--output-dir",
        required=True,
        help="output directory for v0.9 freeze report artifacts",
    )
    v09_freeze_report.add_argument(
        "--version",
        default="0.9.0-rc1",
        help="v0.9 freeze version label",
    )
    v09_freeze_report.add_argument("--json", action="store_true", help="print JSON output")
    v09_freeze_report.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown v0.9 freeze report",
    )
    v09_freeze_report.set_defaults(handler=_handle_v09_freeze_report)

    freeze_remediation_plan = subparsers.add_parser(
        "freeze-remediation-plan",
        help="build a v0.9 freeze remediation plan",
    )
    freeze_remediation_plan.add_argument(
        "--output-dir",
        required=True,
        help="output directory for freeze remediation artifacts",
    )
    freeze_remediation_plan.add_argument(
        "--version",
        default="0.9.0-rc1",
        help="version label used by current freeze report",
    )
    freeze_remediation_plan.add_argument(
        "--json",
        action="store_true",
        help="print JSON output",
    )
    freeze_remediation_plan.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown remediation plan",
    )
    freeze_remediation_plan.set_defaults(handler=_handle_freeze_remediation_plan)

    windows_smoke_plan = subparsers.add_parser(
        "windows-smoke-plan",
        help="build a manual Windows clean-machine smoke plan",
    )
    windows_smoke_plan.add_argument(
        "--output-dir",
        required=True,
        help="output directory for Windows smoke plan artifacts",
    )
    windows_smoke_plan.add_argument("--json", action="store_true", help="print JSON output")
    windows_smoke_plan.set_defaults(handler=_handle_windows_smoke_plan)

    engineer_review_packet = subparsers.add_parser(
        "engineer-review-packet",
        help="build an engineer review packet",
    )
    engineer_review_packet.add_argument(
        "--output-dir",
        required=True,
        help="output directory for engineer review packet artifacts",
    )
    engineer_review_packet.add_argument(
        "--json",
        action="store_true",
        help="print JSON output",
    )
    engineer_review_packet.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown packet report",
    )
    engineer_review_packet.set_defaults(handler=_handle_engineer_review_packet)

    static_launcher_dashboard = subparsers.add_parser(
        "static-launcher-dashboard",
        help="build a static local launcher dashboard",
    )
    static_launcher_dashboard.add_argument(
        "--output-dir",
        required=True,
        help="output directory for static launcher dashboard artifacts",
    )
    static_launcher_dashboard.add_argument(
        "--json",
        action="store_true",
        help="print JSON output",
    )
    static_launcher_dashboard.set_defaults(handler=_handle_static_launcher_dashboard)

    release_acceptance_checklist = subparsers.add_parser(
        "release-acceptance-checklist",
        help="build a v0.9 release acceptance checklist",
    )
    release_acceptance_checklist.add_argument(
        "--output-dir",
        required=True,
        help="output directory for release acceptance checklist artifacts",
    )
    release_acceptance_checklist.add_argument(
        "--json",
        action="store_true",
        help="print JSON output",
    )
    release_acceptance_checklist.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown checklist",
    )
    release_acceptance_checklist.set_defaults(handler=_handle_release_acceptance_checklist)

    review_signoff_templates = subparsers.add_parser(
        "review-signoff-templates",
        help="build placeholder-only review signoff templates",
    )
    review_signoff_templates.add_argument(
        "--output-dir",
        required=True,
        help="output directory for review signoff templates",
    )
    review_signoff_templates.add_argument(
        "--json",
        action="store_true",
        help="print JSON output",
    )
    review_signoff_templates.set_defaults(handler=_handle_review_signoff_templates)

    v09_review_build = subparsers.add_parser(
        "v09-review-build",
        help="build the v0.9 review build artifact packet",
    )
    v09_review_build.add_argument(
        "--output-dir",
        required=True,
        help="output directory for v0.9 review build artifacts",
    )
    v09_review_build.add_argument(
        "--version",
        default="0.9.0-rc1",
        help="v0.9 review build version label",
    )
    v09_review_build.add_argument("--json", action="store_true", help="print JSON output")
    v09_review_build.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown review build report",
    )
    v09_review_build.set_defaults(handler=_handle_v09_review_build)

    v09_review_closure = subparsers.add_parser(
        "v09-review-closure",
        help="build the v0.9 manual review closure report",
    )
    v09_review_closure.add_argument(
        "--output-dir",
        required=True,
        help="output directory for v0.9 review closure artifacts",
    )
    v09_review_closure.add_argument(
        "--version",
        default="0.9.0-rc1",
        help="v0.9 review closure version label",
    )
    v09_review_closure.add_argument("--json", action="store_true", help="print JSON output")
    v09_review_closure.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown review closure report",
    )
    v09_review_closure.set_defaults(handler=_handle_v09_review_closure)

    v09_release_candidate_package = subparsers.add_parser(
        "v09-release-candidate-package",
        help="build the final v0.9 release candidate package",
    )
    v09_release_candidate_package.add_argument(
        "--output-dir",
        required=True,
        help="output directory for v0.9 release candidate package artifacts",
    )
    v09_release_candidate_package.add_argument(
        "--version",
        default="0.9.0-rc1",
        help="v0.9 release candidate package version label",
    )
    v09_release_candidate_package.add_argument(
        "--json",
        action="store_true",
        help="print JSON output",
    )
    v09_release_candidate_package.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown release candidate package report",
    )
    v09_release_candidate_package.set_defaults(handler=_handle_v09_release_candidate_package)

    v09_package_verify = subparsers.add_parser(
        "v09-package-verify",
        help="verify a v0.9 release candidate package",
    )
    v09_package_verify.add_argument(
        "--package-dir",
        help="existing package directory, or build target when --build is used",
    )
    v09_package_verify.add_argument(
        "--output-dir",
        required=True,
        help="output directory for v0.9 package verification artifacts",
    )
    v09_package_verify.add_argument(
        "--build",
        action="store_true",
        help="build the release candidate package before verification",
    )
    v09_package_verify.add_argument(
        "--version",
        default="0.9.0-rc1",
        help="v0.9 release candidate package version label",
    )
    v09_package_verify.add_argument(
        "--json",
        action="store_true",
        help="print JSON output",
    )
    v09_package_verify.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown package verification report",
    )
    v09_package_verify.set_defaults(handler=_handle_v09_package_verify)

    next_release_roadmap = subparsers.add_parser(
        "next-release-roadmap",
        help="build the post-v0.9 next release roadmap",
    )
    next_release_roadmap.add_argument(
        "--output-dir",
        required=True,
        help="output directory for next release roadmap artifacts",
    )
    next_release_roadmap.add_argument("--json", action="store_true", help="print JSON output")
    next_release_roadmap.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown roadmap",
    )
    next_release_roadmap.set_defaults(handler=_handle_next_release_roadmap)

    agent_sprint_guard = subparsers.add_parser(
        "agent-sprint-guard",
        help="check local K-step artifact completeness for an agent sprint",
    )
    agent_sprint_guard.add_argument("--from-k", type=int, required=True)
    agent_sprint_guard.add_argument("--to-k", type=int, required=True)
    agent_sprint_guard.add_argument("--json", action="store_true", help="print JSON output")
    agent_sprint_guard.set_defaults(handler=_handle_agent_sprint_guard)

    cli_status_contract = subparsers.add_parser(
        "cli-status-contract",
        help="write or print the CLI status and exit-code contract",
    )
    cli_status_contract.add_argument(
        "--output-dir",
        help="output directory for cli_status_contract.json/md",
    )
    cli_status_contract.add_argument("--json", action="store_true", help="print JSON output")
    cli_status_contract.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown contract",
    )
    cli_status_contract.set_defaults(handler=_handle_cli_status_contract)

    json_output_contract = subparsers.add_parser(
        "json-output-contract",
        help="write or print lightweight JSON output schema contracts",
    )
    json_output_contract.add_argument(
        "--output-dir",
        help="output directory for json_output_contract.json/md",
    )
    json_output_contract.add_argument("--json", action="store_true", help="print JSON output")
    json_output_contract.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown contract",
    )
    json_output_contract.set_defaults(handler=_handle_json_output_contract)

    portable_package = subparsers.add_parser(
        "portable-package",
        help="create a portable Windows package skeleton without binaries",
    )
    portable_package.add_argument(
        "--output-dir",
        required=True,
        help="output directory for portable package skeleton",
    )
    portable_package.add_argument("--json", action="store_true", help="print JSON output")
    portable_package.set_defaults(handler=_handle_portable_package)

    report_dataset_export = subparsers.add_parser(
        "report-dataset-export",
        help="export ML-ready dataset rows from validated report archives",
    )
    report_dataset_export.add_argument(
        "--path",
        required=True,
        help="single report bundle or batch report archive directory",
    )
    report_dataset_export.add_argument("--output", help="dataset output path")
    report_dataset_export.add_argument(
        "--format",
        choices=("jsonl", "json", "csv"),
        default="jsonl",
        help="dataset output format",
    )
    report_dataset_export.add_argument(
        "--batch",
        action="store_true",
        help="source path is a batch archive; auto-detected when index.json exists",
    )
    report_dataset_export.add_argument(
        "--no-archive-validation",
        action="store_true",
        help="skip archive validation before dataset extraction",
    )
    report_dataset_export.add_argument("--json", action="store_true", help="print JSON output")
    report_dataset_export.set_defaults(handler=_handle_report_dataset_export)

    report_dataset_quality = subparsers.add_parser(
        "report-dataset-quality",
        help="run quality gate for report-derived ML dataset rows",
    )
    report_dataset_quality.add_argument("--dataset", required=True, help="dataset file path")
    report_dataset_quality.add_argument(
        "--format",
        choices=("jsonl", "json", "csv"),
        help="dataset format; inferred from extension when omitted",
    )
    report_dataset_quality.add_argument(
        "--task",
        choices=("classification", "regression"),
        default="classification",
        help="future ML task type for leakage/status-diversity checks",
    )
    report_dataset_quality.add_argument("--min-rows", type=int, default=100)
    report_dataset_quality.add_argument(
        "--no-require-status-diversity",
        action="store_true",
        help="do not require pass/fail/review_or_fail diversity",
    )
    report_dataset_quality.add_argument("--json", action="store_true", help="print JSON output")
    report_dataset_quality.set_defaults(handler=_handle_report_dataset_quality)

    report_dataset_features = subparsers.add_parser(
        "report-dataset-features",
        help="prepare leakage-safe feature metadata for report-derived datasets",
    )
    report_dataset_features.add_argument("--dataset", required=True, help="dataset file path")
    report_dataset_features.add_argument(
        "--format",
        choices=("jsonl", "json", "csv"),
        help="dataset format; inferred from extension when omitted",
    )
    report_dataset_features.add_argument("--target", default="overall_status")
    report_dataset_features.add_argument(
        "--feature-mode",
        choices=("input_only", "deterministic_derived"),
        default="input_only",
    )
    report_dataset_features.add_argument("--train-ratio", type=float, default=0.7)
    report_dataset_features.add_argument("--validation-ratio", type=float, default=0.15)
    report_dataset_features.add_argument("--test-ratio", type=float, default=0.15)
    report_dataset_features.add_argument("--random-state", type=int, default=42)
    report_dataset_features.add_argument(
        "--no-split",
        action="store_true",
        help="do not compute train/validation/test split counts",
    )
    report_dataset_features.add_argument("--json", action="store_true", help="print JSON output")
    report_dataset_features.set_defaults(handler=_handle_report_dataset_features)

    synthetic_dataset_balance = subparsers.add_parser(
        "synthetic-dataset-balance",
        help="analyze balance and stratified readiness for synthetic report-derived datasets",
    )
    synthetic_dataset_balance.add_argument("--dataset", required=True, help="dataset file path")
    synthetic_dataset_balance.add_argument(
        "--format",
        choices=("jsonl", "json", "csv"),
        help="dataset format; inferred from extension when omitted",
    )
    synthetic_dataset_balance.add_argument(
        "--target",
        choices=SUPPORTED_REPORT_DATASET_TARGETS,
        default="overall_status",
    )
    synthetic_dataset_balance.add_argument("--min-rows", type=int, default=100)
    synthetic_dataset_balance.add_argument("--min-class-count", type=int, default=20)
    synthetic_dataset_balance.add_argument("--max-imbalance-ratio", type=float, default=3.0)
    synthetic_dataset_balance.add_argument("--train-ratio", type=float, default=0.7)
    synthetic_dataset_balance.add_argument("--validation-ratio", type=float, default=0.15)
    synthetic_dataset_balance.add_argument("--test-ratio", type=float, default=0.15)
    synthetic_dataset_balance.add_argument("--random-state", type=int, default=42)
    synthetic_dataset_balance.add_argument(
        "--split-index-output",
        help="optional output path for stratified split row ids",
    )
    synthetic_dataset_balance.add_argument("--json", action="store_true", help="print JSON output")
    synthetic_dataset_balance.set_defaults(handler=_handle_synthetic_dataset_balance)

    synthetic_ml_benchmark = subparsers.add_parser(
        "synthetic-ml-benchmark",
        help="run guided synthetic report dataset through ML benchmark stages",
    )
    synthetic_ml_benchmark.add_argument(
        "--output-dir",
        required=True,
        help="output directory for benchmark artifacts",
    )
    synthetic_ml_benchmark.add_argument("--target-pass", type=int, default=100)
    synthetic_ml_benchmark.add_argument("--target-fail", type=int, default=100)
    synthetic_ml_benchmark.add_argument("--target-review", type=int, default=100)
    synthetic_ml_benchmark.add_argument("--seed", type=int, default=42)
    synthetic_ml_benchmark.add_argument("--max-attempts", type=int, default=10000)
    synthetic_ml_benchmark.add_argument(
        "--target",
        choices=SUPPORTED_REPORT_DATASET_TARGETS,
        default="overall_status",
    )
    synthetic_ml_benchmark.add_argument(
        "--feature-mode",
        choices=("input_only", "deterministic_derived"),
        default="input_only",
    )
    synthetic_ml_benchmark.add_argument(
        "--no-serviceability",
        action="store_true",
        help="omit serviceability fields and checks from guided candidates",
    )
    synthetic_ml_benchmark.add_argument(
        "--no-reports",
        action="store_true",
        help="only generate guided inputs and benchmark metadata",
    )
    synthetic_ml_benchmark.add_argument(
        "--markdown",
        action="store_true",
        help="print the generated Markdown benchmark report",
    )
    synthetic_ml_benchmark.add_argument("--json", action="store_true", help="print JSON output")
    synthetic_ml_benchmark.set_defaults(handler=_handle_synthetic_ml_benchmark)

    benchmark_model_comparison = subparsers.add_parser(
        "benchmark-model-comparison",
        help="compare baseline and neural metrics from a synthetic benchmark report",
    )
    benchmark_model_comparison.add_argument(
        "--benchmark-report",
        required=True,
        help="path to K55 benchmark_report.json",
    )
    benchmark_model_comparison.add_argument(
        "--output-dir",
        help="optional directory for model_comparison.md/json/csv",
    )
    benchmark_model_comparison.add_argument(
        "--no-output-files",
        action="store_true",
        help="do not write model_comparison files even when output-dir is provided",
    )
    benchmark_model_comparison.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown comparison report",
    )
    benchmark_model_comparison.add_argument(
        "--csv",
        action="store_true",
        help="print CSV comparison rows",
    )
    benchmark_model_comparison.add_argument("--json", action="store_true", help="print JSON output")
    benchmark_model_comparison.set_defaults(handler=_handle_benchmark_model_comparison)

    benchmark_trend_report = subparsers.add_parser(
        "benchmark-trend-report",
        help="aggregate several synthetic benchmark reports into a trend report",
    )
    benchmark_trend_report.add_argument(
        "--benchmark-report",
        action="append",
        default=[],
        help="path to a K55 benchmark_report.json; may be repeated",
    )
    benchmark_trend_report.add_argument(
        "--benchmark-dir",
        action="append",
        default=[],
        help="directory to search recursively for benchmark_report.json files",
    )
    benchmark_trend_report.add_argument(
        "--output-dir",
        help="optional directory for benchmark trend Markdown/JSON/CSV files",
    )
    benchmark_trend_report.add_argument(
        "--no-output-files",
        action="store_true",
        help="do not write benchmark trend files even when output-dir is provided",
    )
    benchmark_trend_report.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown trend report",
    )
    benchmark_trend_report.add_argument(
        "--csv",
        action="store_true",
        help="print CSV metric and winner trend rows",
    )
    benchmark_trend_report.add_argument("--json", action="store_true", help="print JSON output")
    benchmark_trend_report.set_defaults(handler=_handle_benchmark_trend_report)

    dataset = subparsers.add_parser("generate-dataset", help="generate deterministic dataset rows")
    dataset.add_argument("--limit", type=int, required=True)
    dataset.add_argument("--output")
    dataset.add_argument("--split", action="store_true", help="export train/validation/test split")
    dataset.add_argument("--output-dir", default="data/generated")
    dataset.add_argument("--prefix", default="dataset_v003")
    dataset.add_argument("--report")
    dataset.add_argument("--seed", type=int, default=42)
    dataset.add_argument("--no-shuffle", action="store_true", help="preserve full-grid order")
    dataset.add_argument("--group-split", action="store_true", help="split by dataset group_key")
    dataset.add_argument("--load-duration", choices=("short",), required=True)
    dataset.add_argument("--json", action="store_true", help="print JSON output")
    dataset.set_defaults(handler=_handle_generate_dataset)

    validate = subparsers.add_parser("validate", help="run draft validation package checks")
    validate.add_argument("--golden", action="store_true", help="run draft golden cases")
    validate.add_argument("--dataset", help="validate an existing dataset CSV")
    validate.add_argument("--generate-dataset-limit", type=int)
    validate.add_argument("--output-report")
    validate.add_argument("--external-template")
    validate.add_argument("--external-input")
    validate.add_argument("--external-with-deltas")
    validate.add_argument("--acceptance-report")
    validate.add_argument("--max-delta-percent", type=float, default=5.0)
    validate.add_argument(
        "--required-external-source",
        choices=("any", "scad", "lira", "both"),
        default="any",
    )
    validate.add_argument("--no-require-engineer-accepted", action="store_true")
    validate.add_argument("--json", action="store_true", help="print JSON output")
    validate.set_defaults(handler=_handle_validate)

    materials_audit = subparsers.add_parser(
        "materials-audit",
        help="print draft material catalog audit rows",
    )
    materials_audit.add_argument(
        "--verification-template",
        action="store_true",
        help="print the material verification CSV template path",
    )
    materials_audit.add_argument(
        "--verification-csv",
        help="engineer-filled material verification CSV",
    )
    materials_audit.add_argument("--json", action="store_true", help="print JSON output")
    materials_audit.set_defaults(handler=_handle_materials_audit)

    material_verification = subparsers.add_parser(
        "material-verification",
        help="check engineer verification status for material catalog values",
    )
    material_verification.add_argument(
        "--template",
        action="store_true",
        help="print the material verification CSV template path",
    )
    material_verification.add_argument(
        "--markdown-template",
        action="store_true",
        help="print the material verification Markdown template path",
    )
    material_verification.add_argument("--csv", help="engineer-filled material verification CSV")
    material_verification.add_argument("--json", action="store_true", help="print JSON output")
    material_verification.set_defaults(handler=_handle_material_verification)

    material_verification_report = subparsers.add_parser(
        "material-verification-report",
        help="build Markdown/JSON report for an engineer-filled material verification CSV",
    )
    material_verification_report.add_argument(
        "--csv",
        required=True,
        help="engineer-filled material verification CSV",
    )
    material_verification_report.add_argument(
        "--output",
        help="optional Markdown report output path",
    )
    material_verification_report.add_argument(
        "--json",
        action="store_true",
        help="print JSON output",
    )
    material_verification_report.set_defaults(handler=_handle_material_verification_report)

    material_verification_closure = subparsers.add_parser(
        "material-verification-closure",
        help="build material verification closure evidence",
    )
    material_verification_closure.add_argument(
        "--material-verification-csv",
        help="engineer-filled material verification CSV",
    )
    material_verification_closure.add_argument(
        "--output-dir",
        help="optional output directory for closure report files",
    )
    material_verification_closure.add_argument(
        "--no-output-files",
        action="store_true",
        help="do not write closure report files",
    )
    material_verification_closure.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown output",
    )
    material_verification_closure.add_argument(
        "--json",
        action="store_true",
        help="print JSON output",
    )
    material_verification_closure.set_defaults(
        handler=_handle_material_verification_closure
    )

    manual_cases = subparsers.add_parser(
        "manual-cases",
        help="run manual SP63 verification cases",
    )
    manual_cases.add_argument("--json", action="store_true", help="print JSON output")
    manual_cases.set_defaults(handler=_handle_manual_cases)

    diagnostic_dataset = subparsers.add_parser(
        "diagnostic-dataset",
        help="generate deterministic diagnostic pass/fail/review dataset rows",
    )
    diagnostic_dataset.add_argument("--limit", type=int, default=100)
    diagnostic_dataset.add_argument("--json", action="store_true", help="print JSON output")
    diagnostic_dataset.set_defaults(handler=_handle_diagnostic_dataset)

    ml_readiness = subparsers.add_parser(
        "ml-readiness",
        help="check deterministic dataset readiness for later advisory ML",
    )
    ml_readiness.add_argument("--generate-dataset-limit", type=int, default=100)
    ml_readiness.add_argument(
        "--diagnostic",
        action="store_true",
        help=(
            "check diagnostic pass/fail/review dataset instead of the diagnostic "
            "regression pass-row dataset"
        ),
    )
    ml_readiness.add_argument("--json", action="store_true", help="print JSON output")
    ml_readiness.set_defaults(handler=_handle_ml_readiness)

    ml_external_readiness = subparsers.add_parser(
        "ml-external-readiness",
        help="check ML readiness with external validation and material verification context",
    )
    ml_external_readiness.add_argument(
        "--dataset",
        required=True,
        help="report-derived dataset path (jsonl, json, or csv)",
    )
    ml_external_readiness.add_argument(
        "--external-validation-csv",
        help="engineer-filled external validation CSV",
    )
    ml_external_readiness.add_argument(
        "--material-verification-csv",
        help="engineer-filled material verification CSV",
    )
    ml_external_readiness.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown readiness report",
    )
    ml_external_readiness.add_argument("--output", help="optional Markdown output path")
    ml_external_readiness.add_argument("--json", action="store_true", help="print JSON output")
    ml_external_readiness.set_defaults(handler=_handle_ml_external_readiness)

    ml_material_readiness = subparsers.add_parser(
        "ml-material-readiness",
        help="check material verification coverage for ML/report-derived datasets",
    )
    ml_material_readiness.add_argument(
        "--dataset",
        required=True,
        help="report-derived dataset path (jsonl, json, or csv)",
    )
    ml_material_readiness.add_argument(
        "--format",
        choices=("jsonl", "json", "csv"),
        help="dataset format; inferred from extension when omitted",
    )
    ml_material_readiness.add_argument(
        "--material-verification-csv",
        help="engineer-filled material verification CSV",
    )
    ml_material_readiness.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown readiness report",
    )
    ml_material_readiness.add_argument("--output", help="optional Markdown output path")
    ml_material_readiness.add_argument("--json", action="store_true", help="print JSON output")
    ml_material_readiness.set_defaults(handler=_handle_ml_material_readiness)

    engineering_ml_readiness = subparsers.add_parser(
        "engineering-ml-readiness",
        help="build an advisory engineering ML readiness bundle",
    )
    engineering_ml_readiness.add_argument(
        "--dataset",
        required=True,
        help="report-derived dataset path (jsonl, json, or csv)",
    )
    engineering_ml_readiness.add_argument(
        "--format",
        choices=("jsonl", "json", "csv"),
        help="dataset format; inferred from extension when omitted",
    )
    engineering_ml_readiness.add_argument(
        "--external-validation-csv",
        help="engineer-filled external validation CSV",
    )
    engineering_ml_readiness.add_argument(
        "--material-verification-csv",
        help="engineer-filled material verification CSV",
    )
    engineering_ml_readiness.add_argument("--benchmark-report", help="benchmark_report.json")
    engineering_ml_readiness.add_argument(
        "--benchmark-trend-report",
        help="benchmark_trend_report.json",
    )
    engineering_ml_readiness.add_argument(
        "--model-comparison-report",
        help="model_comparison.json",
    )
    engineering_ml_readiness.add_argument(
        "--ml-proposal-package-json",
        help="ml_proposal_package.json",
    )
    engineering_ml_readiness.add_argument(
        "--output-dir",
        help="optional directory for Markdown, JSON, CSV matrix, and README_REVIEW.md",
    )
    engineering_ml_readiness.add_argument(
        "--no-output-files",
        action="store_true",
        help="do not write output files even when output-dir is supplied",
    )
    engineering_ml_readiness.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown readiness bundle",
    )
    engineering_ml_readiness.add_argument(
        "--csv",
        action="store_true",
        help="print readiness matrix CSV",
    )
    engineering_ml_readiness.add_argument(
        "--json",
        action="store_true",
        help="print JSON output",
    )
    engineering_ml_readiness.set_defaults(handler=_handle_engineering_ml_readiness)

    ml_baseline = subparsers.add_parser(
        "ml-baseline",
        help="run non-neural baseline ML report for safe and diagnostic datasets",
    )
    ml_baseline.add_argument("--safe-limit", type=int, default=100)
    ml_baseline.add_argument("--diagnostic-limit", type=int, default=100)
    ml_baseline.add_argument("--seed", type=int, default=42)
    ml_baseline.add_argument("--json", action="store_true", help="print JSON output")
    ml_baseline.set_defaults(handler=_handle_ml_baseline)

    report_ml_baseline = subparsers.add_parser(
        "report-ml-baseline",
        help="run non-neural baseline ML on report-derived safe features",
    )
    report_ml_baseline.add_argument("--dataset", required=True, help="dataset file path")
    report_ml_baseline.add_argument(
        "--format",
        choices=("jsonl", "json", "csv"),
        help="dataset format; inferred from extension when omitted",
    )
    report_ml_baseline.add_argument("--target", default="overall_status")
    report_ml_baseline.add_argument(
        "--feature-mode",
        choices=("input_only", "deterministic_derived"),
        default="input_only",
    )
    report_ml_baseline.add_argument("--random-state", type=int, default=42)
    report_ml_baseline.add_argument("--json", action="store_true", help="print JSON output")
    report_ml_baseline.set_defaults(handler=_handle_report_ml_baseline)

    report_neural_surrogate = subparsers.add_parser(
        "report-neural-surrogate",
        help="run advisory neural surrogate on leakage-safe report-derived features",
    )
    report_neural_surrogate.add_argument("--dataset", required=True, help="dataset file path")
    report_neural_surrogate.add_argument(
        "--format",
        choices=("jsonl", "json", "csv"),
        help="dataset format; inferred from extension when omitted",
    )
    report_neural_surrogate.add_argument("--target", default="overall_status")
    report_neural_surrogate.add_argument(
        "--feature-mode",
        choices=("input_only", "deterministic_derived"),
        default="input_only",
    )
    report_neural_surrogate.add_argument("--hidden-layer-size", type=int, default=16)
    report_neural_surrogate.add_argument("--max-iter", type=int, default=500)
    report_neural_surrogate.add_argument("--random-state", type=int, default=42)
    report_neural_surrogate.add_argument("--json", action="store_true", help="print JSON output")
    report_neural_surrogate.set_defaults(handler=_handle_report_neural_surrogate)

    report_neural_predict = subparsers.add_parser(
        "report-neural-predict",
        help="run advisory neural prediction with deterministic report verification",
    )
    report_neural_predict.add_argument("--dataset", required=True, help="dataset file path")
    report_neural_predict.add_argument("--input-json", required=True, help="design input JSON")
    report_neural_predict.add_argument(
        "--format",
        choices=("jsonl", "json", "csv"),
        help="dataset format; inferred from extension when omitted",
    )
    report_neural_predict.add_argument("--target", default="overall_status")
    report_neural_predict.add_argument(
        "--feature-mode",
        choices=("input_only", "deterministic_derived"),
        default="input_only",
    )
    report_neural_predict.add_argument("--hidden-layer-size", type=int, default=16)
    report_neural_predict.add_argument("--max-iter", type=int, default=500)
    report_neural_predict.add_argument("--random-state", type=int, default=42)
    report_neural_predict.add_argument("--json", action="store_true", help="print JSON output")
    report_neural_predict.set_defaults(handler=_handle_report_neural_predict)

    neural_safety_audit = subparsers.add_parser(
        "neural-safety-audit",
        help="build an engineer-facing safety audit for a neural advisory prediction",
    )
    neural_safety_audit.add_argument("--dataset", required=True, help="dataset file path")
    neural_safety_audit.add_argument("--input-json", required=True, help="design input JSON")
    neural_safety_audit.add_argument(
        "--format",
        choices=("jsonl", "json", "csv"),
        help="dataset format; inferred from extension when omitted",
    )
    neural_safety_audit.add_argument("--target", default="overall_status")
    neural_safety_audit.add_argument(
        "--feature-mode",
        choices=("input_only", "deterministic_derived"),
        default="input_only",
    )
    neural_safety_audit.add_argument("--random-state", type=int, default=42)
    neural_safety_audit.add_argument("--json", action="store_true", help="print JSON output")
    neural_safety_audit.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown audit report",
    )
    neural_safety_audit.add_argument(
        "--output",
        help="write JSON or Markdown audit report to a file",
    )
    neural_safety_audit.set_defaults(handler=_handle_neural_safety_audit)

    ml_proposal_package = subparsers.add_parser(
        "ml-proposal-package",
        help="build advisory ML proposal package with deterministic SP63 verification",
    )
    ml_proposal_package.add_argument("--dataset", required=True, help="dataset file path")
    ml_proposal_package.add_argument("--input-json", required=True, help="design input JSON")
    ml_proposal_package.add_argument(
        "--format",
        choices=("jsonl", "json", "csv"),
        help="dataset format; inferred from extension when omitted",
    )
    ml_proposal_package.add_argument("--target", default="overall_status")
    ml_proposal_package.add_argument(
        "--feature-mode",
        choices=("input_only", "deterministic_derived"),
        default="input_only",
    )
    ml_proposal_package.add_argument("--hidden-layer-size", type=int, default=16)
    ml_proposal_package.add_argument("--max-iter", type=int, default=500)
    ml_proposal_package.add_argument("--random-state", type=int, default=42)
    ml_proposal_package.add_argument("--json", action="store_true", help="print JSON output")
    ml_proposal_package.add_argument(
        "--markdown",
        action="store_true",
        help="print Markdown proposal package report",
    )
    ml_proposal_package.add_argument(
        "--output",
        help="write JSON or Markdown proposal package report to a file",
    )
    ml_proposal_package.set_defaults(handler=_handle_ml_proposal_package)

    ml_proposal_review_package = subparsers.add_parser(
        "ml-proposal-review-package",
        help="build engineering review package and ZIP for an advisory ML proposal",
    )
    ml_proposal_review_package.add_argument("--dataset", required=True, help="dataset file path")
    ml_proposal_review_package.add_argument(
        "--input-json",
        required=True,
        help="design input JSON",
    )
    ml_proposal_review_package.add_argument(
        "--output-dir",
        required=True,
        help="output package directory",
    )
    ml_proposal_review_package.add_argument(
        "--format",
        choices=("jsonl", "json", "csv"),
        help="dataset format; inferred from extension when omitted",
    )
    ml_proposal_review_package.add_argument("--target", default="overall_status")
    ml_proposal_review_package.add_argument(
        "--feature-mode",
        choices=("input_only", "deterministic_derived"),
        default="input_only",
    )
    ml_proposal_review_package.add_argument("--hidden-layer-size", type=int, default=16)
    ml_proposal_review_package.add_argument("--max-iter", type=int, default=500)
    ml_proposal_review_package.add_argument("--random-state", type=int, default=42)
    ml_proposal_review_package.add_argument(
        "--no-zip",
        action="store_true",
        help="write package directory without ZIP export",
    )
    ml_proposal_review_package.add_argument(
        "--json",
        action="store_true",
        help="print JSON output",
    )
    ml_proposal_review_package.set_defaults(handler=_handle_ml_proposal_review_package)

    neural_surrogate = subparsers.add_parser(
        "neural-surrogate",
        help="run advisory-only neural surrogate smoke report",
    )
    neural_surrogate.add_argument("--diagnostic-limit", type=int, default=5000)
    neural_surrogate.add_argument("--seed", type=int, default=42)
    neural_surrogate.add_argument("--json", action="store_true", help="print JSON output")
    neural_surrogate.set_defaults(handler=_handle_neural_surrogate)

    ml_proposal_verify = subparsers.add_parser(
        "ml-proposal-verify",
        help="verify advisory ML proposals with deterministic SP63 checks",
    )
    ml_proposal_verify.add_argument("--json", action="store_true", help="print JSON output")
    ml_proposal_verify.set_defaults(handler=_handle_ml_proposal_verify)

    external_validation = subparsers.add_parser(
        "external-validation",
        help="summarize engineer-filled external validation comparison CSV",
    )
    external_validation.add_argument(
        "--template",
        action="store_true",
        help="print the external validation CSV template path",
    )
    external_validation.add_argument(
        "--sample",
        action="store_true",
        help="summarize the public synthetic/manual external validation sample",
    )
    external_validation.add_argument("--csv", help="engineer-filled external validation CSV")
    external_validation.add_argument(
        "--strict",
        action="store_true",
        help="enforce strict engineer-filled external validation acceptance gate",
    )
    external_validation.add_argument("--json", action="store_true", help="print JSON output")
    external_validation.set_defaults(handler=_handle_external_validation)

    baseline = subparsers.add_parser(
        "train-baseline",
        help="train experimental advisory baseline ML models",
    )
    baseline.add_argument("--dataset", help="existing dataset CSV")
    baseline.add_argument("--generate-dataset-limit", type=int, default=500)
    baseline.add_argument("--model-output", default="models/baseline_model.pkl")
    baseline.add_argument(
        "--metrics-output",
        default="reports/interim/baseline_metrics.json",
    )
    baseline.add_argument("--seed", type=int, default=42)
    baseline.add_argument("--json", action="store_true", help="print JSON output")
    baseline.set_defaults(handler=_handle_train_baseline)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run one CLI scenario."""
    args = build_parser().parse_args(argv)
    return args.handler(args)


def _add_section_arguments(parser: ArgumentParser) -> None:
    parser.add_argument("--b", type=float, required=True, help="section width, mm")
    parser.add_argument("--h", type=float, required=True, help="section height, mm")
    parser.add_argument(
        "--cover",
        type=float,
        required=True,
        help="distance from concrete face to outer stirrup surface, mm",
    )
    parser.add_argument(
        "--stirrup-diameter",
        type=float,
        required=True,
        help="stirrup diameter, mm",
    )
    parser.add_argument(
        "--main-bar-diameter",
        type=float,
        default=20.0,
        help="main bar diameter for section geometry, mm",
    )


def _add_orientation_arguments(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--local-axes-id",
        required=True,
        help="identifier of the declared local section axes",
    )
    parser.add_argument("--moment-axis", choices=("local_z",), required=True)
    parser.add_argument(
        "--tension-face",
        choices=("local_y_min", "local_y_max"),
        required=True,
    )


def _add_material_arguments(
    parser: ArgumentParser, *, include_rebar: bool = False, include_stirrup_rebar: bool = False
) -> None:
    parser.add_argument("--concrete", required=True, help="concrete class")
    if include_rebar:
        parser.add_argument("--rebar", required=True, help="longitudinal reinforcement class")
    if include_stirrup_rebar:
        parser.add_argument("--stirrup-rebar", required=True, help="stirrup reinforcement class")


def _add_design_arguments(parser: ArgumentParser) -> None:
    parser.add_argument("--b", type=float, required=True, help="section width, mm")
    parser.add_argument("--h", type=float, required=True, help="section height, mm")
    parser.add_argument(
        "--cover",
        type=float,
        required=True,
        help="distance from concrete face to outer stirrup surface, mm",
    )
    parser.add_argument(
        "--stirrup-diameter",
        type=float,
        required=True,
        help="stirrup diameter used for section geometry, mm",
    )
    parser.add_argument("--concrete", required=True, help="concrete class")
    parser.add_argument("--rebar", required=True, help="longitudinal reinforcement class")
    parser.add_argument("--stirrup-rebar", required=True, help="stirrup reinforcement class")
    parser.add_argument("--moment", type=float, required=True, help="bending moment, N*mm")
    parser.add_argument("--shear", type=float, required=True, help="shear force, N")
    _add_orientation_arguments(parser)
    parser.add_argument("--moment-ser", type=float, default=None, help="service moment, N*mm")
    parser.add_argument("--check-cracks", action="store_true", help="run Mcrc crack check")
    parser.add_argument("--check-crack-width", action="store_true", help="run acrc crack check")
    parser.add_argument("--acrc-limit", type=float, default=0.3, help="crack width limit, mm")
    parser.add_argument("--check-deflection", action="store_true", help="run deflection check")
    parser.add_argument("--span", type=float, default=None, help="beam span, mm")
    parser.add_argument("--deflection-limit", type=float, default=None, help="deflection limit, mm")
    parser.add_argument(
        "--deflection-limit-ratio",
        type=float,
        default=250.0,
        help="span divisor for default deflection limit",
    )
    parser.add_argument(
        "--deflection-loading-scheme",
        default="simply_supported_uniform",
        help="draft deflection loading scheme",
    )
    parser.add_argument("--load-duration", choices=("short", "long"), required=True)


def _section_from_args(args: Namespace) -> RectangularSection:
    return RectangularSection(
        b=args.b,
        h=args.h,
        cover=args.cover,
        stirrup_diameter=args.stirrup_diameter,
        main_bar_diameter=args.main_bar_diameter,
    )


def _orientation_from_args(args: Namespace) -> RectangularBendingOrientation:
    return RectangularBendingOrientation(
        local_axes_id=args.local_axes_id,
        moment_axis=args.moment_axis,
        tension_face=args.tension_face,
    )


def _handle_bending(args: Namespace) -> int:
    section = _section_from_args(args)
    concrete = get_concrete(args.concrete)
    rebar = get_rebar(args.rebar)
    bending = check_bending_rectangular(
        section=section,
        concrete=concrete,
        rebar=rebar,
        As=args.as_area,
        M=args.moment,
        orientation=_orientation_from_args(args),
        load_duration=args.load_duration,
    )
    reported_status = bending.public_status
    intermediate_values = bending.intermediate_values
    result = {
        "x": bending.x,
        "xi": bending.xi,
        "xi_R": bending.xi_R,
        "capacity_applicable": bending.capacity_applicable,
        "capacity_publication_allowed": bending.capacity_publication_allowed,
        "diagnostic_status": bending.diagnostic_status,
        "status_scope": bending.status_scope,
        "clause_8_1_3_status": bending.clause_8_1_3_status,
        "clause_8_1_3_decision_status": bending.clause_8_1_3_decision_status,
        "completeness_status": bending.completeness_status,
        "evidence_status": bending.evidence_status,
        "project_use_status": bending.project_use_status,
        "project_use": bending.project_use,
        "source_clause": bending.source_clause,
        "requires_engineer_review": bending.requires_engineer_review,
    }
    for field_name in (
        "x_limit",
        "Rb_base",
        "gamma_b1",
        "Rb_effective",
        "Rsc",
        "load_combination",
        "normative_profile_id",
        "local_axes_id",
        "moment_axis",
        "tension_face",
        "material_source_clauses",
        "layout_applicability_status",
        "manual_applicability_confirmation_required",
    ):
        if field_name in intermediate_values:
            result[field_name] = intermediate_values[field_name]
    if bending.capacity_publication_allowed and bending.Mult is not None:
        result["Mult"] = bending.Mult
    if bending.capacity_publication_allowed and bending.utilization is not None:
        result["utilization"] = bending.utilization
    if args.json:
        _print_json("bending", reported_status, result, bending.warnings)
        return 0

    print("Bending check")
    print(f"status: {reported_status}")
    print(f"diagnostic_status: {bending.diagnostic_status}")
    print(f"status_scope: {bending.status_scope}")
    print("x: not available" if bending.x is None else f"x: {bending.x:.2f} mm")
    print("xi: not available" if bending.xi is None else f"xi: {bending.xi:.3f}")
    print("xi_R: not available" if bending.xi_R is None else f"xi_R: {bending.xi_R:.3f}")
    if (
        not bending.capacity_publication_allowed
        or bending.Mult is None
        or bending.utilization is None
    ):
        print("M_ult not available: outside applicability")
    else:
        print(f"Mult: {bending.Mult:.2f} N*mm")
        print(f"utilization: {bending.utilization:.3f}")
    for field_name in (
        "material_source_clauses",
        "layout_applicability_status",
        "manual_applicability_confirmation_required",
    ):
        if field_name in intermediate_values:
            value = intermediate_values[field_name]
            rendered_value = str(value).lower() if isinstance(value, bool) else value
            print(f"{field_name}: {rendered_value}")
    print(f"completeness_status: {bending.completeness_status}")
    print(f"evidence_status: {bending.evidence_status}")
    print(f"project_use_status: {bending.project_use_status}")
    print(f"project_use: {str(bending.project_use).lower()}")
    print(f"requires_engineer_review: {str(bending.requires_engineer_review).lower()}")
    _print_warnings(bending.warnings)
    return 0


def _handle_shear(args: Namespace) -> int:
    section = _section_from_args(args)
    concrete = get_concrete(args.concrete)
    stirrup_rebar = get_rebar(args.stirrup_rebar)
    shear = check_shear_rectangular(
        section=section,
        concrete=concrete,
        stirrup_rebar=stirrup_rebar,
        Q=args.Q,
        Asw=args.Asw,
        sw=args.sw,
    )
    result = {
        "status_scope": "diagnostic_regression",
        "Q_strip": shear.Q_strip,
        "qsw": shear.qsw,
        "Qb": shear.Qb,
        "Qsw": shear.Qsw,
        "Qult": shear.Qult,
        "utilization": shear.utilization,
        "sw_max_by_shear_rule": shear.intermediate_values["sw_max_by_shear_rule"],
        "qsw_rule_status": shear.intermediate_values["qsw_rule_status"],
        "transverse_reinforcement_countable": shear.intermediate_values[
            "transverse_reinforcement_countable"
        ],
    }
    if args.json:
        _print_json("shear", shear.status, result, shear.warnings)
        return 0

    print("Shear check")
    print(f"status: {shear.status}")
    print("status_scope: diagnostic_regression")
    print(f"Q_strip: {shear.Q_strip:.2f} N")
    print(f"qsw: {shear.qsw:.2f} N/mm")
    print(f"Qb: {shear.Qb:.2f} N")
    print(f"Qsw: {shear.Qsw:.2f} N")
    print(f"Qult: {shear.Qult:.2f} N")
    print(f"utilization: {shear.utilization:.3f}")
    print(f"sw_max_by_shear_rule: {shear.intermediate_values['sw_max_by_shear_rule']:.2f} mm")
    print(f"qsw_rule_status: {shear.intermediate_values['qsw_rule_status']}")
    print(
        "transverse_reinforcement_countable: "
        f"{shear.intermediate_values['transverse_reinforcement_countable']}"
    )
    _print_warnings(shear.warnings)
    return 0


def _handle_crack_formation(args: Namespace) -> int:
    section = _section_from_args(args)
    concrete = get_concrete(args.concrete)
    crack = check_normal_crack_formation_rectangular(
        section=section,
        concrete=concrete,
        Mser=args.moment_ser,
    )
    result = {
        "Mser": crack.Mser,
        "Mcrc": crack.Mcrc,
        "utilization": crack.utilization,
        "W": crack.intermediate_values["W"],
        "Rbtser": crack.intermediate_values["Rbtser"],
        "model_status": crack.model_status,
        "clause_8_1_3_status": crack.clause_8_1_3_status,
        "clause_8_1_3_decision_status": crack.clause_8_1_3_decision_status,
        "usable_for_clause_8_1_3": crack.usable_for_clause_8_1_3,
        "evidence_status": crack.evidence_status,
        "project_use_status": crack.project_use_status,
        "project_use": crack.project_use,
    }
    if args.json:
        _print_json("crack-formation", crack.status, result, crack.warnings)
        return 0

    print("Crack formation")
    print(f"status: {crack.status}")
    print(f"Mser: {crack.Mser:.2f} N*mm")
    print(f"Mcrc: {crack.Mcrc:.2f} N*mm")
    print(f"utilization: {crack.utilization:.3f}")
    print(f"W: {crack.intermediate_values['W']:.2f} mm3")
    print(f"Rbtser: {crack.intermediate_values['Rbtser']:.3f} MPa")
    print(f"model_status: {crack.model_status}")
    print(f"clause_8_1_3_status: {crack.clause_8_1_3_status}")
    print(f"usable_for_clause_8_1_3: {str(crack.usable_for_clause_8_1_3).lower()}")
    _print_warnings(crack.warnings)
    return 0


def _handle_crack_width(args: Namespace) -> int:
    section = _section_from_args(args)
    concrete = get_concrete(args.concrete)
    rebar = get_rebar(args.rebar)
    crack_width = check_normal_crack_width_rectangular(
        section=section,
        concrete=concrete,
        rebar=rebar,
        Mser=args.moment_ser,
        As=args.as_area,
        main_bar_diameter=args.main_bar_diameter,
        acrc_limit=args.acrc_limit,
    )
    result = _crack_width_to_dict(crack_width)
    if args.json:
        _print_json("crack-width", crack_width.status, result, crack_width.warnings)
        return 0

    print("Crack width")
    print(f"status: {crack_width.status}")
    print(f"acrc: {crack_width.acrc:.6f} mm")
    print(f"acrc_limit: {crack_width.acrc_limit:.3f} mm")
    print(f"utilization: {crack_width.utilization:.3f}")
    print(f"sigma_s: {crack_width.sigma_s:.3f} MPa")
    print(f"epsilon_s: {crack_width.epsilon_s:.8f}")
    print(f"crack_spacing: {crack_width.crack_spacing:.2f} mm")
    print(f"Mcrc: {crack_width.Mcrc:.2f} N*mm")
    _print_warnings(crack_width.warnings)
    return 0


def _handle_deflection(args: Namespace) -> int:
    section = _section_from_args(args)
    concrete = get_concrete(args.concrete)
    rebar = get_rebar(args.rebar)
    deflection = check_curvature_deflection_rectangular(
        section=section,
        concrete=concrete,
        rebar=rebar,
        Mser=args.moment_ser,
        As=args.as_area,
        span=args.span,
        deflection_limit=args.deflection_limit,
        deflection_limit_ratio=args.deflection_limit_ratio,
        loading_scheme=args.loading_scheme,
    )
    result = _deflection_to_dict(deflection)
    if args.json:
        _print_json("deflection", deflection.status, result, deflection.warnings)
        return 0

    print("Deflection")
    print(f"status: {deflection.status}")
    print(f"curvature: {deflection.curvature:.10f} 1/mm")
    print(f"deflection: {deflection.deflection:.6f} mm")
    print(f"deflection_limit: {deflection.deflection_limit:.3f} mm")
    print(f"utilization: {deflection.utilization:.3f}")
    print(f"I_gross: {deflection.I_gross:.2f} mm4")
    print(f"I_cracked: {deflection.I_cracked:.2f} mm4")
    print(f"I_eff: {deflection.I_eff:.2f} mm4")
    print(f"stiffness_status: {deflection.stiffness_status}")
    print(f"Mcrc: {deflection.Mcrc:.2f} N*mm")
    _print_warnings(deflection.warnings)
    return 0


def _handle_select_longitudinal(args: Namespace) -> int:
    section = _section_from_args(args)
    concrete = get_concrete(args.concrete)
    rebar = get_rebar(args.rebar)
    options = select_longitudinal_rebar(
        section=section,
        concrete=concrete,
        rebar=rebar,
        M=args.moment,
        orientation=_orientation_from_args(args),
        load_duration=args.load_duration,
        max_results=args.max_results,
    )
    result = [_longitudinal_option_to_dict(option) for option in options]
    unsupported_profile = (
        rebar.class_name not in SUPPORTED_ULS_LONGITUDINAL_REBAR_CLASSES
    )
    if unsupported_profile:
        status = "outside_applicability"
        warnings = (
            f"unsupported ULS longitudinal rebar class {rebar.class_name!r}; "
            "no options were evaluated",
        )
    elif options and any(
        not option.bending.capacity_publication_allowed for option in options
    ):
        status = "outside_applicability"
        warnings = (
            "longitudinal candidates are diagnostic only because clause 8.1.3 "
            "is not checked; no option is approved for selection",
        )
    else:
        status = "pass" if options else "fail"
        warnings = () if options else ("no passing longitudinal reinforcement options",)
    selection_safety = {
        "completeness_status": (
            options[0].bending.completeness_status if options else "incomplete"
        ),
        "evidence_status": (
            options[0].bending.evidence_status if options else "needs_engineer_review"
        ),
        "project_use_status": (
            options[0].bending.project_use_status if options else "prohibited"
        ),
        "project_use": False,
        "status_scope": (
            options[0].bending.status_scope if options else "public"
        ),
        "requires_engineer_review": True,
    }
    if args.json:
        _print_json(
            "select-longitudinal",
            status,
            result,
            warnings,
            safety_statuses=selection_safety,
        )
        return 0

    print("Longitudinal reinforcement options")
    print(f"status: {status}")
    for field_name, value in selection_safety.items():
        rendered_value = str(value).lower() if isinstance(value, bool) else value
        print(f"{field_name}: {rendered_value}")
    for option in options:
        reinforcement_ratio = option.constructive.intermediate_values[
            "reinforcement_ratio_percent"
        ]
        print(
            f"{option.scheme}: As={option.As:.2f} mm2, "
            f"h0={option.section.effective_depth():.2f} mm, "
            f"diagnostic_utilization={option.diagnostic_utilization:.3f}, "
            f"constructive={option.constructive.status}, "
            f"reinforcement ratio={reinforcement_ratio:.3f}%, "
            "layout_feasible="
            f"{option.layout.layout_feasible}, status={option.bending.public_status}, "
            f"diagnostic_status={option.diagnostic_status}"
        )
    _print_warnings(warnings)
    return 0


def _handle_select_transverse(args: Namespace) -> int:
    section = _section_from_args(args)
    concrete = get_concrete(args.concrete)
    stirrup_rebar = get_rebar(args.stirrup_rebar)
    options = select_transverse_rebar(
        section=section,
        concrete=concrete,
        stirrup_rebar=stirrup_rebar,
        Q=args.Q,
        max_results=args.max_results,
    )
    result = [_transverse_option_to_dict(option) for option in options]
    status = "pass" if options else "fail"
    warnings = () if options else ("no passing transverse reinforcement options",)
    selection_safety = {
        "completeness_status": "incomplete",
        "evidence_status": "needs_engineer_review",
        "project_use_status": "prohibited",
        "project_use": False,
        "requires_engineer_review": True,
    }
    if args.json:
        _print_json(
            "select-transverse",
            status,
            result,
            warnings,
            safety_statuses=selection_safety,
        )
        return 0

    print("Transverse reinforcement options")
    print(f"status: {status}")
    for field_name, value in selection_safety.items():
        rendered_value = str(value).lower() if isinstance(value, bool) else value
        print(f"{field_name}: {rendered_value}")
    for option in options:
        max_spacing = option.constructive.intermediate_values["max_spacing"]
        sw_max_by_shear_rule = option.shear.intermediate_values["sw_max_by_shear_rule"]
        print(
            f"{option.scheme}: Asw={option.Asw:.2f} mm2, spacing={option.spacing:g} mm, "
            f"legs={option.legs}, utilization={option.utilization:.3f}, "
            f"h0={option.section.effective_depth():.2f} mm, "
            f"steel_consumption={option.steel_consumption:.4f}, "
            f"constructive={option.constructive.status}, max_spacing={max_spacing:.2f} mm, "
            f"sw_max_by_shear_rule={sw_max_by_shear_rule:.2f} mm, "
            f"qsw_rule_status={option.shear.intermediate_values['qsw_rule_status']}, "
            "transverse_reinforcement_countable="
            f"{option.shear.intermediate_values['transverse_reinforcement_countable']}, "
            f"status={option.status}"
        )
    _print_warnings(warnings)
    return 0


def _handle_design_rectangular(args: Namespace) -> int:
    design_input = RectangularDesignInput(
        b=args.b,
        h=args.h,
        cover=args.cover,
        stirrup_diameter_for_geometry=args.stirrup_diameter,
        concrete_class=args.concrete,
        longitudinal_rebar_class=args.rebar,
        stirrup_rebar_class=args.stirrup_rebar,
        M=args.moment,
        Q=args.shear,
        local_axes_id=args.local_axes_id,
        moment_axis=args.moment_axis,
        tension_face=args.tension_face,
        load_duration=args.load_duration,
        Mser=args.moment_ser,
        check_cracks=args.check_cracks,
        check_crack_width=args.check_crack_width,
        acrc_limit=args.acrc_limit,
        check_deflection=args.check_deflection,
        span=args.span,
        deflection_limit=args.deflection_limit,
        deflection_limit_ratio=args.deflection_limit_ratio,
        deflection_loading_scheme=args.deflection_loading_scheme,
    )
    design = design_rectangular_element(design_input)
    result = _design_result_to_dict(design)
    if args.json:
        _print_json("design-rectangular", design.status, result, design.warnings)
        return 0

    print("Rectangular design")
    print(f"status: {design.status}")
    print(f"strength_status: {design.strength_status}")
    print(f"serviceability_status: {design.serviceability_status}")
    print(f"overall_status: {design.overall_status}")
    print(f"completeness_status: {design.completeness_status}")
    print(f"evidence_status: {design.evidence_status}")
    print(f"project_use_status: {design.project_use_status}")
    print(f"project_use: {str(design.project_use).lower()}")
    print(
        "requires_engineer_review: "
        f"{str(design.requires_engineer_review).lower()}"
    )
    if design.selected_longitudinal is not None:
        longitudinal = design.selected_longitudinal
        print(f"selected longitudinal scheme: {longitudinal.scheme}")
        print(f"As: {longitudinal.As:.2f} mm2")
        print(f"h0: {longitudinal.section.effective_depth():.2f} mm")
        print(
            "diagnostic bending utilization: "
            f"{longitudinal.diagnostic_utilization:.3f}"
        )
        print(f"longitudinal constructive status: {longitudinal.constructive.status}")
        print(
            "longitudinal reinforcement ratio: "
            f"{longitudinal.constructive.intermediate_values['reinforcement_ratio_percent']:.3f}%"
        )
    if design.selected_transverse is not None:
        transverse = design.selected_transverse
        print(f"selected transverse scheme: {transverse.scheme}")
        print(f"Asw: {transverse.Asw:.2f} mm2")
        print(f"spacing: {transverse.spacing:g} mm")
        print(f"legs: {transverse.legs}")
        print(f"shear utilization: {transverse.utilization:.3f}")
        print(f"stirrup constructive status: {transverse.constructive.status}")
        print(
            "stirrup max_spacing: "
            f"{transverse.constructive.intermediate_values['max_spacing']:.2f} mm"
        )
        print(
            "stirrup sw_max_by_shear_rule: "
            f"{transverse.shear.intermediate_values['sw_max_by_shear_rule']:.2f} mm"
        )
        print(f"stirrup qsw_rule_status: {transverse.shear.intermediate_values['qsw_rule_status']}")
        print(
            "stirrup transverse_reinforcement_countable: "
            f"{transverse.shear.intermediate_values['transverse_reinforcement_countable']}"
        )
    if design.crack_formation is not None:
        crack = design.crack_formation
        print(f"crack_formation_status: {crack.status}")
        print(f"Mcrc: {crack.Mcrc:.2f} N*mm")
        print(f"crack_utilization: {crack.utilization:.3f}")
    if design.crack_width is not None:
        crack_width = design.crack_width
        print(f"crack_width_status: {crack_width.status}")
        print(f"acrc: {crack_width.acrc:.6f} mm")
        print(f"acrc_limit: {crack_width.acrc_limit:.3f} mm")
        print(f"crack_width_utilization: {crack_width.utilization:.3f}")
    if design.deflection is not None:
        deflection = design.deflection
        print(f"deflection_status: {deflection.status}")
        print(f"curvature: {deflection.curvature:.10f} 1/mm")
        print(f"deflection: {deflection.deflection:.6f} mm")
        print(f"deflection_limit: {deflection.deflection_limit:.3f} mm")
        print(f"deflection_utilization: {deflection.utilization:.3f}")
    _print_warnings(design.warnings)
    return 0


def _handle_design_report(args: Namespace) -> int:
    design, source = _build_design_report_result(args)
    include_html = bool(args.html or args.bundle_output)
    report = build_rectangular_design_report(design, include_html=include_html)
    json_payload = _design_report_json_payload(report, source=source)

    if args.bundle_output:
        output_files = _write_design_report_bundle(
            report,
            json_payload,
            Path(args.bundle_output),
            input_json_path=Path(args.input_json) if args.input_json else None,
            create_manifest=not args.no_manifest,
        )
        if args.json:
            json_payload["bundle_output"] = str(Path(args.bundle_output))
            json_payload["output_files"] = output_files
            print(jsonlib.dumps(json_payload, ensure_ascii=False, indent=2))
            return 0
        print(f"Design report bundle written: {args.bundle_output}")
        return 0

    if args.html:
        content = report.html if report.html is not None else ""
    elif args.json:
        content = jsonlib.dumps(json_payload, ensure_ascii=False, indent=2)
    else:
        content = report.markdown

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        print(f"Design report written: {output_path}")
        return 0

    print(content, end="" if content.endswith("\n") else "\n")
    return 0


def _handle_design_report_batch(args: Namespace) -> int:
    input_paths = _collect_batch_design_report_inputs(args)
    result = build_batch_design_reports(
        input_paths=input_paths,
        output_dir=Path(args.output_dir),
        include_html=True,
    )
    if args.json:
        payload = {
            "command": "design-report-batch",
            "status": result.status,
            "input_count": result.input_count,
            "report_count": result.report_count,
            "passed_count": result.passed_count,
            "review_count": result.review_count,
            "failed_count": result.failed_count,
            "output_dir": result.output_dir,
            "warnings": list(result.warnings),
            "completeness_status": result.completeness_status,
            "evidence_status": result.evidence_status,
            "project_use_status": result.project_use_status,
            "project_use": result.project_use,
            "requires_engineer_review": result.requires_engineer_review,
            "index": result.index_json,
        }
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"Batch design reports written: {result.output_dir}")
    print(f"status: {result.status}")
    print(f"input_count: {result.input_count}")
    print(f"report_count: {result.report_count}")
    print(f"completeness_status: {result.completeness_status}")
    print(f"evidence_status: {result.evidence_status}")
    print(f"project_use_status: {result.project_use_status}")
    print(f"project_use: {str(result.project_use).lower()}")
    print(f"index.md: {Path(result.output_dir) / 'index.md'}")
    print(f"index.json: {Path(result.output_dir) / 'index.json'}")
    _print_warnings(result.warnings)
    return 0


def _handle_synthetic_report_inputs(args: Namespace) -> int:
    result = generate_synthetic_report_inputs(
        output_dir=Path(args.output_dir),
        case_count=args.case_count,
        seed=args.seed,
        include_serviceability=not args.no_serviceability,
    )
    payload = {
        "command": "synthetic-report-inputs",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Synthetic report input generation")
    print(f"status: {result.status}")
    print(f"output_dir: {result.output_dir}")
    print(f"case_count: {result.case_count}")
    print(f"generated_count: {result.generated_count}")
    print(f"skipped_count: {result.skipped_count}")
    print(f"seed: {result.seed}")
    print(f"synthetic_data_only: {result.synthetic_data_only}")
    print(f"requires_engineer_review: {result.requires_engineer_review}")
    print(f"ml_is_advisory_only: {result.ml_is_advisory_only}")
    print(f"deterministic_checks_required: {result.deterministic_checks_required}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_guided_synthetic_inputs(args: Namespace) -> int:
    target_distribution_goal = {
        "pass": args.target_pass,
        "fail": args.target_fail,
        "review_or_fail": args.target_review,
    }
    result = generate_guided_synthetic_inputs(
        output_dir=Path(args.output_dir),
        target_distribution_goal=target_distribution_goal,
        seed=args.seed,
        max_attempts=args.max_attempts,
        include_serviceability=not args.no_serviceability,
    )
    payload = {
        "command": "guided-synthetic-inputs",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Guided synthetic report input generation")
    print(f"status: {result.status}")
    print(f"output_dir: {result.output_dir}")
    print(f"target_distribution_goal: {result.target_distribution_goal}")
    print(f"generated_count: {result.generated_count}")
    print(f"accepted_count: {result.accepted_count}")
    print(f"rejected_count: {result.rejected_count}")
    print(f"final_distribution: {result.final_distribution}")
    print(f"seed: {result.seed}")
    print(f"max_attempts: {result.max_attempts}")
    print(f"synthetic_data_only: {result.synthetic_data_only}")
    print(f"completeness_status: {result.completeness_status}")
    print(f"evidence_status: {result.evidence_status}")
    print(f"project_use_status: {result.project_use_status}")
    print(f"project_use: {str(result.project_use).lower()}")
    print(f"requires_engineer_review: {result.requires_engineer_review}")
    print(f"ml_is_advisory_only: {result.ml_is_advisory_only}")
    print(f"deterministic_checks_required: {result.deterministic_checks_required}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_report_archive_validate(args: Namespace) -> int:
    archive_path = Path(args.path)
    is_batch = bool(args.batch or (archive_path / "index.json").exists())
    result = (
        validate_batch_report_archive(archive_path)
        if is_batch
        else validate_report_bundle(archive_path)
    )
    payload = {
        "command": "report-archive-validate",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Report archive validation")
    print(f"status: {result.status}")
    print(f"archive_path: {result.archive_path}")
    print(f"manifest_count: {result.manifest_count}")
    print(f"checked_file_count: {result.checked_file_count}")
    print(f"missing_file_count: {result.missing_file_count}")
    print(f"checksum_mismatch_count: {result.checksum_mismatch_count}")
    print(f"index_consistency_status: {result.index_consistency_status}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_report_archive_zip(args: Namespace) -> int:
    result = export_report_archive_to_zip(
        source_path=Path(args.path),
        zip_path=Path(args.output),
    )
    payload = {
        "command": "report-archive-zip",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Report archive ZIP export")
    print(f"status: {result.status}")
    print(f"source_path: {result.source_path}")
    print(f"zip_path: {result.zip_path}")
    print(f"file_count: {result.file_count}")
    print(f"zip_sha256: {result.zip_sha256}")
    print(f"validation_status: {result.validation_status}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_engineering_workflow(args: Namespace) -> int:
    result = run_engineering_workflow(
        input_json_path=Path(args.input_json),
        output_dir=Path(args.output_dir),
        dataset_path=Path(args.dataset) if args.dataset else None,
        dataset_format=args.format,
        external_validation_csv=(
            Path(args.external_validation_csv) if args.external_validation_csv else None
        ),
        material_verification_csv=(
            Path(args.material_verification_csv) if args.material_verification_csv else None
        ),
        include_ml_readiness=args.include_ml_readiness,
        create_zip=not args.no_zip,
        with_index=args.with_index,
        with_preflight=args.with_preflight,
    )
    payload = {
        "command": "engineering-workflow",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        summary_path = Path(result.output_dir) / "workflow_summary.md"
        print(summary_path.read_text(encoding="utf-8"), end="")
        return 0

    print("Engineering workflow")
    print(f"status: {result.status}")
    print(f"workflow_status: {result.workflow_status}")
    print(f"completeness_status: {result.completeness_status}")
    print(f"evidence_status: {result.evidence_status}")
    print(f"project_use_status: {result.project_use_status}")
    print(f"project_use: {str(result.project_use).lower()}")
    print(f"preflight_status: {result.preflight_status}")
    print(f"deterministic_report_status: {result.deterministic_report_status}")
    print(f"archive_validation_status: {result.archive_validation_status}")
    print(f"zip_status: {result.zip_status}")
    print(f"ml_readiness_status: {result.ml_readiness_status}")
    print(f"output_dir: {result.output_dir}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_engineering_workflow_batch(args: Namespace) -> int:
    result = run_engineering_workflow_batch(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        with_preflight=args.with_preflight,
        with_index=args.with_index,
        create_zip=not args.no_zip,
    )
    payload = {
        "command": "engineering-workflow-batch",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        summary_path = Path(result.batch_summary_markdown_path)
        print(summary_path.read_text(encoding="utf-8"), end="")
        return 0

    print("Batch engineering workflow")
    print(f"status: {result.status}")
    print(f"batch_status: {result.batch_status}")
    print(f"completeness_status: {result.completeness_status}")
    print(f"evidence_status: {result.evidence_status}")
    print(f"project_use_status: {result.project_use_status}")
    print(f"project_use: {str(result.project_use).lower()}")
    print(f"command_exit_status: {result.command_exit_status}")
    print(f"case_count: {result.case_count}")
    print(f"passed_count: {result.passed_count}")
    print(f"review_required_count: {result.review_required_count}")
    print(f"failed_count: {result.failed_count}")
    print(f"failed_cases: {', '.join(result.failed_cases) or 'none'}")
    print(f"output_dir: {result.output_dir}")
    if result.recommendations:
        print("recommendations:")
        for recommendation in result.recommendations:
            print(f"- {recommendation}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_engineering_report_index(args: Namespace) -> int:
    result = build_static_workflow_report_index(
        workflow_dir=Path(args.workflow_dir),
        output_path=Path(args.output) if args.output else None,
        title=args.title,
    )
    open_browser_status = "not_requested"
    warnings = list(result.warnings)
    if args.open_in_browser:
        try:
            opened = webbrowser.open(Path(result.output_path).resolve().as_uri())
        except OSError as exc:
            opened = False
            warnings.append(f"open-in-browser failed: {exc}")
        open_browser_status = "opened" if opened else "not_opened"
        if not opened:
            warnings.append("open-in-browser requested but browser did not open")

    payload = {
        "command": "engineering-report-index",
        **asdict(result),
        "warnings": tuple(dict.fromkeys(warnings)),
        "open_browser_status": open_browser_status,
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Engineering workflow report index")
    print(f"status: {result.status}")
    print(f"index_status: {result.index_status}")
    print(f"workflow_dir: {result.workflow_dir}")
    print(f"output_path: {result.output_path}")
    print(f"linked_files: {len(result.linked_files)}")
    print(f"missing_expected_files: {len(result.missing_expected_files)}")
    print(f"open_browser_status: {open_browser_status}")
    _print_warnings(tuple(dict.fromkeys(warnings)))
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_engineering_workflow_self_check(args: Namespace) -> int:
    result = run_engineering_workflow_self_check(
        output_dir=Path(args.output_dir),
        include_ml_readiness=args.include_ml_readiness,
        dataset_path=Path(args.dataset) if args.dataset else None,
        external_validation_csv=(
            Path(args.external_validation_csv) if args.external_validation_csv else None
        ),
        material_verification_csv=(
            Path(args.material_verification_csv) if args.material_verification_csv else None
        ),
        cleanup=args.cleanup,
    )
    payload = {
        "command": "engineering-workflow-self-check",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(render_self_check_markdown(result), end="")
        return 0

    print("Engineering workflow self-check")
    print(f"status: {result.status}")
    print(f"self_check_status: {result.self_check_status}")
    print(f"passed_checks: {result.passed_checks}")
    print(f"failed_checks: {result.failed_checks}")
    print(f"skipped_checks: {result.skipped_checks}")
    print(f"deterministic_workflow_status: {result.deterministic_workflow_status}")
    print(f"deterministic_archive_status: {result.deterministic_archive_status}")
    print(f"deterministic_zip_status: {result.deterministic_zip_status}")
    print(f"ml_workflow_status: {result.ml_workflow_status}")
    print(f"output_dir: {result.output_dir}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_clean_demo_workflow(args: Namespace) -> int:
    result = run_clean_demo_workflow(output_dir=Path(args.output_dir))
    payload = {
        "command": "clean-demo-workflow",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        summary_path = Path(result.output_dir) / "clean_demo_workflow.md"
        print(summary_path.read_text(encoding="utf-8"), end="")
        return 0

    print("Clean deterministic demo workflow")
    print(f"status: {result.status}")
    print(f"demo_status: {result.demo_status}")
    print(f"workflow_status: {result.workflow_status}")
    print(f"preflight_status: {result.preflight_status}")
    print(f"deterministic_report_status: {result.deterministic_report_status}")
    print(f"archive_validation_status: {result.archive_validation_status}")
    print(f"zip_status: {result.zip_status}")
    print(f"index_status: {result.index_status}")
    print(f"output_dir: {result.output_dir}")
    print(f"ml_ready_for_project_use: {result.ml_ready_for_project_use}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_clean_demo_verify(args: Namespace) -> int:
    if args.run:
        if not args.output_dir:
            raise SystemExit("--output-dir is required with --run")
        result = run_clean_demo_and_verify(output_dir=Path(args.output_dir))
    else:
        if not args.workflow_dir:
            raise SystemExit("--workflow-dir is required unless --run is used")
        result = verify_clean_demo_artifacts(workflow_dir=Path(args.workflow_dir))

    payload = {
        "command": "clean-demo-verify",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0
    if args.markdown:
        print(Path(result.summary_markdown_path).read_text(encoding="utf-8"), end="")
        return 1 if result.status == "fail" else 0

    print("Clean demo verification")
    print(f"status: {result.status}")
    print(f"verification_status: {result.verification_status}")
    print(f"workflow_dir: {result.workflow_dir}")
    print(f"missing_artifacts: {len(result.missing_artifacts)}")
    print(f"ml_ready_true_files: {len(result.ml_ready_true_files)}")
    print(f"warning_artifacts_present: {result.warning_artifacts_present}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_engineering_handoff_package(args: Namespace) -> int:
    result = build_engineering_handoff_package(output_dir=Path(args.output_dir))
    payload = {
        "command": "engineering-handoff-package",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Engineering handoff package")
    print(f"status: {result.status}")
    print(f"package_status: {result.package_status}")
    print(f"output_dir: {result.output_dir}")
    print(f"file_count: {result.file_count}")
    print(f"manifest_path: {result.manifest_path}")
    print(f"ml_ready_for_project_use: {result.ml_ready_for_project_use}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_launcher_scripts(args: Namespace) -> int:
    result = build_launcher_scripts_package(output_dir=Path(args.output_dir))
    payload = {
        "command": "launcher-scripts",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Launcher scripts package")
    print(f"status: {result.status}")
    print(f"package_status: {result.package_status}")
    print(f"script_count: {result.script_count}")
    print(f"output_dir: {result.output_dir}")
    print(f"manifest_path: {result.manifest_path}")
    print(f"ml_ready_for_project_use: {result.ml_ready_for_project_use}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_external_validation_evidence_package(args: Namespace) -> int:
    result = build_external_validation_evidence_package(
        output_dir=Path(args.output_dir),
        external_validation_csv=(
            Path(args.external_validation_csv) if args.external_validation_csv else None
        ),
        strict_mode=args.strict,
    )
    payload = {
        "command": "external-validation-evidence-package",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("External validation evidence package")
    print(f"status: {result.status}")
    print(f"evidence_status: {result.evidence_status}")
    print(f"total_cases: {result.total_cases}")
    print(f"accepted_cases: {result.accepted_cases}")
    print(f"review_cases: {result.review_cases}")
    print(f"failed_cases: {result.failed_cases}")
    print(f"output_dir: {result.output_dir}")
    print(f"manifest_path: {result.manifest_path}")
    print(f"ml_ready_for_project_use: {result.ml_ready_for_project_use}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_engineering_interface_contract(args: Namespace) -> int:
    output_dir = None
    if args.output_dir and not args.no_output_files:
        output_dir = Path(args.output_dir)
    result = build_engineering_interface_contract(output_dir=output_dir)
    payload = {
        "command": "engineering-interface-contract",
        "status": result.status,
        "contract_status": result.contract_status,
        "workflow_names": result.workflow_names,
        "required_screens": result.required_screens,
        "required_inputs": result.required_inputs,
        "required_outputs": result.required_outputs,
        "mandatory_warnings": result.mandatory_warnings,
        "forbidden_ui_actions": result.forbidden_ui_actions,
        "recommended_cli_commands": result.recommended_cli_commands,
        "output_dir": result.output_dir,
        "requires_engineer_review": result.requires_engineer_review,
        "ml_is_advisory_only": result.ml_is_advisory_only,
        "deterministic_checks_required": result.deterministic_checks_required,
        "ml_ready_for_project_use": result.ml_ready_for_project_use,
        "warnings": result.warnings,
        "errors": result.errors,
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(result.markdown, end="")
        return 0

    print("Engineering interface contract")
    print(f"status: {result.status}")
    print(f"contract_status: {result.contract_status}")
    print(f"output_dir: {result.output_dir}")
    print(f"workflow_count: {len(result.workflow_names)}")
    print(f"required_screen_count: {len(result.required_screens)}")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    return 0


def _handle_engineering_gui_planning(args: Namespace) -> int:
    output_dir = None
    if args.output_dir and not args.no_output_files:
        output_dir = Path(args.output_dir)
    result = build_engineering_gui_planning_decision(output_dir=output_dir)
    payload = {
        "command": "engineering-gui-planning",
        "status": result.status,
        "decision_status": result.decision_status,
        "recommended_option": result.recommended_option,
        "considered_options": result.considered_options,
        "rejected_options": result.rejected_options,
        "required_backend_commands": result.required_backend_commands,
        "required_safety_warnings": result.required_safety_warnings,
        "recommended_next_step": result.recommended_next_step,
        "output_dir": str(output_dir) if output_dir is not None else None,
        "requires_engineer_review": result.requires_engineer_review,
        "ml_is_advisory_only": result.ml_is_advisory_only,
        "deterministic_checks_required": result.deterministic_checks_required,
        "ml_ready_for_project_use": result.ml_ready_for_project_use,
        "warnings": result.warnings,
        "errors": result.errors,
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(result.markdown, end="")
        return 0

    print("Engineering GUI planning")
    print(f"status: {result.status}")
    print(f"decision_status: {result.decision_status}")
    print(f"recommended_option: {result.recommended_option}")
    print(f"recommended_next_step: {result.recommended_next_step}")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    return 0


def _handle_input_form_schema(args: Namespace) -> int:
    output_dir = None
    if args.output_dir and not args.no_output_files:
        output_dir = Path(args.output_dir)
    result = build_input_form_schema(output_dir=output_dir)
    payload = {
        "command": "input-form-schema",
        "status": result.status,
        "schema_status": result.schema_status,
        "output_dir": result.output_dir,
        "field_count": result.field_count,
        "required_fields": result.required_fields,
        "optional_fields": result.optional_fields,
        "validation_rules_count": result.validation_rules_count,
        "requires_engineer_review": result.requires_engineer_review,
        "ml_is_advisory_only": result.ml_is_advisory_only,
        "deterministic_checks_required": result.deterministic_checks_required,
        "ml_ready_for_project_use": result.ml_ready_for_project_use,
        "warnings": result.warnings,
        "errors": result.errors,
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(result.markdown, end="")
        return 0

    print("Input form schema")
    print(f"status: {result.status}")
    print(f"schema_status: {result.schema_status}")
    print(f"field_count: {result.field_count}")
    print(f"validation_rules_count: {result.validation_rules_count}")
    print(f"output_dir: {result.output_dir}")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    return 0


def _handle_input_preflight(args: Namespace) -> int:
    output_dir = None
    if args.output_dir and not args.no_output_files:
        output_dir = Path(args.output_dir)
    result = run_input_preflight(
        Path(args.input_json),
        output_dir=output_dir,
    )
    payload = {
        "command": "input-preflight",
        "status": result.status,
        "preflight_status": result.preflight_status,
        "input_json_path": result.input_json_path,
        "output_dir": result.output_dir,
        "checked_fields": result.checked_fields,
        "required_fields": result.required_fields,
        "optional_fields": result.optional_fields,
        "missing_required_fields": result.missing_required_fields,
        "unknown_fields": result.unknown_fields,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "issues": [asdict(issue) for issue in result.issues],
        "requires_engineer_review": result.requires_engineer_review,
        "ml_is_advisory_only": result.ml_is_advisory_only,
        "deterministic_checks_required": result.deterministic_checks_required,
        "ml_ready_for_project_use": result.ml_ready_for_project_use,
        "warnings": result.warnings,
        "errors": result.errors,
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(result.markdown, end="")
        return 0

    print("Input JSON preflight")
    print(f"status: {result.status}")
    print(f"preflight_status: {result.preflight_status}")
    print(f"input_json_path: {result.input_json_path}")
    print(f"output_dir: {result.output_dir}")
    print(f"checked_fields: {len(result.checked_fields)}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_input_form_preview(args: Namespace) -> int:
    output_dir = None
    if args.output_dir and not args.no_output_files:
        output_dir = Path(args.output_dir)
    result = build_static_input_form_preview(output_dir=output_dir)
    payload = {
        "command": "input-form-preview",
        "status": result.status,
        "preview_status": result.preview_status,
        "output_dir": result.output_dir,
        "output_path": result.output_path,
        "schema_field_count": result.schema_field_count,
        "generated_files": result.generated_files,
        "requires_engineer_review": result.requires_engineer_review,
        "ml_is_advisory_only": result.ml_is_advisory_only,
        "deterministic_checks_required": result.deterministic_checks_required,
        "ml_ready_for_project_use": result.ml_ready_for_project_use,
        "warnings": result.warnings,
        "errors": result.errors,
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(result.markdown, end="")
        return 0

    print("Input form preview")
    print(f"status: {result.status}")
    print(f"preview_status: {result.preview_status}")
    print(f"schema_field_count: {result.schema_field_count}")
    print(f"output_dir: {result.output_dir}")
    print(f"output_path: {result.output_path}")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    return 0


def _handle_diagnostics_catalog(args: Namespace) -> int:
    output_dir = None
    if args.output_dir and not args.no_output_files:
        output_dir = Path(args.output_dir)
    result = build_diagnostics_catalog(output_dir=output_dir)
    payload = {
        "command": "diagnostics-catalog",
        "status": result.status,
        "catalog_status": result.catalog_status,
        "diagnostics_count": result.diagnostics_count,
        "categories": result.categories,
        "diagnostics": result.json_data["diagnostics"],
        "requires_engineer_review": result.requires_engineer_review,
        "ml_is_advisory_only": result.ml_is_advisory_only,
        "deterministic_checks_required": result.deterministic_checks_required,
        "ml_ready_for_project_use": result.ml_ready_for_project_use,
        "warnings": result.warnings,
        "errors": result.errors,
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(result.markdown, end="")
        return 0

    print("Diagnostics catalog")
    print(f"status: {result.status}")
    print(f"catalog_status: {result.catalog_status}")
    print(f"diagnostics_count: {result.diagnostics_count}")
    print(f"categories: {', '.join(result.categories)}")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_docs_audit(args: Namespace) -> int:
    result = build_docs_audit_report(
        output_dir=Path(args.output_dir) if args.output_dir else None,
    )
    payload = {
        "command": "docs-audit",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(render_docs_audit_markdown(result), end="")
        return 0

    print("Documentation audit")
    print(f"status: {result.status}")
    print(f"docs_audit_status: {result.docs_audit_status}")
    print(f"markdown_files_count: {result.markdown_files_count}")
    print(f"local_link_count: {result.local_link_count}")
    print(f"missing_local_links: {len(result.missing_local_links)}")
    print(f"required_commands_missing: {len(result.required_commands_missing)}")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_evidence_templates(args: Namespace) -> int:
    result = build_evidence_templates_package(output_dir=Path(args.output_dir))
    payload = {
        "command": "evidence-templates",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Evidence templates package")
    print(f"status: {result.status}")
    print(f"package_status: {result.package_status}")
    print(f"output_dir: {result.output_dir}")
    print(f"external_validation_template_path: {result.external_validation_template_path}")
    print(f"material_verification_template_path: {result.material_verification_template_path}")
    print(f"manifest_path: {result.manifest_path}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_project_template(args: Namespace) -> int:
    result = build_project_template_package(output_dir=Path(args.output_dir))
    payload = {
        "command": "project-template",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Project template package")
    print(f"status: {result.status}")
    print(f"package_status: {result.package_status}")
    print(f"output_dir: {result.output_dir}")
    print(f"generated_files: {len(result.generated_files)}")
    print(f"manifest_path: {result.manifest_path}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_protected_files_check(args: Namespace) -> int:
    result = run_protected_files_guard(
        base_ref=args.base_ref,
        head_ref=args.head_ref,
        allow_review_required=args.allow_review_required,
    )
    payload = {
        "command": "protected-files-check",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0

    print("Protected files check")
    print(f"status: {result.status}")
    print(f"guard_status: {result.guard_status}")
    print(f"checked_git_ref: {result.checked_git_ref}")
    print(f"base_ref: {result.base_ref}")
    print(f"head_ref: {result.head_ref}")
    print(f"github_actions_detected: {result.github_actions_detected}")
    print(f"changed_protected_files: {len(result.changed_protected_files)}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_user_manual_index(args: Namespace) -> int:
    result = build_user_manual_index(
        manual_dir=Path(args.manual_dir),
        output_dir=Path(args.output_dir) if args.output_dir else None,
    )
    payload = {
        "command": "user-manual-index",
        "status": result.status,
        "manual_status": result.manual_status,
        "manual_dir": result.manual_dir,
        "required_files": result.required_files,
        "existing_files": result.existing_files,
        "missing_files": result.missing_files,
        "output_dir": result.output_dir,
        "requires_engineer_review": result.requires_engineer_review,
        "ml_is_advisory_only": result.ml_is_advisory_only,
        "deterministic_checks_required": result.deterministic_checks_required,
        "ml_ready_for_project_use": result.ml_ready_for_project_use,
        "warnings": result.warnings,
        "errors": result.errors,
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(result.markdown, end="")
        return 0

    print("User manual index")
    print(f"status: {result.status}")
    print(f"manual_status: {result.manual_status}")
    print(f"manual_dir: {result.manual_dir}")
    print(f"required_files: {len(result.required_files)}")
    print(f"missing_files: {len(result.missing_files)}")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_release_candidate_report(args: Namespace) -> int:
    result = build_release_candidate_report(
        output_dir=Path(args.output_dir),
        version=args.version,
    )
    payload = {
        "command": "release-candidate-report",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        report_path = Path(result.output_dir) / "release_candidate_report.md"
        print(report_path.read_text(encoding="utf-8"), end="")
        return 0

    print("Release candidate report")
    print(f"status: {result.status}")
    print(f"release_candidate_status: {result.release_candidate_status}")
    print(f"version: {result.version}")
    print(f"output_dir: {result.output_dir}")
    print(f"protected_files_guard_status: {result.protected_files_guard_status}")
    print(f"user_manual_status: {result.user_manual_status}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_release_manifest(args: Namespace) -> int:
    result = build_release_artifact_manifest(
        output_dir=Path(args.output_dir),
        version=args.version,
    )
    payload = {
        "command": "release-manifest",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(Path(result.markdown_path).read_text(encoding="utf-8"), end="")
        return 0

    print("Release artifact manifest")
    print(f"status: {result.status}")
    print(f"manifest_status: {result.manifest_status}")
    print(f"version: {result.version}")
    print(f"git_commit: {result.git_commit}")
    print(f"artifact_count: {result.artifact_count}")
    print(f"output_dir: {result.output_dir}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_release_bundle(args: Namespace) -> int:
    result = build_release_bundle(
        output_dir=Path(args.output_dir),
        version=args.version,
    )
    payload = {
        "command": "release-bundle",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0
    if args.markdown:
        print(Path(result.report_markdown_path).read_text(encoding="utf-8"), end="")
        return 1 if result.status == "fail" else 0

    print("Release bundle")
    print(f"status: {result.status}")
    print(f"bundle_status: {result.bundle_status}")
    print(f"version: {result.version}")
    print(f"zip_path: {result.zip_path}")
    print(f"file_count: {result.file_count}")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_traceability_matrix(args: Namespace) -> int:
    result = build_traceability_matrix(
        output_dir=Path(args.output_dir) if args.output_dir else None,
    )
    payload = {
        "command": "traceability-matrix",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0
    if args.markdown:
        print(render_traceability_matrix_markdown(result), end="")
        return 1 if result.status == "fail" else 0

    print("Traceability matrix")
    print(f"status: {result.status}")
    print(f"matrix_status: {result.matrix_status}")
    print(f"row_count: {result.row_count}")
    print(f"output_dir: {result.output_dir}")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_release_notes(args: Namespace) -> int:
    result = build_release_notes_package(
        output_dir=Path(args.output_dir),
        version=args.version,
    )
    payload = {
        "command": "release-notes",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(Path(result.release_notes_markdown_path).read_text(encoding="utf-8"), end="")
        return 0

    print("Release notes package")
    print(f"status: {result.status}")
    print(f"package_status: {result.package_status}")
    print(f"version: {result.version}")
    print(f"output_dir: {result.output_dir}")
    print(f"release_notes_markdown_path: {result.release_notes_markdown_path}")
    print(f"ml_ready_for_project_use: {result.ml_ready_for_project_use}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_user_acceptance_smoke(args: Namespace) -> int:
    result = run_user_acceptance_smoke(
        output_dir=Path(args.output_dir),
        version=args.version,
    )
    payload = {
        "command": "user-acceptance-smoke",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(Path(result.summary_markdown_path).read_text(encoding="utf-8"), end="")
        return 0

    print("User acceptance smoke")
    print(f"status: {result.status}")
    print(f"user_acceptance_status: {result.user_acceptance_status}")
    print(f"smoke_count: {result.smoke_count}")
    print(f"passed_count: {result.passed_count}")
    print(f"review_required_count: {result.review_required_count}")
    print(f"failed_count: {result.failed_count}")
    print(f"output_dir: {result.output_dir}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_v09_readiness(args: Namespace) -> int:
    result = build_v09_readiness_gate(
        output_dir=Path(args.output_dir),
        version=args.version,
    )
    payload = {
        "command": "v09-readiness",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(Path(result.summary_markdown_path).read_text(encoding="utf-8"), end="")
        return 0

    print("v0.9 readiness gate")
    print(f"status: {result.status}")
    print(f"readiness_status: {result.readiness_status}")
    print(f"gate_count: {result.gate_count}")
    print(f"passed_count: {result.passed_count}")
    print(f"review_required_count: {result.review_required_count}")
    print(f"failed_count: {result.failed_count}")
    print(f"output_dir: {result.output_dir}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_v09_final_audit(args: Namespace) -> int:
    result = build_v09_final_audit(
        output_dir=Path(args.output_dir),
        version=args.version,
    )
    payload = {
        "command": "v09-final-audit",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(Path(result.summary_markdown_path).read_text(encoding="utf-8"), end="")
        return 0

    print("v0.9 final audit")
    print(f"status: {result.status}")
    print(f"audit_status: {result.audit_status}")
    print(f"audit_count: {result.audit_count}")
    print(f"passed_count: {result.passed_count}")
    print(f"review_required_count: {result.review_required_count}")
    print(f"failed_count: {result.failed_count}")
    print(f"output_dir: {result.output_dir}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_v10_gap_report(args: Namespace) -> int:
    result = build_v10_gap_report(output_dir=Path(args.output_dir))
    payload = {
        "command": "v10-gap-report",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0
    if args.markdown:
        print(render_v10_gap_report_markdown(result), end="")
        return 1 if result.status == "fail" else 0

    print("v1.0 gap report")
    print(f"status: {result.status}")
    print(f"report_status: {result.report_status}")
    print(f"ready_for_v10: {result.ready_for_v10}")
    print(f"remaining_steps_estimate: {result.remaining_steps_estimate}")
    print(f"output_dir: {result.output_dir}")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_v09_freeze_report(args: Namespace) -> int:
    result = build_v09_freeze_report(
        output_dir=Path(args.output_dir),
        version=args.version,
    )
    payload = {
        "command": "v09-freeze-report",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0
    if args.markdown:
        print(render_v09_freeze_report_markdown(result), end="")
        return 1 if result.status == "fail" else 0

    print("v0.9 freeze report")
    print(f"status: {result.status}")
    print(f"freeze_status: {result.freeze_status}")
    print(f"version: {result.version}")
    print(f"critical_failed_count: {result.critical_failed_count}")
    print(f"review_required_count: {result.review_required_count}")
    print("project_use_allowed: false")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_freeze_remediation_plan(args: Namespace) -> int:
    result = build_freeze_remediation_plan(
        output_dir=Path(args.output_dir),
        version=args.version,
    )
    payload = {
        "command": "freeze-remediation-plan",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0
    if args.markdown:
        print(render_freeze_remediation_plan_markdown(result), end="")
        return 1 if result.status == "fail" else 0

    print("Freeze remediation plan")
    print(f"status: {result.status}")
    print(f"plan_status: {result.plan_status}")
    print(f"version: {result.version}")
    print(f"blocker_count: {result.blocker_count}")
    print(f"acceptable_review_gate_count: {result.acceptable_review_gate_count}")
    print("project_use_allowed: false")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_windows_smoke_plan(args: Namespace) -> int:
    result = build_windows_smoke_plan(output_dir=Path(args.output_dir))
    payload = {
        "command": "windows-smoke-plan",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0

    print("Windows smoke plan")
    print(f"status: {result.status}")
    print(f"command_count: {result.command_count}")
    print("project_use_allowed: false")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_engineer_review_packet(args: Namespace) -> int:
    result = build_engineer_review_packet(output_dir=Path(args.output_dir))
    payload = {
        "command": "engineer-review-packet",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0
    if args.markdown:
        print(render_engineer_review_packet_markdown(result), end="")
        return 1 if result.status == "fail" else 0

    print("Engineer review packet")
    print(f"status: {result.status}")
    print(f"packet_status: {result.packet_status}")
    print(f"evidence_count: {result.evidence_count}")
    print(f"review_required_count: {result.review_required_count}")
    print(f"failed_count: {result.failed_count}")
    print("project_use_allowed: false")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_static_launcher_dashboard(args: Namespace) -> int:
    result = build_static_launcher_dashboard(output_dir=Path(args.output_dir))
    payload = {
        "command": "static-launcher-dashboard",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0

    print("Static launcher dashboard")
    print(f"status: {result.status}")
    print(f"command_count: {result.command_count}")
    print("web_server_required: false")
    print("javascript_calculations_present: false")
    print("project_use_allowed: false")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_release_acceptance_checklist(args: Namespace) -> int:
    result = build_release_acceptance_checklist(output_dir=Path(args.output_dir))
    payload = {
        "command": "release-acceptance-checklist",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0
    if args.markdown:
        print(render_release_acceptance_checklist_markdown(result), end="")
        return 1 if result.status == "fail" else 0

    print("Release acceptance checklist")
    print(f"status: {result.status}")
    print(f"item_count: {result.item_count}")
    print(f"machine_pass_count: {result.machine_pass_count}")
    print(f"manual_signoff_required_count: {result.manual_signoff_required_count}")
    print(f"review_required_count: {result.review_required_count}")
    print(f"failed_count: {result.failed_count}")
    print("project_use_allowed: false")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_review_signoff_templates(args: Namespace) -> int:
    result = build_review_signoff_templates(output_dir=Path(args.output_dir))
    payload = {
        "command": "review-signoff-templates",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0

    print("Review signoff templates")
    print(f"status: {result.status}")
    print(f"template_count: {result.template_count}")
    print("project_use_allowed: false")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_v09_review_build(args: Namespace) -> int:
    result = build_v09_review_build(
        output_dir=Path(args.output_dir),
        version=args.version,
    )
    payload = {
        "command": "v09-review-build",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0
    if args.markdown:
        print(render_v09_review_build_markdown(result), end="")
        return 1 if result.status == "fail" else 0

    print("v0.9 review build")
    print(f"status: {result.status}")
    print(f"review_build_status: {result.review_build_status}")
    print(f"artifact_count: {result.artifact_count}")
    print(f"critical_failed_count: {result.critical_failed_count}")
    print(f"review_required_count: {result.review_required_count}")
    print("project_use_allowed: false")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_v09_review_closure(args: Namespace) -> int:
    result = build_v09_review_closure(
        output_dir=Path(args.output_dir),
        version=args.version,
    )
    payload = {
        "command": "v09-review-closure",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0
    if args.markdown:
        print(render_v09_review_closure_markdown(result), end="")
        return 1 if result.status == "fail" else 0

    print("v0.9 review closure")
    print(f"status: {result.status}")
    print(f"closure_status: {result.closure_status}")
    print(f"ready_for_v09_review_build: {result.ready_for_v09_review_build}")
    print(f"ready_for_v09_release_candidate: {result.ready_for_v09_release_candidate}")
    print("ready_for_project_use: false")
    print("ml_ready_for_project_use: false")
    print(f"critical_failures: {len(result.critical_failures)}")
    print(f"blocking_review_gates: {len(result.blocking_review_gates)}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_v09_release_candidate_package(args: Namespace) -> int:
    result = build_v09_release_candidate_package(
        output_dir=Path(args.output_dir),
        version=args.version,
    )
    payload = {
        "command": "v09-release-candidate-package",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0
    if args.markdown:
        print(render_v09_release_candidate_package_markdown(result), end="")
        return 1 if result.status == "fail" else 0

    print("v0.9 release candidate package")
    print(f"status: {result.status}")
    print(f"package_status: {result.package_status}")
    print(f"ready_for_engineering_review: {result.ready_for_engineering_review}")
    print("ready_for_project_use: false")
    print("ml_ready_for_project_use: false")
    print(f"critical_failures: {len(result.critical_failures)}")
    print(f"review_required_gates: {len(result.review_required_gates)}")
    print(f"zip_path: {result.zip_path}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_v09_package_verify(args: Namespace) -> int:
    package_dir = Path(args.package_dir) if args.package_dir else None
    result = verify_v09_release_candidate_package(
        package_dir=package_dir,
        output_dir=Path(args.output_dir),
        build=args.build,
        version=args.version,
    )
    payload = {
        "command": "v09-package-verify",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0
    if args.markdown:
        print(render_v09_package_verification_markdown(result), end="")
        return 1 if result.status == "fail" else 0

    print("v0.9 package verification")
    print(f"status: {result.status}")
    print(f"verification_status: {result.verification_status}")
    print(f"ready_for_manual_review: {result.ready_for_manual_review}")
    print("ready_for_project_use: false")
    print("ml_ready_for_project_use: false")
    print(f"missing_required_paths: {len(result.missing_required_paths)}")
    print(f"missing_zip_entries: {len(result.missing_zip_entries)}")
    print(f"forbidden_package_paths: {len(result.forbidden_package_paths)}")
    print(f"forbidden_zip_entries: {len(result.forbidden_zip_entries)}")
    print(f"manual_review_gates: {len(result.manual_review_gates)}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_next_release_roadmap(args: Namespace) -> int:
    result = build_next_release_roadmap(output_dir=Path(args.output_dir))
    payload = {
        "command": "next-release-roadmap",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0
    if args.markdown:
        print(render_next_release_roadmap_markdown(result), end="")
        return 1 if result.status == "fail" else 0

    print("Next release roadmap")
    print(f"status: {result.status}")
    print(f"section_count: {result.section_count}")
    print(f"review_required_count: {result.review_required_count}")
    print("project_use_allowed: false")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_agent_sprint_guard(args: Namespace) -> int:
    result = build_agent_sprint_guard(from_k=args.from_k, to_k=args.to_k)
    payload = {
        "command": "agent-sprint-guard",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Agent sprint guard")
    print(f"status: {result.status}")
    print(f"guard_status: {result.guard_status}")
    print(f"from_k: {result.from_k}")
    print(f"to_k: {result.to_k}")
    print(f"checked_step_count: {result.checked_step_count}")
    print(f"completed_count: {result.completed_count}")
    print(f"missing_count: {result.missing_count}")
    print(f"proposed_next_k: {result.proposed_next_k}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_cli_status_contract(args: Namespace) -> int:
    result = build_cli_status_contract(
        output_dir=Path(args.output_dir) if args.output_dir else None,
    )
    payload = {
        "command": "cli-status-contract",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0
    if args.markdown:
        print(render_cli_status_contract_markdown(result), end="")
        return 1 if result.status == "fail" else 0

    print("CLI status contract")
    print(f"status: {result.status}")
    print(f"contract_status: {result.contract_status}")
    print(f"command_count: {result.command_count}")
    print(f"output_dir: {result.output_dir}")
    print("exit_code_mapping:")
    for status, exit_code in result.exit_code_mapping.items():
        print(f"- {status}: {exit_code}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_json_output_contract(args: Namespace) -> int:
    result = build_json_output_contract(
        output_dir=Path(args.output_dir) if args.output_dir else None,
    )
    payload = {
        "command": "json-output-contract",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0
    if args.markdown:
        print(render_json_output_contract_markdown(result), end="")
        return 1 if result.status == "fail" else 0

    print("JSON output contract")
    print(f"status: {result.status}")
    print(f"contract_status: {result.contract_status}")
    print(f"contract_count: {result.contract_count}")
    print(f"output_dir: {result.output_dir}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_portable_package(args: Namespace) -> int:
    result = build_portable_package(output_dir=Path(args.output_dir))
    payload = {
        "command": "portable-package",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if result.status == "fail" else 0

    print("Portable package")
    print(f"status: {result.status}")
    print(f"package_status: {result.package_status}")
    print(f"output_dir: {result.output_dir}")
    print(f"file_count: {result.file_count}")
    print(f"script_count: {result.script_count}")
    print(f"manifest_path: {result.manifest_path}")
    print("ml_ready_for_project_use: false")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 1 if result.status == "fail" else 0


def _handle_report_dataset_export(args: Namespace) -> int:
    result = export_dataset_from_report_archive(
        source_path=Path(args.path),
        output_path=Path(args.output) if args.output else None,
        output_format=args.format,
        require_archive_validation=not args.no_archive_validation,
    )
    payload = {
        "command": "report-dataset-export",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Report dataset export")
    print(f"status: {result.status}")
    print(f"source_path: {result.source_path}")
    print(f"output_path: {result.output_path}")
    print(f"row_count: {result.row_count}")
    print(f"skipped_count: {result.skipped_count}")
    print(f"input_error_count: {result.input_error_count}")
    print(f"archive_validation_status: {result.archive_validation_status}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_report_dataset_quality(args: Namespace) -> int:
    result = run_report_dataset_quality_gate(
        dataset_path=Path(args.dataset),
        dataset_format=args.format,
        task=args.task,
        min_rows=args.min_rows,
        require_status_diversity=not args.no_require_status_diversity,
    )
    payload = {
        "command": "report-dataset-quality",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Report dataset quality gate")
    print(f"status: {result.status}")
    print(f"source_path: {result.source_path}")
    print(f"row_count: {result.row_count}")
    print(f"column_count: {result.column_count}")
    print(f"required_columns_present: {result.required_columns_present}")
    print(f"empty_critical_values_count: {result.empty_critical_values_count}")
    print(f"provenance_columns_present: {result.provenance_columns_present}")
    print(f"advisory_flags_present: {result.advisory_flags_present}")
    print(f"status_distribution: {result.status_distribution}")
    if result.leakage_columns_detected:
        print("leakage_columns_detected:")
        for column in result.leakage_columns_detected:
            print(f"- {column}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_report_dataset_features(args: Namespace) -> int:
    result = build_report_dataset_feature_set(
        dataset_path=Path(args.dataset),
        dataset_format=args.format,
        target=args.target,
        feature_mode=args.feature_mode,
        split=not args.no_split,
        train_ratio=args.train_ratio,
        validation_ratio=args.validation_ratio,
        test_ratio=args.test_ratio,
        random_state=args.random_state,
    )
    payload = {
        "command": "report-dataset-features",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Report dataset feature set")
    print(f"status: {result.status}")
    print(f"source_path: {result.source_path}")
    print(f"row_count: {result.row_count}")
    print(f"feature_count: {result.feature_count}")
    print(f"target: {result.target}")
    print(f"target_distribution: {result.target_distribution}")
    print(f"split_strategy: {result.split_strategy}")
    print(f"train_count: {result.train_count}")
    print(f"validation_count: {result.validation_count}")
    print(f"test_count: {result.test_count}")
    if result.feature_columns:
        print("feature_columns:")
        for column in result.feature_columns:
            print(f"- {column}")
    if result.excluded_leakage_columns:
        print("excluded_leakage_columns:")
        for column in result.excluded_leakage_columns:
            print(f"- {column}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_synthetic_dataset_balance(args: Namespace) -> int:
    dataset_path = Path(args.dataset)
    result = analyze_synthetic_dataset_balance(
        dataset_path=dataset_path,
        dataset_format=args.format,
        target=args.target,
        min_rows=args.min_rows,
        min_class_count=args.min_class_count,
        max_imbalance_ratio=args.max_imbalance_ratio,
        train_ratio=args.train_ratio,
        validation_ratio=args.validation_ratio,
        test_ratio=args.test_ratio,
        random_state=args.random_state,
    )
    split_index_output = None
    if args.split_index_output:
        rows = load_report_dataset_rows(dataset_path, args.format)
        split_summary = build_stratified_split_summary(
            rows=rows,
            target=args.target,
            train_ratio=args.train_ratio,
            validation_ratio=args.validation_ratio,
            test_ratio=args.test_ratio,
            random_state=args.random_state,
        )
        split_index_path = Path(args.split_index_output)
        split_index_path.parent.mkdir(parents=True, exist_ok=True)
        split_payload = {
            "command": "synthetic-dataset-balance",
            "source_dataset": str(dataset_path),
            "target": args.target,
            **split_summary,
            "synthetic_data_only": result.synthetic_data_only,
            "requires_engineer_review": result.requires_engineer_review,
            "ml_is_advisory_only": result.ml_is_advisory_only,
            "deterministic_checks_required": result.deterministic_checks_required,
        }
        split_index_path.write_text(
            jsonlib.dumps(split_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        split_index_output = str(split_index_path)

    payload = {
        "command": "synthetic-dataset-balance",
        **asdict(result),
        "split_index_output": split_index_output,
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Synthetic dataset balance")
    print(f"status: {result.status}")
    print(f"source_dataset: {result.source_dataset}")
    print(f"row_count: {result.row_count}")
    print(f"target: {result.target}")
    print(f"target_distribution: {result.target_distribution}")
    print(f"min_class_count: {result.min_class_count}")
    print(f"max_class_count: {result.max_class_count}")
    print(f"imbalance_ratio: {result.imbalance_ratio}")
    print(f"required_classes_present: {result.required_classes_present}")
    print(f"stratified_split_ready: {result.stratified_split_ready}")
    print(f"train_count: {result.train_count}")
    print(f"validation_count: {result.validation_count}")
    print(f"test_count: {result.test_count}")
    if split_index_output:
        print(f"split_index_output: {split_index_output}")
    if result.missing_required_classes:
        print("missing_required_classes:")
        for class_name in result.missing_required_classes:
            print(f"- {class_name}")
    if result.leakage_columns_detected:
        print("leakage_columns_detected:")
        for column in result.leakage_columns_detected:
            print(f"- {column}")
    if result.recommendations:
        print("recommendations:")
        for recommendation in result.recommendations:
            print(f"- {recommendation}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_synthetic_ml_benchmark(args: Namespace) -> int:
    target_distribution_goal = {
        "pass": args.target_pass,
        "fail": args.target_fail,
        "review_or_fail": args.target_review,
    }
    result = run_synthetic_ml_benchmark(
        output_dir=Path(args.output_dir),
        target_distribution_goal=target_distribution_goal,
        seed=args.seed,
        max_attempts=args.max_attempts,
        include_serviceability=not args.no_serviceability,
        target=args.target,
        feature_mode=args.feature_mode,
        create_reports=not args.no_reports,
    )
    payload = {
        "command": "synthetic-ml-benchmark",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print((Path(result.output_dir) / "benchmark_report.md").read_text(encoding="utf-8"))
        return 0

    print("Synthetic ML benchmark")
    print(f"status: {result.status}")
    print(f"benchmark_status: {result.benchmark_status}")
    print(f"output_dir: {result.output_dir}")
    print(f"target_distribution_goal: {result.target_distribution_goal}")
    print(f"final_distribution: {result.final_distribution}")
    print(f"generated_count: {result.generated_count}")
    print(f"accepted_count: {result.accepted_count}")
    print(f"rejected_count: {result.rejected_count}")
    print(f"report_count: {result.report_count}")
    print(f"dataset_row_count: {result.dataset_row_count}")
    print(f"balance_status: {result.balance_status}")
    print(f"quality_status: {result.quality_status}")
    print(f"feature_status: {result.feature_status}")
    print(f"baseline_status: {result.baseline_status}")
    print(f"neural_status: {result.neural_status}")
    print(f"synthetic_data_only: {result.synthetic_data_only}")
    print(f"requires_engineer_review: {result.requires_engineer_review}")
    print(f"ml_is_advisory_only: {result.ml_is_advisory_only}")
    print(f"deterministic_checks_required: {result.deterministic_checks_required}")
    if result.recommendations:
        print("recommendations:")
        for recommendation in result.recommendations:
            print(f"- {recommendation}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_benchmark_model_comparison(args: Namespace) -> int:
    output_dir = None
    if args.output_dir and not args.no_output_files:
        output_dir = Path(args.output_dir)
    result = build_benchmark_model_comparison(
        benchmark_report_path=Path(args.benchmark_report),
        output_dir=output_dir,
    )
    payload = {
        "command": "benchmark-model-comparison",
        **result.json_data,
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(result.markdown, end="" if result.markdown.endswith("\n") else "\n")
        return 0
    if args.csv:
        print("metric,baseline,neural,winner")
        for row in result.csv_rows:
            print(f"{row['metric']},{row['baseline']},{row['neural']},{row['winner']}")
        return 0

    print("Benchmark model comparison")
    print(f"status: {result.status}")
    print(f"comparison_status: {result.comparison_status}")
    print(f"benchmark_report_path: {result.benchmark_report_path}")
    print(f"output_dir: {result.output_dir}")
    print(f"dataset_row_count: {result.dataset_row_count}")
    print(f"final_distribution: {result.final_distribution}")
    print(f"baseline_status: {result.baseline_status}")
    print(f"neural_status: {result.neural_status}")
    print(f"metric_winners: {result.metric_winners}")
    print(f"synthetic_data_only: {result.synthetic_data_only}")
    print(f"requires_engineer_review: {result.requires_engineer_review}")
    print(f"ml_is_advisory_only: {result.ml_is_advisory_only}")
    print(f"deterministic_checks_required: {result.deterministic_checks_required}")
    if result.recommendations:
        print("recommendations:")
        for recommendation in result.recommendations:
            print(f"- {recommendation}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_benchmark_trend_report(args: Namespace) -> int:
    report_paths = [Path(path) for path in args.benchmark_report]
    for benchmark_dir in args.benchmark_dir:
        report_paths.extend(discover_benchmark_reports(Path(benchmark_dir)))
    report_paths = list(dict.fromkeys(report_paths))
    output_dir = None
    if args.output_dir and not args.no_output_files:
        output_dir = Path(args.output_dir)
    result = build_benchmark_trend_report(
        benchmark_report_paths=report_paths,
        output_dir=output_dir,
    )
    payload = {
        "command": "benchmark-trend-report",
        **result.json_data,
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(result.markdown, end="" if result.markdown.endswith("\n") else "\n")
        return 0
    if args.csv:
        print("row_type,model,metric,count,mean,min,max,std,missing_count")
        for row in result.csv_rows:
            print(
                "metric,"
                f"{row['model']},{row['metric']},{row['count']},{row['mean']},"
                f"{row['min']},{row['max']},{row['std']},{row['missing_count']}"
            )
        print("row_type,metric,baseline_win_count,neural_win_count,tie_count,missing_count")
        for metric, row in result.winner_summary.items():
            print(
                "winner,"
                f"{metric},{row['baseline_win_count']},{row['neural_win_count']},"
                f"{row['tie_count']},{row['missing_count']}"
            )
        return 0

    print("Benchmark trend report")
    print(f"status: {result.status}")
    print(f"trend_status: {result.trend_status}")
    print(f"benchmark_count: {result.benchmark_count}")
    print(f"output_dir: {result.output_dir}")
    print(f"dataset_row_count_summary: {result.dataset_row_count_summary}")
    print(f"distribution_summary: {result.distribution_summary}")
    print(f"winner_summary: {result.winner_summary}")
    print(f"synthetic_data_only: {result.synthetic_data_only}")
    print(f"requires_engineer_review: {result.requires_engineer_review}")
    print(f"ml_is_advisory_only: {result.ml_is_advisory_only}")
    print(f"deterministic_checks_required: {result.deterministic_checks_required}")
    if result.recommendations:
        print("recommendations:")
        for recommendation in result.recommendations:
            print(f"- {recommendation}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _collect_batch_design_report_inputs(args: Namespace) -> tuple[Path, ...]:
    input_paths: list[Path] = [Path(path) for path in args.input_json]
    if args.input_dir:
        input_dir = Path(args.input_dir)
        input_paths.extend(
            path
            for path in sorted(input_dir.glob("*.json"))
            if path.name
            not in {
                "index.json",
                "manifest.json",
                "synthetic_manifest.json",
                "guided_synthetic_manifest.json",
            }
        )
    if not input_paths:
        raise ValueError("design-report-batch requires --input-dir or at least one --input-json")
    return tuple(dict.fromkeys(input_paths))


def _build_design_report_result(args: Namespace) -> tuple[Any, str]:
    if args.input_json:
        design_input = load_rectangular_design_input_from_json(args.input_json)
        return (
            design_rectangular_element(design_input),
            "input_json",
        )
    return _build_design_report_smoke_result(), "smoke_example"


def _build_design_report_smoke_result() -> Any:
    design_input = RectangularDesignInput(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter_for_geometry=8,
        concrete_class="B25",
        longitudinal_rebar_class="A500",
        stirrup_rebar_class="A240",
        M=150_000_000,
        Q=80_000,
        local_axes_id="design-report-smoke-local-axes",
        moment_axis="local_z",
        tension_face="local_y_min",
        load_duration="short",
        Mser=30_000_000,
        check_cracks=True,
        check_crack_width=True,
        check_deflection=True,
        span=6000,
    )
    return design_rectangular_element(design_input)


def _design_report_json_payload(report: Any, *, source: str) -> dict[str, Any]:
    data = report.json_data
    return {
        "command": "design-report",
        "source": source,
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


def _write_design_report_bundle(
    report: Any,
    json_payload: dict[str, Any],
    output_dir: Path,
    *,
    input_json_path: Path | None = None,
    create_manifest: bool = True,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = output_dir / "report.md"
    json_path = output_dir / "report.json"
    html_path = output_dir / "report.html"
    markdown_path.write_text(report.markdown, encoding="utf-8")
    json_text = jsonlib.dumps(json_payload, ensure_ascii=False, indent=2)
    json_path.write_text(json_text, encoding="utf-8")
    html = report.html if report.html is not None else ""
    html_path.write_text(html, encoding="utf-8")
    output_files = {
        "markdown": str(markdown_path),
        "json": str(json_path),
        "html": str(html_path),
    }
    if input_json_path is not None:
        input_copy_path = output_dir / "input.json"
        shutil.copyfile(input_json_path, input_copy_path)
        output_files["input"] = str(input_copy_path)
    if create_manifest:
        manifest_path = output_dir / "manifest.json"
        manifest = build_report_manifest(
            report_type=report.report_type,
            command="design-report",
            input_paths=() if input_json_path is None else (input_json_path,),
            output_paths=tuple(Path(path) for path in output_files.values()),
            status=report.status,
            strength_status=report.strength_status,
            serviceability_status=report.serviceability_status,
            overall_status=report.overall_status,
            warnings_count=len(report.warnings),
            completeness_status=report.completeness_status,
            evidence_status=report.evidence_status,
            project_use_status=report.project_use_status,
        )
        write_report_manifest_json(manifest, manifest_path)
        readme_path = output_dir / "README_REVIEW.md"
        readme_path.write_text(
            build_review_readme_for_single_bundle(
                bundle_path=output_dir,
                manifest_path=manifest_path,
            ),
            encoding="utf-8",
        )
        output_files["review_readme"] = str(readme_path)
        manifest = build_report_manifest(
            report_type=report.report_type,
            command="design-report",
            input_paths=() if input_json_path is None else (input_json_path,),
            output_paths=tuple(Path(path) for path in output_files.values()),
            status=report.status,
            strength_status=report.strength_status,
            serviceability_status=report.serviceability_status,
            overall_status=report.overall_status,
            warnings_count=len(report.warnings),
            completeness_status=report.completeness_status,
            evidence_status=report.evidence_status,
            project_use_status=report.project_use_status,
        )
        write_report_manifest_json(manifest, manifest_path)
        output_files["manifest"] = str(manifest_path)
    return output_files


def _handle_generate_dataset(args: Namespace) -> int:
    cases = generate_dataset_cases(
        limit=args.limit,
        load_duration=args.load_duration,
        shuffle=not args.no_shuffle,
        seed=args.seed,
    )
    dataset_context = {
        "load_duration": args.load_duration,
        "local_axes_id": cases[0].local_axes_id if cases else None,
        "moment_axis": cases[0].moment_axis if cases else None,
        "tension_face": cases[0].tension_face if cases else None,
        "completeness_status": "incomplete",
        "evidence_status": "needs_engineer_review",
        "project_use_status": "prohibited",
        "project_use": False,
    }
    if args.split:
        split = split_dataset_cases(
            cases,
            seed=args.seed,
            group_by="group_key" if args.group_split else None,
        )
        output_paths = export_dataset_split_csv(
            split,
            Path(args.output_dir),
            prefix=args.prefix,
        )
        report = build_dataset_report(cases, split)
        default_report_path = Path(args.output_dir) / f"{args.prefix}_report.json"
        report_path = export_dataset_report_json(
            report,
            Path(args.report) if args.report else default_report_path,
        )
        payload = {
            "command": "generate-dataset",
            "rows": len(cases),
            "train_rows": len(split.train),
            "validation_rows": len(split.validation),
            "test_rows": len(split.test),
            "output_files": {name: str(path) for name, path in output_paths.items()},
            "report_path": str(report_path),
            "dataset_version": DATASET_VERSION,
            **dataset_context,
            "unique_group_count": report["unique_group_count"],
            "geometry_stirrup_mismatch_count": report["geometry_stirrup_mismatch_count"],
            "unsafe_rows_count": report["unsafe_rows_count"],
        }
        if args.json:
            print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        print("Dataset generation")
        print(f"rows: {payload['rows']}")
        print(f"train_rows: {payload['train_rows']}")
        print(f"validation_rows: {payload['validation_rows']}")
        print(f"test_rows: {payload['test_rows']}")
        for split_name, path in output_paths.items():
            print(f"{split_name}: {path}")
        print(f"report: {report_path}")
        print(f"unique_group_count: {payload['unique_group_count']}")
        print(
            "geometry_stirrup_mismatch_count: "
            f"{payload['geometry_stirrup_mismatch_count']}"
        )
        print(f"unsafe_rows_count: {payload['unsafe_rows_count']}")
        print(f"dataset_version: {DATASET_VERSION}")
        print(f"load_duration: {dataset_context['load_duration']}")
        print(f"local_axes_id: {dataset_context['local_axes_id']}")
        print(f"moment_axis: {dataset_context['moment_axis']}")
        print(f"tension_face: {dataset_context['tension_face']}")
        print(f"completeness_status: {dataset_context['completeness_status']}")
        print(f"evidence_status: {dataset_context['evidence_status']}")
        print(f"project_use_status: {dataset_context['project_use_status']}")
        print("project_use: false")
        return 0

    if args.output is None:
        raise ValueError("--output is required unless --split is used")

    output_path = export_dataset_csv(cases, Path(args.output))
    if args.json:
        print(
            jsonlib.dumps(
                {
                    "command": "generate-dataset",
                    "output": str(output_path),
                    "rows": len(cases),
                    "dataset_version": DATASET_VERSION,
                    **dataset_context,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    print("Dataset generation")
    print(f"output: {output_path}")
    print(f"rows: {len(cases)}")
    print(f"dataset_version: {DATASET_VERSION}")
    print(f"load_duration: {dataset_context['load_duration']}")
    print(f"local_axes_id: {dataset_context['local_axes_id']}")
    print(f"moment_axis: {dataset_context['moment_axis']}")
    print(f"tension_face: {dataset_context['tension_face']}")
    print(f"completeness_status: {dataset_context['completeness_status']}")
    print(f"evidence_status: {dataset_context['evidence_status']}")
    print(f"project_use_status: {dataset_context['project_use_status']}")
    print("project_use: false")
    return 0


def _handle_validate(args: Namespace) -> int:
    golden_results = []
    if args.golden:
        golden_results = [
            *run_bending_golden_cases(),
            *run_step3_bending_benchmark_cases(),
            *run_shear_golden_cases(),
            *run_crack_formation_golden_cases(),
            *run_crack_width_golden_cases(),
            *run_deflection_golden_cases(),
            *run_design_golden_cases(),
        ]

    dataset_result = None
    if args.generate_dataset_limit is not None:
        cases = generate_dataset_cases(
            limit=args.generate_dataset_limit,
            load_duration="short",
        )
        split = split_dataset_cases(cases, group_by="group_key")
        dataset_result = validate_dataset_cases(cases, split)
    elif args.dataset is not None:
        cases = _load_dataset_csv(Path(args.dataset))
        dataset_result = validate_dataset_cases(cases)

    external_input_path = None
    external_rows = ()
    if args.external_input is not None:
        external_input_path = Path(args.external_input)
        external_rows = load_external_comparison_csv(external_input_path)
        external_rows = tuple(compute_external_deltas(row) for row in external_rows)

    external_with_deltas_path = None
    if args.external_with_deltas is not None:
        if args.external_input is None:
            raise ValueError("--external-with-deltas requires --external-input")
        external_with_deltas_path = export_external_comparison_with_deltas_csv(
            external_rows,
            Path(args.external_with_deltas),
        )

    external_template_path = None
    if args.external_template is not None:
        external_cases = generate_dataset_cases(limit=10, load_duration="short")
        template_rows = build_external_comparison_rows(external_cases, limit=10)
        external_template_path = export_external_comparison_csv(
            template_rows,
            Path(args.external_template),
        )

    acceptance_report = None
    acceptance_report_path = None
    if args.acceptance_report is not None:
        acceptance_golden_results = [
            *run_bending_golden_cases(),
            *run_step3_bending_benchmark_cases(),
            *run_shear_golden_cases(),
            *run_crack_formation_golden_cases(),
            *run_crack_width_golden_cases(),
            *run_deflection_golden_cases(),
            *run_design_golden_cases(),
        ]
        acceptance_cases = generate_dataset_cases(
            limit=args.generate_dataset_limit or 100,
            load_duration="short",
        )
        acceptance_split = split_dataset_cases(acceptance_cases, group_by="group_key")
        acceptance_dataset_result = validate_dataset_cases(
            acceptance_cases,
            acceptance_split,
        )
        acceptance_report = evaluate_acceptance_gates(
            golden_results=acceptance_golden_results,
            dataset_validation=acceptance_dataset_result,
            external_rows=external_rows,
            max_delta_percent=args.max_delta_percent,
            required_external_source=args.required_external_source,
            require_engineer_accepted=not args.no_require_engineer_accepted,
        )
        acceptance_report_path = export_acceptance_report_json(
            acceptance_report,
            Path(args.acceptance_report),
        )

    golden_passed = all(result.passed for result in golden_results)
    dataset_passed = dataset_result is None or dataset_result.status == "pass"
    acceptance_passed = (
        acceptance_report is None or acceptance_report["status"] in ("pass", "warning")
    )
    validation_executed = (
        bool(golden_results)
        or dataset_result is not None
        or acceptance_report is not None
    )
    status = (
        "pass"
        if validation_executed and golden_passed and dataset_passed and acceptance_passed
        else "fail"
    )
    payload: dict[str, Any] = {
        "command": "validate",
        "status": status,
        "status_scope": "diagnostic_regression",
        "completeness_status": "incomplete",
        "evidence_status": "needs_engineer_review",
        "project_use_status": "prohibited",
        "project_use": False,
        "requires_engineer_review": True,
        "golden": [asdict(result) for result in golden_results],
        "dataset": None if dataset_result is None else asdict(dataset_result),
        "external_template": (
            None if external_template_path is None else str(external_template_path)
        ),
        "external_input": None if external_input_path is None else str(external_input_path),
        "external_with_deltas": (
            None if external_with_deltas_path is None else str(external_with_deltas_path)
        ),
        "acceptance": acceptance_report,
        "acceptance_report": (
            None if acceptance_report_path is None else str(acceptance_report_path)
        ),
    }

    if args.output_report is not None:
        report_path = Path(args.output_report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            jsonlib.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        payload["output_report"] = str(report_path)

    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if status == "fail" else 0

    print("Validation")
    print(f"status: {status}")
    print("status_scope: diagnostic_regression")
    print("completeness_status: incomplete")
    print("evidence_status: needs_engineer_review")
    print("project_use_status: prohibited")
    print("project_use: false")
    print("requires_engineer_review: true")
    if golden_results:
        passed_count = sum(1 for result in golden_results if result.passed)
        print(f"golden: {passed_count}/{len(golden_results)} passed")
        for result in golden_results:
            expected_status = result.expected.get("calculation_status", "not_available")
            actual_status = result.actual.get("calculation_status", "not_available")
            print(
                f"{result.case_id}: regression_match={result.status}; "
                f"expected_calculation_status={expected_status}; "
                f"actual_calculation_status={actual_status}"
            )
    if dataset_result is not None:
        print(f"dataset: {dataset_result.status}")
        print(f"total_rows: {dataset_result.total_rows}")
        print(f"unsafe_rows_count: {dataset_result.unsafe_rows_count}")
        print(f"group_leakage_count: {dataset_result.group_leakage_count}")
    if external_template_path is not None:
        print(f"external_template: {external_template_path}")
    if external_input_path is not None:
        print(f"external_input: {external_input_path}")
    if external_with_deltas_path is not None:
        print(f"external_with_deltas: {external_with_deltas_path}")
    if acceptance_report is not None:
        print(f"acceptance: {acceptance_report['status']}")
        print(f"completed_external_rows: {acceptance_report['completed_external_rows']}")
        print(f"external_incomplete_count: {acceptance_report['external_incomplete_count']}")
        print(f"external_rejected_count: {acceptance_report['external_rejected_count']}")
        print(
            "external_delta_exceeded_count: "
            f"{acceptance_report['external_delta_exceeded_count']}"
        )
        print(f"acceptance_report: {acceptance_report_path}")
    if args.output_report is not None:
        print(f"output_report: {payload['output_report']}")
    return 1 if status == "fail" else 0


def _handle_materials_audit(args: Namespace) -> int:
    if args.verification_template and args.verification_csv is None:
        template_path = _material_verification_template_path()
        payload = {
            "command": "materials-audit",
            "status": "verification_template",
            "verification_template_path": str(template_path),
            "columns": list(MATERIAL_VERIFICATION_REQUIRED_COLUMNS),
            "warnings": [
                "engineer_verified requires engineer_name, review_date, source_note, "
                "and evidence_kind=independent_engineer_evidence"
            ],
        }
        if args.json:
            print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        print("Material verification template")
        print(f"verification_template_path: {template_path}")
        _print_warnings(tuple(payload["warnings"]))
        return 0

    if args.verification_csv is not None:
        csv_path = Path(args.verification_csv)
        csv_rows = _load_material_verification_csv(csv_path)
        report = build_material_verification_report(csv_rows)
        payload = {
            "command": "materials-audit",
            "status": report.status,
            "mode": "material-verification",
            "verification_csv": str(csv_path),
            "summary": {
                key: value
                for key, value in asdict(report).items()
                if key != "rows"
            },
            "rows": [asdict(row) for row in report.rows],
            "warnings": list(report.warnings),
        }
        if args.json:
            print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        print("Materials audit verification")
        print(f"status: {report.status}")
        print(f"verification_csv: {csv_path}")
        print(f"total_rows: {report.total_rows}")
        print(f"engineer_verified_count: {report.engineer_verified_count}")
        print(f"draft_count: {report.draft_count}")
        print(f"needs_review_count: {report.needs_review_count}")
        print(f"invalid_rows_count: {report.invalid_rows_count}")
        _print_warnings(report.warnings)
        return 0

    rows = build_material_audit_rows()
    warnings = (
        "material catalog values are draft and require engineer review against SP 63 tables",
    )
    payload = {
        "command": "materials-audit",
        "status": "review_required",
        "rows": [asdict(row) for row in rows],
        "warnings": list(warnings),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Materials audit")
    print("status: review_required")
    for row in rows:
        print(
            f"{row.material_type} {row.class_name} {row.property_name}: "
            f"{row.value:g} {row.unit}; usage={row.usage}; "
            f"audit_status={row.audit_status}; "
            f"requires_engineer_review={row.requires_engineer_review}"
        )
    _print_warnings(warnings)
    return 0


def _handle_material_verification(args: Namespace) -> int:
    template_path = _material_verification_template_path()
    markdown_template_path = _material_verification_markdown_template_path()

    if args.template and args.csv is None and not args.markdown_template:
        payload = {
            "command": "material-verification",
            "status": "template",
            "template_path": str(template_path),
            "columns": list(MATERIAL_VERIFICATION_REQUIRED_COLUMNS),
            "warnings": [
                "engineer_verified requires engineer_name, review_date, source_note, "
                "and evidence_kind=independent_engineer_evidence"
            ],
        }
        if args.json:
            print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        print("Material verification template")
        print(f"template_path: {template_path}")
        _print_warnings(tuple(payload["warnings"]))
        return 0

    if args.markdown_template and args.csv is None:
        payload = {
            "command": "material-verification",
            "status": "template",
            "markdown_template_path": str(markdown_template_path),
            "warnings": [
                "markdown template is a checklist only and does not approve catalog values"
            ],
        }
        if args.json:
            print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        print("Material verification Markdown template")
        print(f"markdown_template_path: {markdown_template_path}")
        _print_warnings(tuple(payload["warnings"]))
        return 0

    csv_rows = None if args.csv is None else _load_material_verification_csv(Path(args.csv))
    report = build_material_verification_report(csv_rows)
    payload = {
        "command": "material-verification",
        "status": report.status,
        "template_path": str(template_path),
        "markdown_template_path": str(markdown_template_path),
        "csv": None if args.csv is None else str(Path(args.csv)),
        "summary": {
            key: value
            for key, value in asdict(report).items()
            if key != "rows"
        },
        "rows": [asdict(row) for row in report.rows],
        "warnings": list(report.warnings),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Material verification")
    print(f"status: {report.status}")
    print(f"total_rows: {report.total_rows}")
    print(f"engineer_verified_count: {report.engineer_verified_count}")
    print(f"draft_count: {report.draft_count}")
    print(f"needs_review_count: {report.needs_review_count}")
    print(f"missing_required_rows_count: {report.missing_required_rows_count}")
    print(f"invalid_rows_count: {report.invalid_rows_count}")
    print(f"value_mismatch_count: {report.value_mismatch_count}")
    for row in report.rows:
        print(
            f"{row.material_type} {row.class_name} {row.property_name}: "
            f"{row.catalog_value:g} {row.unit}; "
            f"verification_status={row.verification_status}; "
            f"evidence_kind={row.evidence_kind}; "
            f"requires_engineer_review={row.requires_engineer_review}"
        )
    _print_warnings(report.warnings)
    return 0


def _handle_material_verification_report(args: Namespace) -> int:
    csv_path = Path(args.csv)
    csv_rows = _load_material_verification_csv(csv_path)
    document = build_material_verification_report_document(csv_rows)
    output_path = None if args.output is None else Path(args.output)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(document.markdown, encoding="utf-8")

    payload = {
        "command": "material-verification-report",
        "status": document.status,
        "csv": str(csv_path),
        "output": None if output_path is None else str(output_path),
        "summary": {
            "total_rows": document.total_rows,
            "engineer_verified_count": document.engineer_verified_count,
            "needs_review_count": document.needs_review_count,
            "draft_count": document.draft_count,
            "missing_required_fields_count": document.missing_required_fields_count,
            "missing_required_rows_count": document.missing_required_rows_count,
            "value_mismatch_count": document.value_mismatch_count,
            "status_counts": document.status_counts,
            "requires_engineer_review": document.requires_engineer_review,
        },
        "needs_review_rows": [asdict(row) for row in document.needs_review_rows],
        "warnings": list(document.warnings),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(document.markdown, end="")
    if output_path is not None:
        print(f"\nreport_output: {output_path}")
    return 0


def _handle_material_verification_closure(args: Namespace) -> int:
    csv_path = (
        None
        if args.material_verification_csv is None
        else Path(args.material_verification_csv)
    )
    output_dir = None
    if not args.no_output_files and args.output_dir is not None:
        output_dir = Path(args.output_dir)
    result = build_material_verification_closure(
        material_verification_csv=csv_path,
        output_dir=output_dir,
    )
    payload = {
        "command": "material-verification-closure",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(render_material_verification_closure_markdown(result), end="")
        return 0

    print("Material verification closure")
    print(f"status: {result.status}")
    print(f"closure_status: {result.closure_status}")
    print(f"material_verification_csv: {result.material_verification_csv}")
    print(f"coverage_ratio: {result.coverage_ratio:.6g}")
    print(
        "material_ready_for_engineering_review: "
        f"{result.material_ready_for_engineering_review}"
    )
    print(f"material_ready_for_project_use: {result.material_ready_for_project_use}")
    print(f"missing_material_keys: {len(result.missing_material_keys)}")
    print(f"rejected_material_keys: {len(result.rejected_material_keys)}")
    print(f"review_required_material_keys: {len(result.review_required_material_keys)}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_manual_cases(args: Namespace) -> int:
    results = run_manual_verification_cases()
    passed_count = sum(1 for result in results if result.passed)
    status = "pass" if passed_count == len(results) else "fail"
    payload = {
        "command": "manual-cases",
        "status": status,
        "case_count": len(results),
        "passed_count": passed_count,
        "cases": [asdict(result) for result in results],
        "requires_engineer_review": True,
        "warnings": [
            "manual SP63 verification cases are draft MVP checks and require engineer review"
        ],
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Manual SP63 verification cases")
    print(f"status: {status}")
    print(f"case_count: {len(results)}")
    print(f"passed_count: {passed_count}")
    for result in results:
        print(f"{result.case_id}: {result.status} - {result.title}")
        print(f"  strength_status: {result.actual_statuses.get('strength_status')}")
        print(f"  serviceability_status: {result.actual_statuses.get('serviceability_status')}")
        print(f"  overall_status: {result.actual_statuses.get('overall_status')}")
    _print_warnings(tuple(payload["warnings"]))
    return 0


def _handle_diagnostic_dataset(args: Namespace) -> int:
    cases = generate_diagnostic_dataset_cases(limit=args.limit)
    status_counts = diagnostic_status_counts(cases)
    warnings = diagnostic_dataset_warnings(cases)
    split = split_diagnostic_dataset_by_group(cases)
    unique_group_count = diagnostic_unique_group_count(cases)
    status = "pass" if not warnings else "review_required"
    payload = {
        "command": "diagnostic-dataset",
        "status": status,
        "case_count": len(cases),
        "unique_group_count": unique_group_count,
        "group_key_present": all(case.group_key for case in cases),
        "group_leakage_count": split.group_leakage_count,
        "train_group_count": split.train_group_count,
        "test_group_count": split.test_group_count,
        "status_counts": status_counts,
        "rows": [case.as_row() for case in cases],
        "warnings": list(warnings),
        "requires_engineer_review": True,
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Diagnostic dataset")
    print(f"status: {status}")
    print(f"case_count: {len(cases)}")
    print(f"unique_group_count: {unique_group_count}")
    print(f"group_key_present: {all(case.group_key for case in cases)}")
    print(f"group_leakage_count: {split.group_leakage_count}")
    print(f"overall_status_counts: {status_counts['overall_status']}")
    for case in cases:
        print(f"{case.case_id}: {case.case_type} -> {case.overall_status}")
        if case.failure_reason:
            print(f"  failure_reason: {case.failure_reason}")
    _print_warnings(warnings)
    return 0


def _handle_ml_readiness(args: Namespace) -> int:
    if args.diagnostic:
        cases = generate_diagnostic_dataset_cases(limit=args.generate_dataset_limit)
        rows = (case.as_readiness_row() for case in cases)
        dataset_mode = "diagnostic"
    else:
        cases = generate_dataset_cases(
            limit=args.generate_dataset_limit,
            load_duration="short",
        )
        rows = (case.as_row() for case in cases)
        dataset_mode = "diagnostic_regression_pass_rows"
    report = build_ml_readiness_report(rows)
    payload = {
        "command": "ml-readiness",
        "dataset_mode": dataset_mode,
        **asdict(report),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("ML readiness")
    print(f"status: {report.status}")
    print(f"total_rows: {report.total_rows}")
    print(f"feature_columns_count: {report.feature_columns_count}")
    print(f"target_columns_count: {report.target_columns_count}")
    print(f"unsafe_rows_count: {report.unsafe_rows_count}")
    print(f"group_key_present: {report.group_key_present}")
    print(f"unique_group_count: {report.unique_group_count}")
    print(f"group_leakage_count: {report.group_leakage_count}")
    print(
        "missing_required_columns: "
        f"{', '.join(report.missing_required_columns) if report.missing_required_columns else '-'}"
    )
    print(
        "constant_target_columns: "
        f"{', '.join(report.constant_target_columns) if report.constant_target_columns else '-'}"
    )
    _print_warnings(report.warnings)
    return 0


def _handle_ml_external_readiness(args: Namespace) -> int:
    result = evaluate_ml_external_validation_readiness(
        dataset_path=Path(args.dataset),
        external_validation_csv=(
            None
            if args.external_validation_csv is None
            else Path(args.external_validation_csv)
        ),
        material_verification_csv=(
            None
            if args.material_verification_csv is None
            else Path(args.material_verification_csv)
        ),
    )
    markdown = render_ml_external_readiness_markdown(result)
    output_path = None if args.output is None else Path(args.output)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")

    payload = {
        "command": "ml-external-readiness",
        **asdict(result),
    }
    if output_path is not None:
        payload["output"] = str(output_path)

    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.markdown:
        print(markdown, end="")
        if output_path is not None:
            print(f"\noutput: {output_path}")
        return 0

    print("ML external validation readiness")
    print(f"status: {result.status}")
    print(f"readiness_status: {result.readiness_status}")
    print(f"dataset_path: {result.dataset_path}")
    print(f"row_count: {result.row_count}")
    print(f"synthetic_data_only: {result.synthetic_data_only}")
    print(f"external_validation_present: {result.external_validation_present}")
    print(f"external_case_count: {result.external_case_count}")
    print(f"accepted_external_case_count: {result.accepted_external_case_count}")
    print(f"failed_external_case_count: {result.failed_external_case_count}")
    print(f"external_match_rate: {result.external_match_rate}")
    print(f"material_verification_present: {result.material_verification_present}")
    print(f"ml_ready_for_research: {result.ml_ready_for_research}")
    print(f"ml_ready_for_engineering_review: {result.ml_ready_for_engineering_review}")
    print(f"ml_ready_for_project_use: {result.ml_ready_for_project_use}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    if result.recommendations:
        print("recommendations:")
        for recommendation in result.recommendations:
            print(f"- {recommendation}")
    if output_path is not None:
        print(f"output: {output_path}")
    return 0


def _handle_ml_material_readiness(args: Namespace) -> int:
    result = evaluate_ml_material_verification_readiness(
        dataset_path=Path(args.dataset),
        material_verification_csv=(
            None
            if args.material_verification_csv is None
            else Path(args.material_verification_csv)
        ),
        dataset_format=args.format,
    )
    markdown = render_ml_material_readiness_markdown(result)
    output_path = None if args.output is None else Path(args.output)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")

    payload = {
        "command": "ml-material-readiness",
        **asdict(result),
    }
    if output_path is not None:
        payload["output"] = str(output_path)

    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.markdown:
        print(markdown, end="")
        if output_path is not None:
            print(f"\noutput: {output_path}")
        return 0

    print("ML material verification readiness")
    print(f"status: {result.status}")
    print(f"source_dataset: {result.source_dataset}")
    print(f"row_count: {result.row_count}")
    print(f"material_verification_present: {result.material_verification_present}")
    print(f"material_verification_complete: {result.material_verification_complete}")
    print(f"material_coverage_ratio: {result.material_coverage_ratio:.6g}")
    print(
        "material_ready_for_engineering_review: "
        f"{result.material_ready_for_engineering_review}"
    )
    print(f"material_ready_for_project_use: {result.material_ready_for_project_use}")
    print(
        "required_material_keys: "
        f"{', '.join(result.required_material_keys) if result.required_material_keys else '-'}"
    )
    print(
        "missing_material_keys: "
        f"{', '.join(result.missing_material_keys) if result.missing_material_keys else '-'}"
    )
    print(
        "rejected_material_keys: "
        f"{', '.join(result.rejected_material_keys) if result.rejected_material_keys else '-'}"
    )
    print(
        "review_required_material_keys: "
        + (
            ", ".join(result.review_required_material_keys)
            if result.review_required_material_keys
            else "-"
        )
    )
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    if output_path is not None:
        print(f"output: {output_path}")
    return 0


def _handle_engineering_ml_readiness(args: Namespace) -> int:
    output_dir = None if args.no_output_files or args.output_dir is None else Path(args.output_dir)
    result = build_engineering_ml_readiness_bundle(
        dataset_path=Path(args.dataset),
        output_dir=output_dir,
        dataset_format=args.format,
        external_validation_csv=(
            None
            if args.external_validation_csv is None
            else Path(args.external_validation_csv)
        ),
        material_verification_csv=(
            None
            if args.material_verification_csv is None
            else Path(args.material_verification_csv)
        ),
        benchmark_report_path=(
            None if args.benchmark_report is None else Path(args.benchmark_report)
        ),
        benchmark_trend_report_path=(
            None
            if args.benchmark_trend_report is None
            else Path(args.benchmark_trend_report)
        ),
        model_comparison_report_path=(
            None
            if args.model_comparison_report is None
            else Path(args.model_comparison_report)
        ),
        ml_proposal_package_json=(
            None
            if args.ml_proposal_package_json is None
            else Path(args.ml_proposal_package_json)
        ),
    )
    payload = {
        "command": "engineering-ml-readiness",
        **asdict(result),
    }

    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(result.markdown, end="")
        return 0
    if args.csv:
        print(render_readiness_matrix_csv(result.readiness_matrix), end="")
        return 0

    print("Engineering ML readiness bundle")
    print(f"status: {result.status}")
    print(f"readiness_status: {result.readiness_status}")
    print(f"dataset_path: {result.dataset_path}")
    print(f"row_count: {result.row_count}")
    print(f"external_validation_present: {result.external_validation_present}")
    print(f"material_verification_present: {result.material_verification_present}")
    print(f"benchmark_evidence_present: {result.benchmark_evidence_present}")
    print(f"proposal_evidence_present: {result.proposal_evidence_present}")
    print(f"ml_ready_for_research: {result.ml_ready_for_research}")
    print(f"ml_ready_for_engineering_review: {result.ml_ready_for_engineering_review}")
    print(f"ml_ready_for_project_use: {result.ml_ready_for_project_use}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    if result.recommendations:
        print("recommendations:")
        for recommendation in result.recommendations:
            print(f"- {recommendation}")
    if result.output_dir is not None:
        print(f"output_dir: {result.output_dir}")
    return 0


def _handle_ml_baseline(args: Namespace) -> int:
    safe_cases = generate_dataset_cases(
        limit=args.safe_limit,
        load_duration="short",
        seed=args.seed,
    )
    diagnostic_cases = generate_diagnostic_dataset_cases(limit=args.diagnostic_limit)
    report = build_baseline_ml_report(
        safe_cases=safe_cases,
        diagnostic_cases=diagnostic_cases,
        seed=args.seed,
    )
    payload = {
        "command": "ml-baseline",
        **asdict(report),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Baseline ML report")
    print(f"status: {report.status}")
    print("ML is advisory-only.")
    print("Neural network is not used.")
    print("Deterministic SP63 checks remain mandatory.")
    print(f"safe_rows: {report.safe_rows}")
    print(f"diagnostic_rows: {report.diagnostic_rows}")
    print(f"regression_targets: {', '.join(report.regression_targets)}")
    print(f"classification_target: {report.classification_target}")
    for target_name, metrics in report.regression_metrics.items():
        print(f"{target_name}:")
        for metric_name, value in metrics.items():
            print(f"  {metric_name}: {value:.6g}")
    print("classification_metrics:")
    for metric_name, value in report.classification_metrics.items():
        print(f"  {metric_name}: {value}")
    print("expanded_diagnostic_classification:")
    print(f"  status: {report.expanded_diagnostic_classification['status']}")
    print(f"  train_rows: {report.expanded_diagnostic_classification['train_rows']}")
    print(f"  test_rows: {report.expanded_diagnostic_classification['test_rows']}")
    for mode_name, mode_report in report.expanded_diagnostic_classification[
        "feature_modes"
    ].items():
        logistic_metrics = mode_report["logistic"]
        print(
            f"  {mode_name}: logistic_accuracy={logistic_metrics['accuracy']:.6g}, "
            f"logistic_macro_f1={logistic_metrics['macro_f1']:.6g}"
        )
    _print_warnings(report.warnings)
    return 0


def _handle_report_ml_baseline(args: Namespace) -> int:
    report = build_report_baseline_ml_result(
        dataset_path=Path(args.dataset),
        dataset_format=args.format,
        target=args.target,
        feature_mode=args.feature_mode,
        random_state=args.random_state,
    )
    payload = {
        "command": "report-ml-baseline",
        **asdict(report),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Report ML baseline")
    print(f"status: {report.status}")
    print("ML is advisory-only.")
    print("Neural network is not used.")
    print("Deterministic SP63 checks remain mandatory.")
    print(f"source_dataset: {report.source_dataset}")
    print(f"row_count: {report.row_count}")
    print(f"feature_mode: {report.feature_mode}")
    print(f"target: {report.target}")
    print(f"model_name: {report.model_name}")
    print(f"train_count: {report.train_count}")
    print(f"validation_count: {report.validation_count}")
    print(f"test_count: {report.test_count}")
    print(f"target_distribution: {report.target_distribution}")
    print(f"feature_columns: {', '.join(report.feature_columns)}")
    print(f"excluded_leakage_columns: {', '.join(report.excluded_leakage_columns)}")
    print("metrics:")
    for metric_name, value in report.metrics.items():
        print(f"  {metric_name}: {value}")
    _print_warnings(report.warnings)
    if report.errors:
        print("errors:")
        for error in report.errors:
            print(f"- {error}")
    return 0


def _handle_report_neural_surrogate(args: Namespace) -> int:
    report = build_report_neural_surrogate_result(
        dataset_path=Path(args.dataset),
        dataset_format=args.format,
        target=args.target,
        feature_mode=args.feature_mode,
        hidden_layer_sizes=(args.hidden_layer_size,),
        max_iter=args.max_iter,
        random_state=args.random_state,
    )
    payload = {
        "command": "report-neural-surrogate",
        **asdict(report),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Report neural surrogate")
    print(f"status: {report.status}")
    print("Neural surrogate is advisory-only and is not a design checker.")
    print("Deterministic SP63 checks remain mandatory.")
    print(f"source_dataset: {report.source_dataset}")
    print(f"row_count: {report.row_count}")
    print(f"feature_mode: {report.feature_mode}")
    print(f"target: {report.target}")
    print(f"model_name: {report.model_name}")
    print(f"neural_network_used: {report.neural_network_used}")
    print(f"train_count: {report.train_count}")
    print(f"validation_count: {report.validation_count}")
    print(f"test_count: {report.test_count}")
    print(f"target_distribution: {report.target_distribution}")
    print(f"feature_columns: {', '.join(report.feature_columns)}")
    print(f"excluded_leakage_columns: {', '.join(report.excluded_leakage_columns)}")
    print("metrics:")
    for metric_name, value in report.metrics.items():
        print(f"  {metric_name}: {value}")
    _print_warnings(report.warnings)
    if report.errors:
        print("errors:")
        for error in report.errors:
            print(f"- {error}")
    return 0


def _handle_report_neural_predict(args: Namespace) -> int:
    result = build_neural_advisory_prediction(
        dataset_path=Path(args.dataset),
        dataset_format=args.format,
        input_json_path=Path(args.input_json),
        target=args.target,
        feature_mode=args.feature_mode,
        hidden_layer_sizes=(args.hidden_layer_size,),
        max_iter=args.max_iter,
        random_state=args.random_state,
    )
    payload = {
        "command": "report-neural-predict",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Report neural advisory prediction")
    print(f"status: {result.status}")
    print("Neural prediction is advisory-only and is not a design checker.")
    print("Deterministic SP63 report verification is mandatory.")
    print(f"source_dataset: {result.source_dataset}")
    print(f"input_json_path: {result.input_json_path}")
    print(f"target: {result.target}")
    print(f"feature_mode: {result.feature_mode}")
    print(f"predicted_status: {result.predicted_status}")
    print(f"prediction_confidence: {result.prediction_confidence}")
    print(f"class_probabilities: {result.class_probabilities}")
    print(f"deterministic_strength_status: {result.deterministic_strength_status}")
    print(
        "deterministic_serviceability_status: "
        f"{result.deterministic_serviceability_status}"
    )
    print(f"deterministic_overall_status: {result.deterministic_overall_status}")
    print(f"prediction_matches_deterministic: {result.prediction_matches_deterministic}")
    print(f"neural_network_used: {result.neural_network_used}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_neural_safety_audit(args: Namespace) -> int:
    result = build_neural_advisory_safety_audit(
        dataset_path=Path(args.dataset),
        dataset_format=args.format,
        input_json_path=Path(args.input_json),
        target=args.target,
        feature_mode=args.feature_mode,
        random_state=args.random_state,
    )
    payload = {
        "command": "neural-safety-audit",
        **result.json_data,
    }
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if args.markdown:
            output_path.write_text(result.markdown, encoding="utf-8")
        else:
            output_path.write_text(
                jsonlib.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(result.markdown)
        return 0

    print("Neural advisory safety audit")
    print(f"status: {result.status}")
    print(f"audit_status: {result.audit_status}")
    print("This audit is advisory-only and is not a design calculation.")
    print("Deterministic SP63 verification and engineer review are mandatory.")
    print(f"source_dataset: {result.source_dataset}")
    print(f"input_json_path: {result.input_json_path}")
    print(f"target: {result.target}")
    print(f"feature_mode: {result.feature_mode}")
    print(f"predicted_status: {result.predicted_status}")
    print(f"prediction_confidence: {result.prediction_confidence}")
    print(f"deterministic_strength_status: {result.deterministic_strength_status}")
    print(
        "deterministic_serviceability_status: "
        f"{result.deterministic_serviceability_status}"
    )
    print(f"deterministic_overall_status: {result.deterministic_overall_status}")
    print(f"prediction_matches_deterministic: {result.prediction_matches_deterministic}")
    print(f"advisory_signal_usable: {result.advisory_signal_usable}")
    print(f"neural_network_used: {result.neural_network_used}")
    if result.rejection_reasons:
        print("rejection_reasons:")
        for reason in result.rejection_reasons:
            print(f"- {reason}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_ml_proposal_package(args: Namespace) -> int:
    result = build_ml_proposal_package(
        dataset_path=Path(args.dataset),
        dataset_format=args.format,
        input_json_path=Path(args.input_json),
        target=args.target,
        feature_mode=args.feature_mode,
        hidden_layer_sizes=(args.hidden_layer_size,),
        max_iter=args.max_iter,
        random_state=args.random_state,
    )
    payload = {
        "command": "ml-proposal-package",
        **result.json_data,
    }
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if args.markdown:
            output_path.write_text(result.markdown, encoding="utf-8")
        else:
            output_path.write_text(
                jsonlib.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.markdown:
        print(result.markdown)
        return 0

    print("ML proposal package")
    print(f"status: {result.status}")
    print(f"proposal_status: {result.proposal_status}")
    print("ML proposal output is advisory-only and is not a design decision.")
    print("Deterministic SP63 verification and engineer review are mandatory.")
    print(f"source_dataset: {result.source_dataset}")
    print(f"input_json_path: {result.input_json_path}")
    print(f"target: {result.target}")
    print(f"feature_mode: {result.feature_mode}")
    print(f"predicted_status: {result.predicted_status}")
    print(f"prediction_confidence: {result.prediction_confidence}")
    print(f"deterministic_strength_status: {result.deterministic_strength_status}")
    print(
        "deterministic_serviceability_status: "
        f"{result.deterministic_serviceability_status}"
    )
    print(f"deterministic_overall_status: {result.deterministic_overall_status}")
    print(f"prediction_matches_deterministic: {result.prediction_matches_deterministic}")
    print(f"advisory_signal_usable: {result.advisory_signal_usable}")
    print(f"safety_audit_status: {result.safety_audit_status}")
    print(f"proposal_accepted: {result.proposal_accepted}")
    print(f"proposal_rejected: {result.proposal_rejected}")
    print(f"proposal_requires_review: {result.proposal_requires_review}")
    print(f"neural_network_used: {result.neural_network_used}")
    if result.rejection_reasons:
        print("rejection_reasons:")
        for reason in result.rejection_reasons:
            print(f"- {reason}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_ml_proposal_review_package(args: Namespace) -> int:
    result = build_ml_proposal_review_package(
        dataset_path=Path(args.dataset),
        input_json_path=Path(args.input_json),
        output_dir=Path(args.output_dir),
        dataset_format=args.format,
        target=args.target,
        feature_mode=args.feature_mode,
        create_zip=not args.no_zip,
        random_state=args.random_state,
        hidden_layer_sizes=(args.hidden_layer_size,),
        max_iter=args.max_iter,
    )
    payload = {
        "command": "ml-proposal-review-package",
        **asdict(result),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("ML proposal engineering review package")
    print(f"status: {result.status}")
    print(f"package_status: {result.package_status}")
    print(f"output_dir: {result.output_dir}")
    print(f"zip_path: {result.zip_path}")
    print(f"proposal_status: {result.proposal_status}")
    print(f"deterministic_overall_status: {result.deterministic_overall_status}")
    print(f"prediction_matches_deterministic: {result.prediction_matches_deterministic}")
    print(f"advisory_signal_usable: {result.advisory_signal_usable}")
    print(f"manifest_path: {result.manifest_path}")
    print(f"readme_path: {result.readme_path}")
    print(f"file_count: {result.file_count}")
    print(f"zip_sha256: {result.zip_sha256}")
    _print_warnings(result.warnings)
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def _handle_neural_surrogate(args: Namespace) -> int:
    report = build_neural_surrogate_report(
        diagnostic_limit=args.diagnostic_limit,
        random_state=args.seed,
    )
    payload = {
        "command": "neural-surrogate",
        **asdict(report),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Neural surrogate smoke report")
    print(f"status: {report.status}")
    print("ML is advisory-only.")
    print("Neural network is a smoke MVP, not a design checker.")
    print("Deterministic SP63 checks remain mandatory.")
    print(f"dataset_name: {report.dataset_name}")
    print(f"total_rows: {report.total_rows}")
    print(f"train_rows: {report.train_rows}")
    print(f"test_rows: {report.test_rows}")
    print(f"group_key_present: {report.group_key_present}")
    print(f"group_leakage_count: {report.group_leakage_count}")
    print(f"classification_target: {report.classification_target}")
    print(
        "classification_accuracy: "
        f"{report.classification_metrics.get('accuracy', 'not_available')}"
    )
    print(
        "classification_macro_f1: "
        f"{report.classification_metrics.get('macro_f1', 'not_available')}"
    )
    for target_name in ("longitudinal_as_mm2", "bending_utilization"):
        if target_name in report.regression_metrics:
            metrics = report.regression_metrics[target_name]
            print(
                f"{target_name}: mae={metrics['mae']:.6g}, "
                f"rmse={metrics['rmse']:.6g}, r2={metrics['r2']:.6g}"
            )
    _print_warnings(report.warnings)
    return 0


def _handle_ml_proposal_verify(args: Namespace) -> int:
    proposals = _ml_proposal_smoke_examples()
    results = tuple(verify_ml_proposal_with_deterministic_core(proposal) for proposal in proposals)
    accepted_count = sum(1 for result in results if result.accepted)
    rejected_count = len(results) - accepted_count
    status = "pass" if accepted_count >= 1 and rejected_count >= 1 else "review_required"
    payload = {
        "command": "ml-proposal-verify",
        "status": status,
        "verified_count": len(results),
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "results": [asdict(result) for result in results],
        "completeness_status": "incomplete",
        "evidence_status": "needs_engineer_review",
        "project_use_status": "prohibited",
        "project_use": False,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "requires_engineer_review": True,
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("ML proposal deterministic verification")
    print(f"status: {status}")
    print(f"verified_count: {len(results)}")
    print(f"accepted_count: {accepted_count}")
    print(f"rejected_count: {rejected_count}")
    print("completeness_status: incomplete")
    print("evidence_status: needs_engineer_review")
    print("project_use_status: prohibited")
    print("project_use: false")
    print("requires_engineer_review: true")
    print("ml_is_advisory_only: true")
    print("accepted means only a narrow deterministic check; project use is prohibited")
    for result in results:
        print(
            f"{result.proposal_id}: {result.verification_status} "
            f"(overall={result.deterministic_overall_status})"
        )
        for reason in result.rejection_reasons:
            print(f"  rejection_reason: {reason}")
    return 0


def _handle_external_validation(args: Namespace) -> int:
    template_path = _external_validation_template_path()

    if args.template and args.csv is None and not args.sample:
        payload = {
            "command": "external-validation",
            "status": "template",
            "template_path": str(template_path),
            "columns": list(EXTERNAL_VALIDATION_COLUMNS),
            "warnings": [EXTERNAL_VALUES_REQUIRED_WARNING],
        }
        if args.json:
            print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        print("External validation template")
        print(f"template_path: {template_path}")
        _print_warnings(tuple(payload["warnings"]))
        return 0

    if args.sample:
        csv_path = _external_validation_sample_path()
    elif args.csv is not None:
        csv_path = Path(args.csv)
    else:
        raise ValueError("--template, --sample, or --csv is required")

    rows = _load_external_validation_csv(csv_path)
    summary = build_external_validation_summary(rows, strict_mode=args.strict)
    payload = {
        "command": "external-validation",
        "status": summary.status,
        "csv": str(csv_path),
        "sample": bool(args.sample),
        "strict": bool(args.strict),
        "template_path": str(template_path),
        "rows_read": summary.total_cases,
        "summary": asdict(summary),
        "warnings": list(summary.warnings),
    }
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if summary.status == "fail" else 0

    print("External validation")
    print(f"status: {summary.status}")
    print(f"csv: {csv_path}")
    print(f"sample: {bool(args.sample)}")
    print(f"strict: {bool(args.strict)}")
    print(f"total_cases: {summary.total_cases}")
    print(f"accepted_cases: {summary.accepted_cases}")
    print(f"review_cases: {summary.review_cases}")
    print(f"failed_cases: {summary.failed_cases}")
    print(f"missing_external_values_count: {summary.missing_external_values_count}")
    _print_warnings(summary.warnings)
    return 1 if summary.status == "fail" else 0


def _ml_proposal_smoke_examples() -> tuple[MLProposal, ...]:
    base_input = {
        "b": 300,
        "h": 500,
        "cover": 32,
        "stirrup_diameter_for_geometry": 8,
        "concrete_class": "B25",
        "longitudinal_rebar_class": "A500",
        "stirrup_rebar_class": "A240",
        "M": 150_000_000,
        "Q": 80_000,
        "local_axes_id": "ml-proposal-smoke-local-axes",
        "moment_axis": "local_z",
        "tension_face": "local_y_min",
        "load_duration": "short",
        "Mser": 30_000_000,
        "span": 6000,
    }
    return (
        MLProposal(
            proposal_id="smoke_pass_proposal",
            proposal_type="rectangular_rebar_scheme",
            input_data=dict(base_input),
            proposed_values={
                "main_bar_count": 3,
                "main_bar_diameter": 20,
                "stirrup_diameter": 8,
                "stirrup_legs": 2,
                "stirrup_spacing": 200,
            },
            model_name="k30_smoke_example",
            model_kind="manual_smoke",
        ),
        MLProposal(
            proposal_id="smoke_fail_proposal",
            proposal_type="rectangular_rebar_scheme",
            input_data=dict(base_input),
            proposed_values={
                "main_bar_count": 2,
                "main_bar_diameter": 12,
                "stirrup_diameter": 6,
                "stirrup_legs": 2,
                "stirrup_spacing": 300,
            },
            model_name="k30_smoke_example",
            model_kind="manual_smoke",
        ),
    )


BASELINE_ML_WARNING = (
    "Baseline ML is experimental and advisory only. "
    "Deterministic SP63 checks remain mandatory."
)


def _handle_train_baseline(args: Namespace) -> int:
    if args.dataset is not None:
        cases = _load_dataset_csv(Path(args.dataset))
        dataset_source = str(Path(args.dataset))
    else:
        cases = generate_dataset_cases(
            limit=args.generate_dataset_limit,
            load_duration="short",
            seed=args.seed,
        )
        dataset_source = "generated"

    split = split_dataset_cases(cases, seed=args.seed, group_by="group_key")
    train_cases = split.train if split.train else cases
    test_cases = split.test or split.validation or train_cases
    bundle = train_baseline_models(train_cases, seed=args.seed)
    metrics = evaluate_baseline_models(bundle, test_cases)
    safety_metrics = evaluate_ml_safety(bundle, test_cases)
    quality_gate = evaluate_ml_quality_gate(
        metrics=metrics,
        safety_metrics=safety_metrics,
    )
    model_path = save_baseline_model_bundle(bundle, Path(args.model_output))

    metrics_path = Path(args.metrics_output)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_payload = {
        "metrics": metrics,
        "safety_metrics": safety_metrics,
        "quality_gate": asdict(quality_gate),
        "dataset_version": bundle.dataset_version,
        "sp63_core_version": bundle.sp63_core_version,
        "requires_deterministic_check": bundle.requires_deterministic_check,
        "completeness_status": "incomplete",
        "evidence_status": "needs_engineer_review",
        "project_use_status": "prohibited",
        "project_use": False,
        "ml_ready_for_project_use": False,
        "requires_engineer_review": True,
    }
    metrics_path.write_text(
        jsonlib.dumps(metrics_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    payload = {
        "command": "train-baseline",
        "status": "pass",
        "warning": BASELINE_ML_WARNING,
        "dataset_source": dataset_source,
        "rows": len(cases),
        "train_rows": len(split.train),
        "validation_rows": len(split.validation),
        "test_rows": len(split.test),
        "model_output": str(model_path),
        "metrics_output": str(metrics_path),
        "metrics": metrics,
        "safety_metrics": safety_metrics,
        "quality_gate": asdict(quality_gate),
        "ml_quality_status": quality_gate.status,
        "ml_quality_warnings": quality_gate.warnings,
        "dataset_version": bundle.dataset_version,
        "completeness_status": "incomplete",
        "evidence_status": "needs_engineer_review",
        "project_use_status": "prohibited",
        "project_use": False,
        "ml_ready_for_project_use": False,
        "requires_engineer_review": True,
    }
    warnings = [BASELINE_ML_WARNING]
    safety_warning = (
        "ML predictions are not accepted unless deterministic safety check passes."
    )
    warnings.append(safety_warning)
    if safety_metrics["unsafe_prediction_rate"] > 0:
        warnings.append(
            "unsafe ML predictions were detected by deterministic safety checks"
        )
    warnings.extend(quality_gate.warnings)
    if quality_gate.status != "pass":
        warnings.append("ML quality gate is not pass; model remains sandbox-only.")
    if quality_gate.status == "fail":
        warnings.append(
            "ML quality gate failed; model must not be used even as advisory output."
        )
    payload["warnings"] = warnings
    if args.json:
        print(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Baseline ML training")
    print(BASELINE_ML_WARNING)
    print(safety_warning)
    print(f"status: {payload['status']}")
    print(f"dataset_source: {dataset_source}")
    print(f"rows: {len(cases)}")
    print(f"train_rows: {len(split.train)}")
    print(f"validation_rows: {len(split.validation)}")
    print(f"test_rows: {len(split.test)}")
    print(f"model_output: {model_path}")
    print(f"metrics_output: {metrics_path}")
    print(f"dataset_version: {bundle.dataset_version}")
    print("completeness_status: incomplete")
    print("evidence_status: needs_engineer_review")
    print("project_use_status: prohibited")
    print("project_use: false")
    print("ml_ready_for_project_use: false")
    print("requires_engineer_review: true")
    for metric_name, value in metrics.items():
        print(f"{metric_name}: {value:.6g}")
    for metric_name, value in safety_metrics.items():
        print(f"{metric_name}: {value:.6g}")
    print(f"ml_quality_status: {quality_gate.status}")
    if quality_gate.warnings:
        print("ml_quality_warnings:")
        for warning in quality_gate.warnings:
            print(f"- {warning}")
    if safety_metrics["unsafe_prediction_rate"] > 0:
        print("warning: unsafe ML predictions were detected by deterministic safety checks")
    if quality_gate.status != "pass":
        print("ML quality gate is not pass; model remains sandbox-only.")
    if quality_gate.status == "fail":
        print("ML quality gate failed; model must not be used even as advisory output.")
    return 0


def _print_json(
    command: str,
    status: str,
    result: Any,
    warnings: tuple[str, ...],
    *,
    safety_statuses: dict[str, Any] | None = None,
) -> None:
    payload = {
        "command": command,
        "status": status,
        "result": result,
        "warnings": list(warnings),
    }
    if safety_statuses is not None:
        payload.update(safety_statuses)
    print(
        jsonlib.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
    )


def _print_warnings(warnings: tuple[str, ...]) -> None:
    if not warnings:
        return
    print("warnings:")
    for warning in warnings:
        print(f"- {warning}")


def _longitudinal_option_to_dict(option: Any) -> dict[str, Any]:
    bending_values = option.bending.intermediate_values
    return {
        "scheme": option.scheme,
        "As": option.As,
        "h0": option.section.effective_depth(),
        "diagnostic_utilization": option.diagnostic_utilization,
        "layout_feasible": option.layout.layout_feasible,
        "constructive_status": option.constructive.status,
        "reinforcement_ratio_percent": option.constructive.intermediate_values[
            "reinforcement_ratio_percent"
        ],
        "local_axes_id": bending_values["local_axes_id"],
        "moment_axis": bending_values["moment_axis"],
        "tension_face": bending_values["tension_face"],
        "load_combination": bending_values["load_combination"],
        "gamma_b1": bending_values["gamma_b1"],
        "completeness_status": option.bending.completeness_status,
        "evidence_status": option.bending.evidence_status,
        "project_use_status": option.bending.project_use_status,
        "project_use": option.bending.project_use,
        "capacity_publication_allowed": option.bending.capacity_publication_allowed,
        "status_scope": option.bending.status_scope,
        "requires_engineer_review": option.requires_engineer_review,
        "diagnostic_status": option.diagnostic_status,
        "status": option.bending.public_status,
    }


def _transverse_option_to_dict(option: Any) -> dict[str, Any]:
    return {
        "scheme": option.scheme,
        "Asw": option.Asw,
        "spacing": option.spacing,
        "legs": option.legs,
        "utilization": option.utilization,
        "steel_consumption": option.steel_consumption,
        "h0": option.section.effective_depth(),
        "geometry_stirrup_diameter": option.section.stirrup_diameter,
        "completeness_status": option.completeness_status,
        "evidence_status": option.evidence_status,
        "project_use_status": option.project_use_status,
        "project_use": option.project_use,
        "requires_engineer_review": option.requires_engineer_review,
        "constructive_status": option.constructive.status,
        "constructive_max_spacing": option.constructive.intermediate_values["max_spacing"],
        "sw_max_by_shear_rule": option.shear.intermediate_values["sw_max_by_shear_rule"],
        "qsw_rule_status": option.shear.intermediate_values["qsw_rule_status"],
        "transverse_reinforcement_countable": option.shear.intermediate_values[
            "transverse_reinforcement_countable"
        ],
        "status": option.status,
    }


def _design_result_to_dict(design: Any) -> dict[str, Any]:
    return {
        "status": design.status,
        "strength_status": design.strength_status,
        "serviceability_status": design.serviceability_status,
        "overall_status": design.overall_status,
        "status_scope": design.status_scope,
        "completeness_status": design.completeness_status,
        "evidence_status": design.evidence_status,
        "project_use_status": design.project_use_status,
        "project_use": design.project_use,
        "requires_engineer_review": design.requires_engineer_review,
        "selected_longitudinal": (
            None
            if design.selected_longitudinal is None
            else _longitudinal_option_to_dict(design.selected_longitudinal)
        ),
        "selected_transverse": (
            None
            if design.selected_transverse is None
            else _transverse_option_to_dict(design.selected_transverse)
        ),
        "crack_formation": (
            None
            if design.crack_formation is None
            else _crack_formation_to_dict(design.crack_formation)
        ),
        "crack_width": (
            None if design.crack_width is None else _crack_width_to_dict(design.crack_width)
        ),
        "deflection": (
            None if design.deflection is None else _deflection_to_dict(design.deflection)
        ),
        "protocol_status": None if design.protocol is None else design.protocol.status,
        "protocol_strength_status": (
            None if design.protocol is None else design.protocol.strength_status
        ),
        "protocol_serviceability_status": (
            None if design.protocol is None else design.protocol.serviceability_status
        ),
        "protocol_overall_status": (
            None if design.protocol is None else design.protocol.overall_status
        ),
    }


def _crack_formation_to_dict(crack: Any) -> dict[str, Any]:
    return {
        "Mser": crack.Mser,
        "Mcrc": crack.Mcrc,
        "utilization": crack.utilization,
        "status": crack.status,
        "W": crack.intermediate_values["W"],
        "Rbtser": crack.intermediate_values["Rbtser"],
        "model_status": crack.model_status,
        "clause_8_1_3_status": crack.clause_8_1_3_status,
        "clause_8_1_3_decision_status": crack.clause_8_1_3_decision_status,
        "usable_for_clause_8_1_3": crack.usable_for_clause_8_1_3,
        "evidence_status": crack.evidence_status,
        "project_use_status": crack.project_use_status,
        "project_use": crack.project_use,
        "warnings": list(crack.warnings),
    }


def _crack_width_to_dict(crack_width: Any) -> dict[str, Any]:
    return {
        "Mser": crack_width.Mser,
        "Mcrc": crack_width.Mcrc,
        "acrc": crack_width.acrc,
        "acrc_limit": crack_width.acrc_limit,
        "utilization": crack_width.utilization,
        "sigma_s": crack_width.sigma_s,
        "epsilon_s": crack_width.epsilon_s,
        "crack_spacing": crack_width.crack_spacing,
        "status": crack_width.status,
        "warnings": list(crack_width.warnings),
    }


def _deflection_to_dict(deflection: Any) -> dict[str, Any]:
    return {
        "Mser": deflection.Mser,
        "Mcrc": deflection.Mcrc,
        "span": deflection.span,
        "curvature": deflection.curvature,
        "deflection": deflection.deflection,
        "deflection_limit": deflection.deflection_limit,
        "utilization": deflection.utilization,
        "I_gross": deflection.I_gross,
        "I_cracked": deflection.I_cracked,
        "I_eff": deflection.I_eff,
        "stiffness_status": deflection.stiffness_status,
        "loading_scheme": deflection.loading_scheme,
        "status": deflection.status,
        "warnings": list(deflection.warnings),
    }


def _external_validation_template_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "validation"
        / "templates"
        / "external_validation_cases_template.csv"
    )


def _external_validation_sample_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "validation"
        / "samples"
        / "external_validation_filled_sample.csv"
    )


def _material_verification_template_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "materials"
        / "templates"
        / "material_catalog_verification_template.csv"
    )


def _material_verification_markdown_template_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "materials"
        / "material_catalog_engineer_verification.md"
    )


def _load_external_validation_csv(path: Path) -> tuple[dict[str, str], ...]:
    return load_external_validation_rows_csv(path)


def _load_material_verification_csv(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("material verification CSV is missing header")
        missing_columns = [
            column
            for column in MATERIAL_VERIFICATION_REQUIRED_COLUMNS
            if column not in reader.fieldnames
        ]
        if missing_columns:
            raise ValueError(
                "material verification CSV is missing columns: " + ", ".join(missing_columns)
            )
        return tuple(dict(row) for row in reader)


def _load_dataset_csv(path: Path) -> tuple[DatasetCase, ...]:
    with path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("dataset CSV is missing header")
        missing_columns = [
            column for column in DATASET_COLUMNS if column not in reader.fieldnames
        ]
        if missing_columns:
            raise ValueError(f"dataset CSV is missing columns: {', '.join(missing_columns)}")
        rows = list(reader)
    cases = []
    for row in rows:
        if row["dataset_version"] != DATASET_VERSION:
            raise ValueError(
                f"unsupported dataset_version {row['dataset_version']!r}; "
                f"expected {DATASET_VERSION!r}"
            )
        if row["load_duration"] != "short":
            raise ValueError(
                "dataset v0.3 rows must use load_duration='short' until the "
                "shear load-combination context is implemented"
            )
        cases.append(
            DatasetCase(
                case_id=row["case_id"],
                group_key=row["group_key"],
                element_type=row["element_type"],
                b=float(row["b"]),
                h=float(row["h"]),
                cover=float(row["cover"]),
                h0=float(row["h0"]),
                geometry_stirrup_diameter=int(row["geometry_stirrup_diameter"]),
                concrete_class=row["concrete_class"],
                rebar_class=row["rebar_class"],
                stirrup_class=row["stirrup_class"],
                local_axes_id=row["local_axes_id"],
                moment_axis=row["moment_axis"],
                tension_face=row["tension_face"],
                load_duration=row["load_duration"],
                M=float(row["M"]),
                Q=float(row["Q"]),
                As_required=float(row["As_required"]),
                As_provided=float(row["As_provided"]),
                main_bar_count=int(row["main_bar_count"]),
                main_bar_diameter=int(row["main_bar_diameter"]),
                main_rebar_scheme=row["main_rebar_scheme"],
                main_rebar_constructive_status=row["main_rebar_constructive_status"],
                main_rebar_ratio_percent=float(row["main_rebar_ratio_percent"]),
                main_rebar_layout_feasible=_parse_bool(row["main_rebar_layout_feasible"]),
                stirrup_scheme=row["stirrup_scheme"],
                stirrup_diameter=int(row["stirrup_diameter"]),
                stirrup_legs=int(row["stirrup_legs"]),
                stirrup_spacing=int(row["stirrup_spacing"]),
                stirrup_Asw=float(row["stirrup_Asw"]),
                stirrup_steel_consumption=float(row["stirrup_steel_consumption"]),
                stirrup_constructive_status=row["stirrup_constructive_status"],
                stirrup_constructive_max_spacing=float(row["stirrup_constructive_max_spacing"]),
                stirrup_sw_max_by_shear_rule=float(row["stirrup_sw_max_by_shear_rule"]),
                stirrup_qsw_rule_status=row["stirrup_qsw_rule_status"],
                stirrup_transverse_reinforcement_countable=_parse_bool(
                    row["stirrup_transverse_reinforcement_countable"]
                ),
                Mult=float(row["Mult"]),
                Qult=float(row["Qult"]),
                bending_utilization=float(row["bending_utilization"]),
                shear_utilization=float(row["shear_utilization"]),
                status=row["status"],
                section_b_mm=float(row["section_b_mm"]),
                section_h_mm=float(row["section_h_mm"]),
                effective_depth_mm=float(row["effective_depth_mm"]),
                cover_mm=float(row["cover_mm"]),
                main_bar_diameter_mm=int(row["main_bar_diameter_mm"]),
                stirrup_diameter_mm=int(row["stirrup_diameter_mm"]),
                stirrup_spacing_mm=int(row["stirrup_spacing_mm"]),
                main_rebar_class=row["main_rebar_class"],
                stirrup_rebar_class=row["stirrup_rebar_class"],
                moment_nmm=float(row["moment_nmm"]),
                shear_n=float(row["shear_n"]),
                moment_service_nmm=float(row["moment_service_nmm"]),
                span_mm=float(row["span_mm"]),
                longitudinal_as_mm2=float(row["longitudinal_as_mm2"]),
                transverse_asw_mm2=float(row["transverse_asw_mm2"]),
                bending_mult_nmm=float(row["bending_mult_nmm"]),
                shear_qult_n=float(row["shear_qult_n"]),
                mcrc_nmm=float(row["mcrc_nmm"]),
                crack_width_mm=float(row["crack_width_mm"]),
                deflection_mm=float(row["deflection_mm"]),
                bending_status=row["bending_status"],
                shear_status=row["shear_status"],
                crack_formation_status=row["crack_formation_status"],
                crack_width_status=row["crack_width_status"],
                deflection_status=row["deflection_status"],
                strength_status=row["strength_status"],
                serviceability_status=row["serviceability_status"],
                overall_status=row["overall_status"],
                completeness_status=row["completeness_status"],
                evidence_status=row["evidence_status"],
                project_use_status=row["project_use_status"],
                project_use=_parse_bool(row["project_use"]),
                warnings_count=int(row["warnings_count"]),
                requires_engineer_review=_parse_bool(row["requires_engineer_review"]),
                unsafe_row=_parse_bool(row["unsafe_row"]),
                status_scope=row["status_scope"],
                dataset_source=row["dataset_source"],
                sp63_core_version=row["sp63_core_version"],
                dataset_version=row["dataset_version"],
            )
        )
    return tuple(cases)


def _parse_bool(value: str) -> bool:
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError(f"cannot parse boolean value {value!r}")
