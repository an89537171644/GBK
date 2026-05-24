"""Command line entry point for the SP 63 MVP scaffold."""

import json as jsonlib
from argparse import ArgumentParser, Namespace
from dataclasses import asdict
from pathlib import Path
from typing import Any

from sp63_core.checks import (
    check_bending_rectangular,
    check_normal_crack_formation_rectangular,
    check_normal_crack_width_rectangular,
    check_shear_rectangular,
)
from sp63_core.dataset import (
    DATASET_COLUMNS,
    DATASET_VERSION,
    DatasetCase,
    build_dataset_report,
    export_dataset_csv,
    export_dataset_report_json,
    export_dataset_split_csv,
    generate_dataset_cases,
    split_dataset_cases,
)
from sp63_core.design import RectangularDesignInput, design_rectangular_element
from sp63_core.materials import get_concrete, get_rebar
from sp63_core.ml import (
    evaluate_baseline_models,
    evaluate_ml_quality_gate,
    evaluate_ml_safety,
    save_baseline_model_bundle,
    train_baseline_models,
)
from sp63_core.rebar import select_longitudinal_rebar, select_transverse_rebar
from sp63_core.sections import RectangularSection
from sp63_core.validation import (
    build_external_comparison_rows,
    compute_external_deltas,
    evaluate_acceptance_gates,
    export_acceptance_report_json,
    export_external_comparison_csv,
    export_external_comparison_with_deltas_csv,
    load_external_comparison_csv,
    run_bending_golden_cases,
    run_crack_formation_golden_cases,
    run_crack_width_golden_cases,
    run_design_golden_cases,
    run_shear_golden_cases,
    validate_dataset_cases,
)


