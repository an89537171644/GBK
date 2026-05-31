import json
from pathlib import Path

import pytest

from sp63_core.cli import main
from sp63_core.design import RectangularDesignInput, design_rectangular_element
from sp63_core.report import (
    build_rectangular_design_report,
    load_rectangular_design_input_from_json,
    rectangular_design_input_from_mapping,
)

EXAMPLE_INPUT = "docs/reports/examples/rectangular_design_input_example.json"


def test_design_report_input_example_loads():
    design_input = load_rectangular_design_input_from_json(EXAMPLE_INPUT)

    assert isinstance(design_input, RectangularDesignInput)
    assert design_input.b == 300
    assert design_input.concrete_class == "B25"
    assert design_input.check_crack_width is True


def test_design_report_builds_from_json_input():
    design_input = load_rectangular_design_input_from_json(EXAMPLE_INPUT)
    result = design_rectangular_element(design_input)
    report = build_rectangular_design_report(result)

    assert report.report_type == "rectangular_design_calculation_report"
    assert report.requires_engineer_review is True
    assert report.json_data["input_data"]["Mser"] == 30_000_000
    assert "crack_width" in report.json_data["checks"]


def test_design_report_input_rejects_missing_required_field():
    with pytest.raises(ValueError, match="missing required design report input fields: b"):
        rectangular_design_input_from_mapping(
            {
                "h": 500,
                "cover": 32,
                "stirrup_diameter_for_geometry": 8,
                "concrete_class": "B25",
                "longitudinal_rebar_class": "A500",
                "stirrup_rebar_class": "A240",
                "M": 150_000_000,
                "Q": 80_000,
            }
        )


def test_design_report_input_rejects_unknown_field():
    data = {
        "b": 300,
        "h": 500,
        "cover": 32,
        "stirrup_diameter_for_geometry": 8,
        "concrete_class": "B25",
        "longitudinal_rebar_class": "A500",
        "stirrup_rebar_class": "A240",
        "M": 150_000_000,
        "Q": 80_000,
        "unexpected_capacity_override": 1.0,
    }

    with pytest.raises(ValueError, match="unknown design report input fields"):
        rectangular_design_input_from_mapping(data)


def test_cli_design_report_input_json_output(capsys):
    exit_code = main(["design-report", "--input-json", EXAMPLE_INPUT, "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "design-report"
    assert data["source"] == "input_json"
    assert data["report_type"] == "rectangular_design_calculation_report"
    assert data["requires_engineer_review"] is True
    assert data["input_data"]["b"] == 300
    assert "checks" in data


def test_cli_design_report_input_markdown_output(capsys):
    exit_code = main(["design-report", "--input-json", EXAMPLE_INPUT, "--markdown"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Rectangular Design Calculation Report" in captured.out
    assert "strength_status" in captured.out


def test_cli_design_report_input_html_output(capsys):
    exit_code = main(["design-report", "--input-json", EXAMPLE_INPUT, "--html"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "<html" in captured.out.lower()
    assert "Rectangular Design Calculation Report" in captured.out


def test_cli_design_report_input_output_file(tmp_path, capsys):
    output_path = tmp_path / "case_report.md"
    exit_code = main(
        [
            "design-report",
            "--input-json",
            EXAMPLE_INPUT,
            "--markdown",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Design report written" in captured.out
    assert "Rectangular Design Calculation Report" in output_path.read_text(encoding="utf-8")


def test_cli_design_report_bundle_output(tmp_path, capsys):
    output_dir = tmp_path / "case_001"
    exit_code = main(
        [
            "design-report",
            "--input-json",
            EXAMPLE_INPUT,
            "--bundle-output",
            str(output_dir),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Design report bundle written" in captured.out
    assert (output_dir / "report.md").exists()
    assert (output_dir / "report.json").exists()
    assert (output_dir / "report.html").exists()
    assert (output_dir / "input.json").exists()
    assert (output_dir / "manifest.json").exists()
    bundled_input = json.loads((output_dir / "input.json").read_text(encoding="utf-8"))
    source_input = json.loads(Path(EXAMPLE_INPUT).read_text(encoding="utf-8"))
    assert bundled_input == source_input
