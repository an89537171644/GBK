import json

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
    assert report.json_data["report_type"] == "rectangular_design_calculation_report"
    assert report.json_data["requires_engineer_review"] is True
    assert "input_data" in report.json_data
    assert "materials" in report.json_data
    assert "geometry" in report.json_data
    assert "reinforcement" in report.json_data
    assert "checks" in report.json_data
    assert "warnings" in report.json_data


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
