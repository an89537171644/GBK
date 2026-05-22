"""Command line entry point for the SP 63 MVP scaffold."""

import json as jsonlib
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any

from sp63_core.checks import check_bending_rectangular, check_shear_rectangular
from sp63_core.dataset import DATASET_VERSION, export_dataset_csv, generate_dataset_cases
from sp63_core.design import RectangularDesignInput, design_rectangular_element
from sp63_core.materials import get_concrete, get_rebar
from sp63_core.rebar import select_longitudinal_rebar, select_transverse_rebar
from sp63_core.sections import RectangularSection


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
    dataset.add_argument("--output", required=True)
    dataset.add_argument("--load-duration", choices=("short", "long"), default="short")
    dataset.add_argument("--json", action="store_true", help="print JSON output")
    dataset.set_defaults(handler=_handle_generate_dataset)

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
    _print_warnings(design.warnings)
    return 0


def _handle_generate_dataset(args: Namespace) -> int:
    cases = generate_dataset_cases(limit=args.limit, load_duration=args.load_duration)
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
        "protocol_status": None if design.protocol is None else design.protocol.status,
    }