def build_parser() -> ArgumentParser:
    """Build the CLI argument parser."""
    parser = ArgumentParser(description="Run SP 63 MVP calculation scenarios.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bending = subparsers.add_parser("bending", help="check rectangular bending capacity")
    _add_section_arguments(bending)
    _add_material_arguments(bending, include_rebar=True)
    bending.add_argument("--as-area", type=float, required=True, help="tensile area As, mm2")
    bending.add_argument("--as-prime", type=float, default=0.0, help="compression area As', mm2")
    bending.add_argument("--moment", type=float, required=True, help="bending moment, N*mm")
    bending.add_argument("--load-duration", choices=("short", "long"), default="short")
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

    longitudinal = subparsers.add_parser(
        "select-longitudinal", help="select longitudinal reinforcement"
    )
    _add_section_arguments(longitudinal)
    _add_material_arguments(longitudinal, include_rebar=True)
    longitudinal.add_argument("--moment", type=float, required=True, help="bending moment, N*mm")
    longitudinal.add_argument("--load-duration", choices=("short", "long"), default="short")
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

    dataset = subparsers.add_parser("generate-dataset", help="generate deterministic dataset rows")
    dataset.add_argument("--limit", type=int, required=True)
    dataset.add_argument("--output")
    dataset.add_argument("--split", action="store_true", help="export train/validation/test split")
    dataset.add_argument("--output-dir", default="data/generated")
    dataset.add_argument("--prefix", default="dataset_v001")
    dataset.add_argument("--report")
    dataset.add_argument("--seed", type=int, default=42)
    dataset.add_argument("--no-shuffle", action="store_true", help="preserve full-grid order")
    dataset.add_argument("--group-split", action="store_true", help="split by dataset group_key")
    dataset.add_argument("--load-duration", choices=("short", "long"), default="short")
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
    parser.add_argument("--cover", type=float, required=True, help="protective cover, mm")
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
    parser.add_argument(
        "--compression-bar-diameter",
        type=float,
        default=None,
        help="compression bar diameter, mm",
    )
    parser.add_argument("--h0-override", type=float, default=None, help="explicit h0, mm")


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
    parser.add_argument("--cover", type=float, required=True, help="protective cover, mm")
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
    parser.add_argument("--moment-ser", type=float, default=None, help="service moment, N*mm")
    parser.add_argument("--check-cracks", action="store_true", help="run Mcrc crack check")
    parser.add_argument("--check-crack-width", action="store_true", help="run acrc crack check")
    parser.add_argument("--acrc-limit", type=float, default=0.3, help="crack width limit, mm")
    parser.add_argument("--load-duration", choices=("short", "long"), default="short")


def _section_from_args(args: Namespace) -> RectangularSection:
    return RectangularSection(
        b=args.b,
        h=args.h,
        cover=args.cover,
        stirrup_diameter=args.stirrup_diameter,
        main_bar_diameter=args.main_bar_diameter,
        compression_bar_diameter=args.compression_bar_diameter,
        h0_override=args.h0_override,
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
        As_prime=args.as_prime,
        M=args.moment,
        load_duration=args.load_duration,
    )
    result = {
        "x": bending.x,
        "xi": bending.xi,
        "xi_R": bending.xi_R,
        "Mult": bending.Mult,
        "utilization": bending.utilization,
    }
    if args.json:
        _print_json("bending", bending.status, result, bending.warnings)
        return 0

    print("Bending check")
    print(f"status: {bending.status}")
    print(f"x: {bending.x:.2f} mm")
    print(f"xi: {bending.xi:.3f}")
    print(f"xi_R: {bending.xi_R:.3f}")
    print(f"Mult: {bending.Mult:.2f} N*mm")
    print(f"utilization: {bending.utilization:.3f}")
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


def _handle_select_longitudinal(args: Namespace) -> int:
    section = _section_from_args(args)
    concrete = get_concrete(args.concrete)
    rebar = get_rebar(args.rebar)
    options = select_longitudinal_rebar(
        section=section,
        concrete=concrete,
        rebar=rebar,
        M=args.moment,
        max_results=args.max_results,
        load_duration=args.load_duration,
    )
    result = [_longitudinal_option_to_dict(option) for option in options]
    status = "pass" if options else "fail"
    warnings = () if options else ("no passing longitudinal reinforcement options",)
    if args.json:
        _print_json("select-longitudinal", status, result, warnings)
        return 0

    print("Longitudinal reinforcement options")
    print(f"status: {status}")
    for option in options:
        reinforcement_ratio = option.constructive.intermediate_values[
            "reinforcement_ratio_percent"
        ]
        print(
            f"{option.scheme}: As={option.As:.2f} mm2, "
            f"h0={option.section.effective_depth():.2f} mm, "
            f"utilization={option.utilization:.3f}, "
            f"constructive={option.constructive.status}, "
            f"reinforcement ratio={reinforcement_ratio:.3f}%, "
            f"layout_feasible={option.layout.layout_feasible}, status={option.status}"
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
    if args.json:
        _print_json("select-transverse", status, result, warnings)
        return 0

    print("Transverse reinforcement options")
    print(f"status: {status}")
    for option in options:
        max_spacing = option.constructive.intermediate_values["max_spacing"]
        sw_max_by_shear_rule = option.shear.intermediate_values["sw_max_by_shear_rule"]
        print(
            f"{option.scheme}: Asw={option.Asw:.2f} mm2, spacing={option.spacing:g} mm, "
            f"legs={option.legs}, utilization={option.utilization:.3f}, "
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
        load_duration=args.load_duration,
        Mser=args.moment_ser,
        check_cracks=args.check_cracks,
        check_crack_width=args.check_crack_width,
        acrc_limit=args.acrc_limit,
    )
    design = design_rectangular_element(design_input)
    result = _design_result_to_dict(design)
    if args.json:
        _print_json("design-rectangular", design.status, result, design.warnings)
        return 0

    print("Rectangular design")
    print(f"status: {design.status}")
    if design.selected_longitudinal is not None:
        longitudinal = design.selected_longitudinal
        print(f"selected longitudinal scheme: {longitudinal.scheme}")
        print(f"As: {longitudinal.As:.2f} mm2")
        print(f"h0: {longitudinal.section.effective_depth():.2f} mm")
        print(f"bending utilization: {longitudinal.utilization:.3f}")
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
    _print_warnings(design.warnings)
    return 0


def _handle_generate_dataset(args: Namespace) -> int:
    cases = generate_dataset_cases(
        limit=args.limit,
        load_duration=args.load_duration,
        shuffle=not args.no_shuffle,
        seed=args.seed,
    )
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
    return 0


def _handle_validate(args: Namespace) -> int:
    golden_results = []
    if args.golden:
        golden_results = [
            *run_bending_golden_cases(),
            *run_shear_golden_cases(),
            *run_crack_formation_golden_cases(),
            *run_crack_width_golden_cases(),
            *run_design_golden_cases(),
        ]

    dataset_result = None
    if args.generate_dataset_limit is not None:
        cases = generate_dataset_cases(limit=args.generate_dataset_limit)
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
        external_cases = generate_dataset_cases(limit=10)
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
            *run_shear_golden_cases(),
            *run_crack_formation_golden_cases(),
            *run_crack_width_golden_cases(),
            *run_design_golden_cases(),
        ]
        acceptance_cases = generate_dataset_cases(
            limit=args.generate_dataset_limit or 100,
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
    status = "pass" if golden_passed and dataset_passed and acceptance_passed else "fail"
    payload: dict[str, Any] = {
        "command": "validate",
        "status": status,
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
        return 0

    print("Validation")
    print(f"status: {status}")
    if golden_results:
        passed_count = sum(1 for result in golden_results if result.passed)
        print(f"golden: {passed_count}/{len(golden_results)} passed")
        for result in golden_results:
            print(f"{result.case_id}: {result.status}")
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
    return 0


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


def _print_json(command: str, status: str, result: Any, warnings: tuple[str, ...]) -> None:
    print(
        jsonlib.dumps(
            {
                "command": command,
                "status": status,
                "result": result,
                "warnings": list(warnings),
            },
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
    return {
        "scheme": option.scheme,
        "As": option.As,
        "h0": option.section.effective_depth(),
        "utilization": option.utilization,
        "layout_feasible": option.layout.layout_feasible,
        "constructive_status": option.constructive.status,
        "reinforcement_ratio_percent": option.constructive.intermediate_values[
            "reinforcement_ratio_percent"
        ],
        "status": option.status,
    }


def _transverse_option_to_dict(option: Any) -> dict[str, Any]:
    return {
        "scheme": option.scheme,
        "Asw": option.Asw,
        "spacing": option.spacing,
        "legs": option.legs,
        "utilization": option.utilization,
        "steel_consumption": option.steel_consumption,
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
        "protocol_status": None if design.protocol is None else design.protocol.status,
    }


def _crack_formation_to_dict(crack: Any) -> dict[str, Any]:
    return {
        "Mser": crack.Mser,
        "Mcrc": crack.Mcrc,
        "utilization": crack.utilization,
        "status": crack.status,
        "W": crack.intermediate_values["W"],
        "Rbtser": crack.intermediate_values["Rbtser"],
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


def _load_dataset_csv(path: Path) -> tuple[DatasetCase, ...]:
    import csv

    with path.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))
    cases = []
    for row in rows:
        missing_columns = [column for column in DATASET_COLUMNS if column not in row]
        if missing_columns:
            raise ValueError(f"dataset CSV is missing columns: {', '.join(missing_columns)}")
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
