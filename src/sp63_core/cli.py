"""Command line entry point for the SP 63 MVP scaffold."""

import json
import sys
from argparse import ArgumentParser, Namespace
from dataclasses import asdict
from pathlib import Path
from typing import Any

from sp63_core import __version__
from sp63_core.checks import check_bending_rectangular, check_shear_rectangular
from sp63_core.dataset import export_dataset_csv, export_dataset_splits, generate_dataset_cases
from sp63_core.materials import area_by_diameter, get_concrete, get_rebar
from sp63_core.rebar import select_longitudinal_rebar, select_transverse_rebar
from sp63_core.report import save_protocol_html, save_protocol_json
from sp63_core.sections import RectangularSection
from sp63_core.services import RectangularDesignResult, design_rectangular_element


def build_parser() -> ArgumentParser:
    """Build the CLI argument parser."""
    parser = ArgumentParser(description="Run SP 63 MVP deterministic checks.")
    subparsers = parser.add_subparsers(dest="command")

    demo_parser = subparsers.add_parser("demo", help="run the default MVP demo")
    _add_section_arguments(demo_parser)
    _add_material_arguments(demo_parser)
    _add_bending_arguments(demo_parser)
    demo_parser.set_defaults(handler=_run_demo)

    bending_parser = subparsers.add_parser("bending", help="check rectangular bending")
    _add_section_arguments(bending_parser)
    _add_material_arguments(bending_parser)
    _add_bending_arguments(bending_parser)
    bending_parser.add_argument(
        "--load-duration",
        choices=("short", "long"),
        default="short",
        help="load duration for compression reinforcement resistance",
    )
    bending_parser.add_argument("--json", action="store_true", help="emit JSON only")
    bending_parser.set_defaults(handler=_run_bending)

    shear_parser = subparsers.add_parser("shear", help="check rectangular shear")
    _add_section_arguments(shear_parser)
    shear_parser.add_argument("--concrete", default="B25", help="concrete class")
    shear_parser.add_argument("--stirrup-rebar", default="A240", help="stirrup rebar class")
    shear_parser.add_argument("--q", type=float, default=80_000.0, help="shear force Q, N")
    shear_parser.add_argument("--asw", type=float, default=100.53, help="stirrup area Asw, mm2")
    shear_parser.add_argument("--sw", type=float, default=200.0, help="stirrup spacing, mm")
    shear_parser.add_argument("--json", action="store_true", help="emit JSON only")
    shear_parser.set_defaults(handler=_run_shear)

    longitudinal_parser = subparsers.add_parser(
        "select-longitudinal",
        help="select passing longitudinal reinforcement options",
    )
    _add_selection_section_arguments(longitudinal_parser)
    longitudinal_parser.add_argument("--concrete", default="B25", help="concrete class")
    longitudinal_parser.add_argument("--rebar", default="A500", help="longitudinal rebar class")
    longitudinal_parser.add_argument(
        "--moment",
        type=float,
        default=150_000_000.0,
        help="bending moment M, N*mm",
    )
    longitudinal_parser.add_argument("--max-results", type=int, default=5)
    longitudinal_parser.set_defaults(handler=_run_select_longitudinal)

    transverse_parser = subparsers.add_parser(
        "select-transverse",
        help="select passing transverse reinforcement options",
    )
    _add_section_arguments(transverse_parser)
    transverse_parser.add_argument("--concrete", default="B25", help="concrete class")
    transverse_parser.add_argument("--stirrup-rebar", default="A240", help="stirrup rebar class")
    transverse_parser.add_argument("--q", type=float, default=80_000.0, help="shear force Q, N")
    transverse_parser.add_argument("--max-results", type=int, default=5)
    transverse_parser.set_defaults(handler=_run_select_transverse)

    design_parser = subparsers.add_parser(
        "design",
        help="select reinforcement and build a calculation protocol",
    )
    _add_section_arguments(design_parser)
    design_parser.add_argument("--concrete", default="B25", help="concrete class")
    design_parser.add_argument("--rebar", default="A500", help="longitudinal rebar class")
    design_parser.add_argument("--stirrup-rebar", default="A240", help="stirrup rebar class")
    design_parser.add_argument(
        "--moment",
        type=float,
        default=150_000_000.0,
        help="bending moment M, N*mm",
    )
    design_parser.add_argument("--q", type=float, default=80_000.0, help="shear force Q, N")
    design_parser.add_argument("--json", action="store_true", help="emit JSON only")
    design_parser.add_argument("--report-json", help="save calculation protocol JSON")
    design_parser.add_argument("--report-html", help="save calculation protocol HTML")
    design_parser.set_defaults(handler=_run_design)

    dataset_parser = subparsers.add_parser(
        "generate-dataset",
        help="generate checked MVP dataset CSV",
    )
    dataset_parser.add_argument("--limit", type=int, default=1000)
    dataset_parser.add_argument("--output", help="single output CSV path")
    dataset_parser.add_argument("--output-dir", default="data/generated", help="output directory")
    dataset_parser.add_argument(
        "--split",
        action="store_true",
        help="export train/validation/test CSV",
    )
    dataset_parser.set_defaults(handler=_run_generate_dataset)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the requested CLI command."""
    normalized_argv = _normalize_argv(argv)
    args = build_parser().parse_args(normalized_argv)
    handler = getattr(args, "handler", _run_demo)
    return handler(args)


def _normalize_argv(argv: list[str] | None) -> list[str]:
    raw = list(sys.argv[1:] if argv is None else argv)
    commands = {
        "demo",
        "bending",
        "shear",
        "select-longitudinal",
        "select-transverse",
        "design",
        "generate-dataset",
    }
    if not raw or raw[0] not in commands:
        return ["demo", *raw]
    return raw


def _add_section_arguments(parser: ArgumentParser) -> None:
    parser.add_argument("--b", type=float, default=300.0, help="section width, mm")
    parser.add_argument("--h", type=float, default=500.0, help="section height, mm")
    parser.add_argument("--cover", type=float, default=30.0, help="protective cover, mm")
    parser.add_argument("--stirrup-diameter", type=float, default=8.0, help="stirrup diameter, mm")
    parser.add_argument(
        "--main-bar-diameter",
        type=float,
        default=20.0,
        help="main bar diameter, mm",
    )
    parser.add_argument(
        "--compression-bar-diameter",
        type=float,
        default=None,
        help="compression bar diameter, mm; defaults to main bar diameter for MVP",
    )
    parser.add_argument("--h0-override", type=float, default=None, help="explicit h0, mm")


def _add_selection_section_arguments(parser: ArgumentParser) -> None:
    parser.add_argument("--b", type=float, default=300.0, help="section width, mm")
    parser.add_argument("--h", type=float, default=500.0, help="section height, mm")
    parser.add_argument("--cover", type=float, default=32.0, help="protective cover, mm")
    parser.add_argument("--stirrup-diameter", type=float, default=8.0, help="stirrup diameter, mm")


def _add_material_arguments(parser: ArgumentParser) -> None:
    parser.add_argument("--concrete", default="B25", help="concrete class")
    parser.add_argument("--rebar", default="A500", help="longitudinal reinforcement class")


def _add_bending_arguments(parser: ArgumentParser) -> None:
    parser.add_argument("--as-area", type=float, default=942.48, help="tensile As, mm2")
    parser.add_argument("--as-prime", type=float, default=0.0, help="compression As', mm2")
    parser.add_argument(
        "--moment",
        type=float,
        default=150_000_000.0,
        help="bending moment M, N*mm",
    )


def _make_section(args: Namespace, *, main_bar_diameter: float | None = None) -> RectangularSection:
    return RectangularSection(
        b=args.b,
        h=args.h,
        cover=args.cover,
        stirrup_diameter=args.stirrup_diameter,
        main_bar_diameter=(
            args.main_bar_diameter
            if main_bar_diameter is None and hasattr(args, "main_bar_diameter")
            else main_bar_diameter or 20.0
        ),
        compression_bar_diameter=getattr(args, "compression_bar_diameter", None),
        h0_override=getattr(args, "h0_override", None),
    )


def _run_demo(args: Namespace) -> int:
    section = _make_section(args)
    concrete = get_concrete(args.concrete)
    rebar = get_rebar(args.rebar)
    bending = check_bending_rectangular(
        section=section,
        concrete=concrete,
        rebar=rebar,
        As=args.as_area,
        As_prime=args.as_prime,
        M=args.moment,
    )

    print(f"sp63-core {__version__}")
    print("MVP status: deterministic geometry, materials, bending, shear, selection, design.")
    print()
    print(f"Concrete {concrete.class_name}: Rb={concrete.Rb:g} MPa, Rbt={concrete.Rbt:g} MPa")
    print(f"Rebar {rebar.class_name}: Rs={rebar.Rs:g} MPa, Rsc={rebar.Rsc:g} MPa")
    print(f"Section: b={section.b:g} mm, h={section.h:g} mm")
    print(f"Gross area: {section.gross_area():.2f} mm2")
    print(f"Effective depth h0: {section.effective_depth():.2f} mm")
    print(f"Compression rebar depth a_prime: {section.compression_rebar_depth():.2f} mm")
    main_bar_area = area_by_diameter(section.main_bar_diameter)
    print(f"D{section.main_bar_diameter:g} bar area: {main_bar_area:.2f} mm2")
    print()
    _print_bending_result(bending)
    return 0


def _run_bending(args: Namespace) -> int:
    section = _make_section(args)
    result = check_bending_rectangular(
        section=section,
        concrete=get_concrete(args.concrete),
        rebar=get_rebar(args.rebar),
        As=args.as_area,
        As_prime=args.as_prime,
        M=args.moment,
        load_duration=args.load_duration,
    )
    if args.json:
        _print_json(asdict(result))
    else:
        _print_bending_result(result)
    return 0


def _run_shear(args: Namespace) -> int:
    section = _make_section(args)
    result = check_shear_rectangular(
        section=section,
        concrete=get_concrete(args.concrete),
        stirrup_rebar=get_rebar(args.stirrup_rebar),
        Q=args.q,
        Asw=args.asw,
        sw=args.sw,
    )
    if args.json:
        _print_json(asdict(result))
    else:
        _print_shear_result(result)
    return 0


def _run_select_longitudinal(args: Namespace) -> int:
    options = select_longitudinal_rebar(
        section=_make_section(args),
        concrete=get_concrete(args.concrete),
        rebar=get_rebar(args.rebar),
        M=args.moment,
        max_results=args.max_results,
    )
    for option in options:
        print(
            "scheme: "
            f"{option.scheme}, As: {option.As:.2f}, "
            f"h0: {option.section.effective_depth():.2f}, "
            f"utilization: {option.utilization:.3f}, status: {option.status}"
        )
    return 0


def _run_select_transverse(args: Namespace) -> int:
    options = select_transverse_rebar(
        section=_make_section(args),
        concrete=get_concrete(args.concrete),
        stirrup_rebar=get_rebar(args.stirrup_rebar),
        Q=args.q,
        max_results=args.max_results,
    )
    for option in options:
        print(
            "scheme: "
            f"{option.scheme}, Asw: {option.Asw:.2f}, "
            f"spacing: {option.spacing:.2f}, "
            f"steel_per_meter: {option.steel_per_meter:.2f}, "
            f"utilization: {option.utilization:.3f}, status: {option.status}"
        )
    return 0


def _run_design(args: Namespace) -> int:
    result = design_rectangular_element(
        section=_make_section(args),
        concrete=get_concrete(args.concrete),
        longitudinal_rebar=get_rebar(args.rebar),
        transverse_rebar=get_rebar(args.stirrup_rebar),
        M=args.moment,
        Q=args.q,
    )
    saved_reports = _save_design_reports(result, args)
    if args.json:
        _print_json(_design_result_to_dict(result))
    else:
        _print_design_result(result)
        for label, path in saved_reports.items():
            print(f"{label}: {path}")
    return 0


def _run_generate_dataset(args: Namespace) -> int:
    cases = generate_dataset_cases(limit=args.limit)
    print(f"generated rows: {len(cases)}")
    if args.split:
        paths = export_dataset_splits(cases, Path(args.output_dir))
        for split_name, path in paths.items():
            print(f"{split_name}: {path}")
    else:
        output_path = Path(args.output) if args.output else Path(args.output_dir) / "dataset.csv"
        print(f"output: {export_dataset_csv(cases, output_path)}")
    return 0


def _print_bending_result(result: Any) -> None:
    print("Bending check")
    print(f"x: {result.x:.2f}")
    print(f"xi: {result.xi:.3f}")
    print(f"xi_R: {result.xi_R:.3f}")
    print(f"Mult: {result.Mult:.2f}")
    print(f"utilization: {result.utilization:.3f}")
    print(f"status: {result.status}")
    _print_warnings(result.warnings)


def _print_shear_result(result: Any) -> None:
    print("Shear check")
    print(f"Q_strip: {result.Q_strip:.2f}")
    print(f"Qb: {result.Qb:.2f}")
    print(f"Qsw: {result.Qsw:.2f}")
    print(f"Qult: {result.Qult:.2f}")
    print(f"utilization: {result.utilization:.3f}")
    print(f"status: {result.status}")
    _print_warnings(result.warnings)


def _print_design_result(result: RectangularDesignResult) -> None:
    print("Rectangular design")
    if result.selected_longitudinal is None:
        print("selected longitudinal reinforcement: none")
    else:
        print(f"selected longitudinal reinforcement: {result.selected_longitudinal.scheme}")
    if result.selected_transverse is None:
        print("selected transverse reinforcement: none")
    else:
        print(f"selected transverse reinforcement: {result.selected_transverse.scheme}")
    if result.selected_longitudinal is not None:
        print(f"bending utilization: {result.selected_longitudinal.utilization:.3f}")
    if result.selected_transverse is not None:
        print(f"shear utilization: {result.selected_transverse.utilization:.3f}")
    print(f"overall status: {result.status}")
    _print_warnings(result.warnings)


def _print_warnings(warnings: tuple[str, ...]) -> None:
    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"- {warning}")


def _save_design_reports(result: RectangularDesignResult, args: Namespace) -> dict[str, Path]:
    report_paths = {
        "report_json": getattr(args, "report_json", None),
        "report_html": getattr(args, "report_html", None),
    }
    requested = {name: path for name, path in report_paths.items() if path}
    if not requested:
        return {}
    if result.protocol is None:
        raise ValueError("design protocol is not available for report export")

    saved: dict[str, Path] = {}
    if requested.get("report_json"):
        saved["report_json"] = save_protocol_json(result.protocol, requested["report_json"])
    if requested.get("report_html"):
        saved["report_html"] = save_protocol_html(result.protocol, requested["report_html"])
    return saved


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _design_result_to_dict(result: RectangularDesignResult) -> dict[str, Any]:
    return {
        "M": result.M,
        "Q": result.Q,
        "status": result.status,
        "warnings": list(result.warnings),
        "selected_longitudinal": (
            None
            if result.selected_longitudinal is None
            else {
                "scheme": result.selected_longitudinal.scheme,
                "As": result.selected_longitudinal.As,
                "h0": result.selected_longitudinal.section.effective_depth(),
                "utilization": result.selected_longitudinal.utilization,
                "status": result.selected_longitudinal.status,
            }
        ),
        "selected_transverse": (
            None
            if result.selected_transverse is None
            else {
                "scheme": result.selected_transverse.scheme,
                "Asw": result.selected_transverse.Asw,
                "spacing": result.selected_transverse.spacing,
                "steel_per_meter": result.selected_transverse.steel_per_meter,
                "utilization": result.selected_transverse.utilization,
                "status": result.selected_transverse.status,
            }
        ),
        "protocol": None if result.protocol is None else result.protocol.as_dict(),
        "requires_engineer_review": result.requires_engineer_review,
    }


if __name__ == "__main__":
    raise SystemExit(main())
