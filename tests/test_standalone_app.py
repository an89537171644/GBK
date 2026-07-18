import json

from sp63_core.standalone.app import main


def _input_payload() -> dict[str, object]:
    return {
        "element_type": "rectangular_beam",
        "load_duration": "short",
        "case_id": "standalone-app-001",
        "b_mm": 300,
        "h_mm": 500,
        "cover_mm": 32,
        "stirrup_diameter_mm": 8,
        "concrete_class": "B25",
        "longitudinal_rebar_class": "A500",
        "stirrup_rebar_class": "A240",
        "moment_kNm": 150,
        "shear_kN": 80,
        "tension_face": "local_y_min",
    }


def test_standalone_app_json_route_builds_public_report(tmp_path, capsys):
    input_path = tmp_path / "beam.json"
    output_dir = tmp_path / "result"
    input_path.write_text(json.dumps(_input_payload()), encoding="utf-8")

    exit_code = main(
        [
            "--input-json",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "standalone-beam"
    assert payload["project_use"] is False
    assert payload["requires_engineer_review"] is True
    assert payload["ml_included"] is False
    assert payload["reinforcement_selection_status"] == "diagnostic_only"
    assert (output_dir / "workflow" / "index.html").exists()
    assert (output_dir / "workflow" / "deterministic_report.zip").exists()
    assert payload["report_zip_path"] == str(output_dir / "standalone_review_bundle.zip")
    assert (output_dir / "standalone_review_bundle.zip").exists()


def test_standalone_app_rejects_slab_before_calculation(tmp_path, capsys):
    input_payload = _input_payload()
    input_payload["element_type"] = "slab_strip"
    input_path = tmp_path / "slab.json"
    output_dir = tmp_path / "result"
    input_path.write_text(json.dumps(input_payload), encoding="utf-8")

    exit_code = main(
        [
            "--input-json",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["status"] == "fail"
    assert payload["project_use"] is False
    assert "rectangular_beam" in payload["errors"][0]
    assert not output_dir.exists()


def test_standalone_app_never_overwrites_source_json(tmp_path, capsys):
    input_path = tmp_path / "beam.json"
    original = json.dumps(_input_payload(), ensure_ascii=False, indent=2)
    input_path.write_text(original, encoding="utf-8")

    exit_code = main(
        [
            "--input-json",
            str(input_path),
            "--output-dir",
            str(tmp_path),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["status"] == "fail"
    assert "не должен содержать исходный JSON" in payload["errors"][0]
    assert input_path.read_text(encoding="utf-8") == original


def test_standalone_app_rejects_duplicate_json_fields(tmp_path, capsys):
    input_path = tmp_path / "duplicate.json"
    input_path.write_text('{"case_id": "first", "case_id": "second"}', encoding="utf-8")

    exit_code = main(["--input-json", str(input_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["status"] == "fail"
    assert "повторяющееся поле: case_id" in payload["errors"][0]


def test_standalone_text_output_never_hides_calculation_status(tmp_path, capsys):
    input_path = tmp_path / "beam.json"
    input_path.write_text(json.dumps(_input_payload()), encoding="utf-8")

    exit_code = main(
        [
            "--input-json",
            str(input_path),
            "--output-dir",
            str(tmp_path / "result"),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Статус выполнения: review_required" in output
    assert "Статус расчётного маршрута: outside_applicability" in output
    assert "не является утверждением расчёта или несущей способности" in output
    assert "diagnostic proposals only" in output
