"""Command line entry point for the SP 63 MVP scaffold."""

from argparse import ArgumentParser

from sp63_core import __version__
from sp63_core.checks import check_bending_rectangular
from sp63_core.materials import area_by_diameter, get_concrete, get_rebar
from sp63_core.sections import RectangularSection


def build_parser() -> ArgumentParser:
    """Build the CLI argument parser."""
    parser = ArgumentParser(description="Run the SP 63 MVP scaffold demo.")
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
    parser.add_argument(
        "--h0-override",
        type=float,
        default=None,
        help="explicit effective depth, mm",
    )
    parser.add_argument("--concrete", default="B25", help="concrete class")
    parser.add_argument("--rebar", default="A500", help="longitudinal reinforcement class")
    parser.add_argument(
        "--as-area",
        type=float,
        default=942.48,
        help="tensile reinforcement area, mm2",
    )
    parser.add_argument(
        "--as-prime",
        type=float,
        default=0.0,
        help="compression reinforcement area, mm2",
    )
    parser.add_argument("--moment", type=float, default=150_000_000.0, help="bending moment, N*mm")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run a small deterministic demo for the currently implemented MVP core."""
    args = build_parser().parse_args(argv)
    section = RectangularSection(
        b=args.b,
        h=args.h,
        cover=args.cover,
        stirrup_diameter=args.stirrup_diameter,
        main_bar_diameter=args.main_bar_diameter,
        compression_bar_diameter=args.compression_bar_diameter,
        h0_override=args.h0_override,
    )
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
    print("MVP status: geometry, units, draft material catalogs, and bending check are available.")
    print("Calculation checks: bending is implemented; shear awaits a separate command.")
    print()
    print(f"Concrete {concrete.class_name}: Rb={concrete.Rb:g} MPa, Rbt={concrete.Rbt:g} MPa")
    print(f"Rebar {rebar.class_name}: Rs={rebar.Rs:g} MPa, Rsc={rebar.Rsc:g} MPa")
    print(f"Section: b={section.b:g} mm, h={section.h:g} mm")
    print(f"Gross area: {section.gross_area():.2f} mm2")
    print(f"Effective depth h0: {section.effective_depth():.2f} mm")
    print(f"Compression rebar depth a_prime: {section.compression_rebar_depth():.2f} mm")
    main_bar_area = area_by_diameter(args.main_bar_diameter)
    print(f"D{args.main_bar_diameter:g} bar area: {main_bar_area:.2f} mm2")
    print()
    print("Bending check")
    print(f"As: {args.as_area:.2f} mm2")
    print(f"M: {args.moment:.2f} N*mm")
    print(f"x: {bending.x:.2f} mm")
    print(f"xi: {bending.xi:.3f}")
    print(f"xi_R: {bending.xi_R:.3f}")
    print(f"Mult: {bending.Mult:.2f} N*mm")
    print(f"utilization: {bending.utilization:.3f}")
    print(f"status: {bending.status}")
    if bending.warnings:
        print("warnings:")
        for warning in bending.warnings:
            print(f"- {warning}")
    return 0
