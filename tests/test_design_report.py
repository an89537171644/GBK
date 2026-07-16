import json
from dataclasses import replace

from sp63_core.cli import main
from sp63_core.design import RectangularDesignInput, design_rectangular_element
from sp63_core.report import (
    build_rectangular_design_report,
    render_rectangular_design_report_html,
    render_rectangular_design_report_markdown,
)


def report_input() -> RectangularDesignInput:
    return RectangularDesignInput(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter_for_geometry=8,
        concrete_class="B25",
        longitudinal_rebar_class="A500",
        stirrup_rebar_class="A240",
        M=150_000_000,
        Q=80_000,
        local_axes_id="design-report-test-local-axes",
        moment_axis="local_z",
        tension_face="local_y_min",
        load_duration="short",
        Mser=30_000_000,
        check_cracks=True,
        check_crack_width=True,
        check_deflection=True,
        span=6000,
    )


def report_result():
    return design_rectangular_element(report_input())


def test_design_report_markdown_contains_required_sections():
    markdown = render_rectangular_design_report_markdown(report_result())
    lower_markdown = markdown.lower()

    assert "strength_status" in markdown
    assert "serviceability_status" in markdown
    assert "overall_status" in markdown
    assert "bending" in lower_markdown
    assert "shear" in lower_markdown
    assert "crack" in lower_markdown
    assert "deflection" in lower_markdown
    assert "requires_engineer_review = true" in markdown


def test_design_report_json_contains_expected_blocks():
    report = build_rectangular_design_report(report_result())

    assert report.requires_engineer_review is True
    assert report.completeness_status == "incomplete"
    assert report.evidence_status == "needs_engineer_review"
    assert report.project_use_status == "prohibited"
    assert report.project_use is False
    assert report.json_data["report_type"] == "rectangular_design_calculation_report"
    assert report.json_data["requires_engineer_review"] is True
    assert "input_data" in report.json_data
    assert "materials" in report.json_data
    assert "geometry" in report.json_data
    assert "reinforcement" in report.json_data
    assert "checks" in report.json_data
    assert "warnings" in report.json_data
    assert report.json_data["geometry"]["local_axes_id"] == (
        "design-report-test-local-axes"
    )
    assert report.json_data["materials"]["Rb_base"] == 14.5
    assert report.json_data["materials"]["gamma_b1"] == 1.0
    assert report.json_data["materials"]["Rb_effective"] == 14.5
    assert report.json_data["materials"]["material_context_status"] == "resolved"
    assert report.json_data["materials"]["material_source_clauses"]


def test_design_report_unsupported_material_profile_does_not_stamp_normative_context():
    design_result = design_rectangular_element(
        replace(report_input(), longitudinal_rebar_class="A240")
    )

    report = build_rectangular_design_report(design_result)
    materials = report.json_data["materials"]

    assert materials["longitudinal_rebar_class"] == "A240"
    assert materials["longitudinal_rebar"]["Rs"] == design_result.longitudinal_rebar.Rs
    assert materials["material_context_status"] == "unsupported"
    assert "unsupported ULS longitudinal rebar class" in materials["material_context_error"]
    assert materials["normative_profile_id"] is None
    assert materials["load_combination"] is None
    assert materials["Rb_effective"] is None
    assert materials["Rsc"] is None
    assert report.project_use_status == "prohibited"
    assert report.project_use is False


def test_design_report_fallback_geometry_uses_selected_main_bar():
    design_result = design_rectangular_element(
        replace(
            report_input(),
            M=20_000_000,
            Q=2_000_000,
            main_bar_counts=(2, 3, 4),
            main_bar_diameters=(10,),
            check_cracks=False,
            check_crack_width=False,
            check_deflection=False,
        )
    )

    assert design_result.protocol is None
    assert design_result.selected_longitudinal is not None
    assert design_result.selected_transverse is None
    report = build_rectangular_design_report(design_result)

    assert report.json_data["geometry"]["h0"] == 455.0
    assert report.json_data["geometry"]["h0_source"] == (
        "derived_from_selected_longitudinal_geometry"
    )
    assert report.json_data["geometry"]["selected_main_bar_diameter"] == 10


def test_design_report_does_not_publish_dummy_h0_without_selected_main_bar():
    design_result = design_rectangular_element(replace(report_input(), M=2_000_000_000))

    assert design_result.protocol is None
    assert design_result.selected_longitudinal is None
    report = build_rectangular_design_report(design_result)

    assert report.json_data["geometry"]["h0"] is None
    assert report.json_data["geometry"]["h0_source"] == (
        "not_available_no_selected_main_bar"
    )


def test_design_report_html_builds_static_document():
    html = render_rectangular_design_report_html(report_result())

    assert "<html" in html.lower()
    assert "Rectangular Design Calculation Report" in html


def test_cli_design_report_json_output(capsys):
    exit_code = main(["design-report", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "design-report"
    assert data["report"]["report_type"] == "rectangular_design_calculation_report"
    assert data["report"]["requires_engineer_review"] is True


def test_cli_design_report_markdown_output(capsys):
    exit_code = main(["design-report", "--markdown"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Rectangular Design Calculation Report" in captured.out
    assert "strength_status" in captured.out


def test_cli_design_report_html_output(capsys):
    exit_code = main(["design-report", "--html"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "<html" in captured.out.lower()
    assert "Rectangular Design Calculation Report" in captured.out


def test_cli_design_report_output_file(tmp_path, capsys):
    output_path = tmp_path / "rectangular_design_report.md"
    exit_code = main(["design-report", "--markdown", "--output", str(output_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert output_path.exists()
    assert "Design report written" in captured.out
    assert "Rectangular Design Calculation Report" in output_path.read_text(encoding="utf-8")
