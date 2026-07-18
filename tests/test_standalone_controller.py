import json
import re
from pathlib import Path

from sp63_core.standalone import StandaloneBeamInput, run_standalone_beam_case
from sp63_core.standalone.app import load_standalone_input


def beam_input(**overrides) -> StandaloneBeamInput:
    values = {
        "case_id": "controller-beam-001",
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
    values.update(overrides)
    return StandaloneBeamInput(**values)


def test_controller_builds_public_review_package_without_ml(tmp_path):
    result = run_standalone_beam_case(beam_input(), tmp_path)

    assert result.status == "review_required"
    assert result.preflight_status == "pass"
    assert result.calculation_status == "outside_applicability"
    assert result.evidence_status == "needs_engineer_review"
    assert result.project_use is False
    assert result.project_use_status == "prohibited"
    assert result.requires_engineer_review is True
    assert result.ml_included is False
    assert result.reinforcement_selection_status == "diagnostic_only"
    assert result.errors == ()
    assert any("Slab-strip mode is unavailable" in warning for warning in result.warnings)
    assert any(
        "selected longitudinal or transverse reinforcement" in warning
        and "not an approved design decision" in warning
        for warning in result.warnings
    )
    assert result.report_dir is not None
    assert result.report_index_path is not None
    assert result.report_zip_path is not None
    assert Path(result.report_dir).is_dir()
    assert Path(result.report_index_path).is_file()
    assert Path(result.report_index_path).name == "standalone_index.html"
    assert Path(result.report_zip_path).is_file()
    assert Path(result.report_zip_path).name == "standalone_review_bundle.zip"
    assert result.deterministic_report_zip_path is not None
    assert Path(result.deterministic_report_zip_path).is_file()
    assert Path(result.deterministic_report_zip_path).name == "deterministic_report.zip"
    landing = Path(result.report_index_path).read_text(encoding="utf-8")
    assert "project_use=false" in landing
    assert "requires_engineer_review=true" in landing
    assert "Любой локальный статус" in landing
    assert "workflow/index.html" in landing
    assert "standalone_review_bundle.zip" in landing
    assert "передавать следует только этот архив" in landing
    local_hrefs = re.findall(r'href="([^"]+)"', landing)
    assert local_hrefs
    assert all((tmp_path / href).is_file() for href in local_hrefs)
    readme = (tmp_path / "README_STANDALONE_RESULT.md").read_text(encoding="utf-8")
    assert "внутренний ZIP не предназначен" in readme
    assert not (tmp_path / "workflow" / "ml_readiness").exists()


def test_controller_writes_canonical_internal_units(tmp_path):
    result = run_standalone_beam_case(
        beam_input(moment_kNm=12.5, shear_kN=7.25),
        tmp_path,
    )

    assert result.input_json_path is not None
    assert result.canonical_input_path == result.input_json_path
    assert Path(result.input_json_path).name == "canonical_input.json"
    payload = json.loads(Path(result.input_json_path).read_text(encoding="utf-8"))
    assert payload["M"] == 12_500_000
    assert payload["Q"] == 7_250
    assert payload["load_duration"] == "short"
    assert payload["check_cracks"] is False
    assert payload["check_crack_width"] is False
    assert payload["check_deflection"] is False
    assert "include_ml_readiness" not in payload
    assert "element_type" not in payload

    assert result.standalone_input_path is not None
    assert Path(result.standalone_input_path).name == "standalone_input.json"
    standalone_payload = json.loads(
        Path(result.standalone_input_path).read_text(encoding="utf-8")
    )
    assert standalone_payload["moment_kNm"] == 12.5
    assert standalone_payload["shear_kN"] == 7.25
    assert set(standalone_payload) == {
        "element_type",
        "load_duration",
        "case_id",
        "b_mm",
        "h_mm",
        "cover_mm",
        "stirrup_diameter_mm",
        "concrete_class",
        "longitudinal_rebar_class",
        "stirrup_rebar_class",
        "moment_kNm",
        "shear_kN",
        "tension_face",
    }
    assert load_standalone_input(Path(result.standalone_input_path)) == beam_input(
        moment_kNm=12.5,
        shear_kN=7.25,
    )


def test_controller_records_owned_failure_without_exposing_reports(tmp_path):
    result = run_standalone_beam_case(beam_input(moment_kNm=-1), tmp_path)

    assert result.status == "fail"
    assert result.preflight_status == "not_run"
    assert result.calculation_status == "not_run"
    assert result.project_use is False
    assert result.input_json_path is None
    assert result.report_dir is None
    assert result.report_index_path is None
    assert result.report_zip_path is None
    assert result.deterministic_report_zip_path is None
    assert any("input validation failed" in error for error in result.errors)
    assert result.latest_status_path is not None
    latest_status = json.loads(Path(result.latest_status_path).read_text(encoding="utf-8"))
    assert latest_status["status"] == "fail"
    assert latest_status["report_zip_path"] is None
    assert (tmp_path / ".gbk_standalone_output.json").is_file()
    assert not (tmp_path / "workflow").exists()
    assert not (tmp_path / "canonical_input.json").exists()
    assert not (tmp_path / "standalone_input.json").exists()


def test_conversion_overflow_fails_before_canonical_input_or_workflow(tmp_path):
    result = run_standalone_beam_case(beam_input(moment_kNm=1e308), tmp_path)

    assert result.status == "fail"
    assert any("unit conversion must remain finite" in error for error in result.errors)
    assert not (tmp_path / "canonical_input.json").exists()
    assert not (tmp_path / "standalone_input.json").exists()
    assert not (tmp_path / "workflow").exists()


def test_controller_keeps_beam_only_scope_explicit(tmp_path):
    result = run_standalone_beam_case(beam_input(), tmp_path)

    assert result.element_type == "rectangular_beam"
    assert result.load_duration == "short"
    assert result.status_scope == "public"
    assert result.ml_included is False


def test_success_then_invalid_same_output_removes_all_stale_reports(tmp_path):
    success = run_standalone_beam_case(beam_input(), tmp_path)

    assert success.report_dir is not None
    assert success.report_index_path is not None
    assert success.report_zip_path is not None
    assert success.deterministic_report_zip_path is not None
    stale_paths = tuple(
        Path(path)
        for path in (
            success.report_dir,
            success.report_index_path,
            success.report_zip_path,
            success.deterministic_report_zip_path,
        )
    )
    assert all(path.exists() for path in stale_paths)

    failure = run_standalone_beam_case(beam_input(moment_kNm=-1), tmp_path)

    assert failure.status == "fail"
    assert failure.report_dir is None
    assert failure.report_index_path is None
    assert failure.report_zip_path is None
    assert failure.deterministic_report_zip_path is None
    assert not any(path.exists() for path in stale_paths)
    assert not (tmp_path / "workflow").exists()
    latest_status = json.loads(
        (tmp_path / "standalone_latest_status.json").read_text(encoding="utf-8")
    )
    assert latest_status["status"] == "fail"
    assert latest_status["report_dir"] is None
    assert latest_status["report_index_path"] is None
    assert latest_status["report_zip_path"] is None


def test_unowned_nonempty_output_fails_without_touching_user_files(tmp_path):
    input_path = tmp_path / "input.json"
    notes_path = tmp_path / "user_notes.txt"
    input_path.write_bytes(b'{"belongs": "to user"}\n')
    notes_path.write_bytes(b"keep me\n")
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}

    result = run_standalone_beam_case(beam_input(), tmp_path)

    assert result.status == "fail"
    assert result.latest_status_path is None
    assert any("ownership marker" in error for error in result.errors)
    after = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    assert after == before


