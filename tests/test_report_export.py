import json

from sp63_core.cli import main
from sp63_core.materials import get_concrete, get_rebar
from sp63_core.report import (
    protocol_to_html,
    protocol_to_json,
    save_protocol_html,
    save_protocol_json,
)
from sp63_core.sections import RectangularSection
from sp63_core.services import design_rectangular_element


def passing_protocol():
    design = design_rectangular_element(
        section=RectangularSection(
            b=300,
            h=500,
            cover=32,
            stirrup_diameter=8,
            main_bar_diameter=20,
        ),
        concrete=get_concrete("B25"),
        longitudinal_rebar=get_rebar("A500"),
        transverse_rebar=get_rebar("A240"),
        M=150_000_000,
        Q=80_000,
    )

    assert design.protocol is not None
    return design.protocol


def test_protocol_to_json_contains_status():
    payload = protocol_to_json(passing_protocol())
    data = json.loads(payload)

    assert data["status"] == "pass"
    assert data["requires_engineer_review"] is True


def test_save_protocol_json_creates_file(tmp_path):
    output_path = save_protocol_json(passing_protocol(), tmp_path / "protocol.json")

    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8"))["status"] == "pass"


def test_protocol_to_html_contains_sections_status_and_review_warning():
    html = protocol_to_html(passing_protocol())

    assert "Исходные данные" in html or "Input data" in html
    assert "status" in html
    assert "pass" in html
    assert "requires_engineer_review" in html
    assert "MVP/draft" in html


def test_save_protocol_html_creates_file(tmp_path):
    output_path = save_protocol_html(passing_protocol(), tmp_path / "protocol.html")

    assert output_path.exists()
    assert "SP63 calculation protocol" in output_path.read_text(encoding="utf-8")


def test_cli_design_report_export_creates_json_and_html(tmp_path, capsys):
    json_path = tmp_path / "design.json"
    html_path = tmp_path / "design.html"

    exit_code = main(
        [
            "design",
            "--cover",
            "32",
            "--moment",
            "150000000",
            "--q",
            "80000",
            "--report-json",
            str(json_path),
            "--report-html",
            str(html_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "overall status: pass" in captured.out
    assert json_path.exists()
    assert html_path.exists()