def test_owned_output_uses_collision_safe_names_and_preserves_unknown_files(tmp_path):
    first = run_standalone_beam_case(beam_input(), tmp_path)
    assert first.status == "review_required"
    user_input_path = tmp_path / "input.json"
    user_notes_path = tmp_path / "user_notes.txt"
    user_input_path.write_bytes(b'{"source": "user"}\n')
    user_notes_path.write_bytes(b"do not delete\n")

    second = run_standalone_beam_case(beam_input(case_id="controller-beam-002"), tmp_path)

    assert second.status == "review_required"
    assert user_input_path.read_bytes() == b'{"source": "user"}\n'
    assert user_notes_path.read_bytes() == b"do not delete\n"
    assert second.input_json_path == second.canonical_input_path
    assert Path(second.canonical_input_path).name == "canonical_input.json"
    assert Path(second.standalone_input_path).name == "standalone_input.json"
    assert Path(second.canonical_input_path) != user_input_path
    assert Path(second.standalone_input_path) != user_input_path


def test_landing_page_escapes_user_controlled_case_id(tmp_path):
    result = run_standalone_beam_case(
        beam_input(case_id="case-<script>alert(1)</script>"),
        tmp_path,
    )

    assert result.status == "review_required"
    assert result.report_index_path is not None
    landing = Path(result.report_index_path).read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in landing
    assert "case-&lt;script&gt;alert(1)&lt;/script&gt;" in landing
