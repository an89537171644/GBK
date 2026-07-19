import hashlib
import json
import zipfile
from dataclasses import asdict, replace
from datetime import datetime
from pathlib import Path

import pytest

from sp63_core.standalone import (
    run_standalone_beam_case,
    validate_standalone_review_bundle,
)
from sp63_core.standalone.gui_logic import (
    next_output_dir,
    parse_decimal,
    parse_form_values,
    status_view_model,
    verify_gui_result,
)
from sp63_core.standalone.model import StandaloneBeamInput, StandaloneRunResult


def _form_values(**overrides: str) -> dict[str, str]:
    values = {
        "case_id": "beam-gui-001",
        "b_mm": "300",
        "h_mm": "500",
        "cover_mm": "32",
        "stirrup_diameter_mm": "8",
        "concrete_class": "B25",
        "longitudinal_rebar_class": "A500",
        "stirrup_rebar_class": "A240",
        "moment_kNm": "150,5",
        "shear_kN": "80.25",
        "tension_face": "local_y_min",
    }
    values.update(overrides)
    return values


def _run_result(report_index_path: Path | None, **overrides: object) -> StandaloneRunResult:
    values: dict[str, object] = {
        "case_id": "beam-gui-001",
        "status": "review_required",
        "preflight_status": "pass",
        "calculation_status": "outside_applicability",
        "evidence_status": "needs_engineer_review",
        "project_use": False,
        "input_json_path": None,
        "standalone_input_path": None,
        "canonical_input_path": None,
        "latest_status_path": None,
        "report_dir": str(report_index_path.parent) if report_index_path else None,
        "report_index_path": str(report_index_path) if report_index_path else None,
        "report_zip_path": None,
        "deterministic_report_zip_path": None,
        "warnings": ("engineering review remains required",),
        "errors": (),
    }
    values.update(overrides)
    return StandaloneRunResult(**values)


def _rewrite_review_bundle_json(bundle_path: Path, mutate) -> None:
    """Rewrite selected JSON members and keep all integrity records self-consistent."""
    with zipfile.ZipFile(bundle_path, "r") as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}

    json_names = {
        "standalone_bundle_status.json",
        "standalone_review_metadata.json",
        "workflow_summary.json",
        "standalone_review_manifest.json",
        "deterministic_report/report.json",
    }
    payloads = {
        name: json.loads(entries[name].decode("utf-8")) for name in json_names
    }
    mutate(payloads)
    for name, payload in payloads.items():
        if name != "standalone_review_manifest.json":
            entries[name] = (
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
            ).encode()

    manifest = payloads["standalone_review_manifest.json"]
    for record in manifest["files"]:
        data = entries[record["path"]]
        record["sha256"] = hashlib.sha256(data).hexdigest()
        record["size_bytes"] = len(data)
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode()
    entries["standalone_review_manifest.json"] = manifest_bytes
    entries["standalone_review_manifest.sha256"] = (
        f"{hashlib.sha256(manifest_bytes).hexdigest()}  "
        "standalone_review_manifest.json\n"
    ).encode("ascii")

    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)


def _rewrite_review_bundle_text(bundle_path: Path, replacements: dict[str, str]) -> None:
    with zipfile.ZipFile(bundle_path, "r") as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    entries.update({name: value.encode() for name, value in replacements.items()})
    manifest_name = "standalone_review_manifest.json"
    manifest = json.loads(entries[manifest_name].decode("utf-8"))
    for record in manifest["files"]:
        data = entries[record["path"]]
        record["sha256"] = hashlib.sha256(data).hexdigest()
        record["size_bytes"] = len(data)
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode()
    entries[manifest_name] = manifest_bytes
    entries["standalone_review_manifest.sha256"] = (
        f"{hashlib.sha256(manifest_bytes).hexdigest()}  {manifest_name}\n"
    ).encode("ascii")
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("12,5", 12.5),
        ("12.5", 12.5),
        ("0", 0.0),
    ),
)
def test_parse_decimal_accepts_engineer_friendly_decimal_spelling(text, expected):
    assert parse_decimal(text, "Нагрузка") == expected


@pytest.mark.parametrize("text", ("", "   ", "nan", "NaN", "inf", "+inf", "-inf"))
def test_parse_decimal_rejects_blank_and_non_finite_values(text):
    with pytest.raises(ValueError, match="Нагрузка"):
        parse_decimal(text, "Нагрузка")


def test_parse_decimal_does_not_guess_thousands_separators():
    with pytest.raises(ValueError, match="Нагрузка"):
        parse_decimal("1 250,75", "Нагрузка")


def test_parse_form_values_maps_exact_public_eleven_field_contract():
    result = parse_form_values(_form_values())

    assert isinstance(result, StandaloneBeamInput)
    assert asdict(result) == {
        "case_id": "beam-gui-001",
        "b_mm": 300.0,
        "h_mm": 500.0,
        "cover_mm": 32.0,
        "stirrup_diameter_mm": 8.0,
        "concrete_class": "B25",
        "longitudinal_rebar_class": "A500",
        "stirrup_rebar_class": "A240",
        "moment_kNm": 150.5,
        "shear_kN": 80.25,
        "tension_face": "local_y_min",
    }


def test_parse_form_values_rejects_scope_expansion_fields():
    with pytest.raises(ValueError, match="неподдерживаемые поля"):
        parse_form_values({**_form_values(), "element_type": "column"})


def test_gui_layer_does_not_import_calculation_implementations():
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            Path("src/sp63_core/standalone/gui.py"),
            Path("src/sp63_core/standalone/gui_logic.py"),
        )
    )

    assert "sp63_core.checks" not in source
    assert "sp63_core.design" not in source
    assert "run_engineering_workflow" not in source
    assert "kNm_to_Nmm" not in source
    assert "kN_to_N" not in source


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("case_id", ""),
        ("b_mm", ""),
        ("h_mm", "nan"),
        ("cover_mm", "inf"),
        ("stirrup_diameter_mm", "-inf"),
        ("moment_kNm", "not-a-number"),
        ("shear_kN", ""),
    ),
)
def test_parse_form_values_rejects_invalid_or_incomplete_fields(field, value):
    with pytest.raises((KeyError, TypeError, ValueError)):
        parse_form_values(_form_values(**{field: value}))


def test_parse_form_values_applies_existing_engineering_validation():
    with pytest.raises(ValueError, match="Ширина"):
        parse_form_values(_form_values(b_mm="0"))


@pytest.mark.parametrize(
    ("status", "calculation_status", "expected_title", "expected_tone"),
    (
        (
            "review_required",
            "review_required",
            "требуется инженерная проверка",
            "warning",
        ),
        (
            "outside_applicability",
            "outside_applicability",
            "Вне подтверждённой области применимости",
            "danger",
        ),
        ("fail", "not_run", "Расчётный маршрут не выполнен", "danger"),
    ),
)
def test_status_view_model_uses_fail_closed_engineering_labels(
    tmp_path, status, calculation_status, expected_title, expected_tone
):
    report = tmp_path / "standalone_index.html"
    result = _run_result(
        report,
        status=status,
        calculation_status=calculation_status,
    )

    view = status_view_model(result)

    assert expected_title.casefold() in view.title.casefold()
    assert view.tone == expected_tone
    assert status in view.overall
    assert "запрещено" in view.project_use_text.lower()
    assert "требуется" in view.review_text.lower()
    assert view.tone.lower() not in {"green", "pass", "success", "approved"}
    visible_text = " ".join(
        (
            view.title,
            view.project_use_text,
            view.review_text,
            *view.details,
        )
    ).lower()
    assert "разрешено проектное применение" not in visible_text
    assert "расчёт утверждён" not in visible_text


def test_next_output_dir_is_unique_safe_and_does_not_precreate_directory(tmp_path):
    now = datetime(2026, 7, 19, 12, 34, 56)

    first = next_output_dir(tmp_path, "../../unsafe-case", now=now)
    second = next_output_dir(tmp_path, "../../unsafe-case", now=now)

    assert isinstance(first, Path)
    assert first.parent == tmp_path
    assert second.parent == tmp_path
    assert first != second
    assert not first.exists()
    assert not second.exists()
    assert "20260719-123456" in first.name
    assert "unsafe" not in first.name
    assert ".." not in first.name
    assert "/" not in first.name
    assert "\\" not in first.name


def test_verify_gui_result_rejects_unvalidated_review_bundle(tmp_path):
    output_dir = tmp_path / "current"
    output_dir.mkdir()
    report = output_dir / "standalone_index.html"
    report.write_text("current report", encoding="utf-8")
    review_bundle = output_dir / "standalone_review_bundle.zip"
    review_bundle.write_bytes(b"review bundle placeholder")

    result = _run_result(report, report_zip_path=str(review_bundle))
    errors = verify_gui_result(result, output_dir)

    assert errors
    assert any("архив" in error.casefold() for error in errors)


def test_gui_gate_accepts_real_controller_review_package(tmp_path, monkeypatch):
    build_id = "wheel-sha256:" + "a" * 64
    monkeypatch.setenv("GBK_BUILD_ID", build_id)
    input_data = parse_form_values(_form_values())
    output_dir = tmp_path / "actual-controller-output"

    result = run_standalone_beam_case(input_data, output_dir)

    assert result.status == "review_required"
    assert result.calculation_status == "outside_applicability"
    view = status_view_model(result)
    assert view.tone == "danger"
    assert "вне подтверждённой области" in view.title.casefold()
    assert verify_gui_result(result, output_dir) == ()

    metadata_path = output_dir / "standalone_review_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["code_identity"]["build_id"] = "wheel-sha256:" + "b" * 64
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    assert verify_gui_result(result, output_dir) == ()

    monkeypatch.setenv("GBK_BUILD_ID", "wheel-sha256:" + "b" * 64)
    errors = verify_gui_result(result, output_dir)
    assert any("build_id" in error or "сборк" in error for error in errors)


def test_gui_gate_rejects_tampered_real_review_package(tmp_path, monkeypatch):
    monkeypatch.setenv("GBK_BUILD_ID", "wheel-sha256:" + "a" * 64)
    input_data = parse_form_values(_form_values())
    output_dir = tmp_path / "actual-controller-output"
    result = run_standalone_beam_case(input_data, output_dir)

    Path(result.report_zip_path or "").write_bytes(b"tampered")

    errors = verify_gui_result(result, output_dir)
    assert errors
    assert any("архив" in error.casefold() for error in errors)


def test_public_bundle_validator_rejects_self_consistent_approved_statuses(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    result = run_standalone_beam_case(
        parse_form_values(_form_values()),
        tmp_path / "semantic-status-tamper",
    )
    bundle = Path(result.report_zip_path or "")

    def mutate(payloads):
        for name in ("standalone_bundle_status.json", "workflow_summary.json"):
            payloads[name]["preflight_status"] = "approved"
            payloads[name]["calculation_status"] = "approved"
            payloads[name]["evidence_status"] = "confirmed"

    _rewrite_review_bundle_json(bundle, mutate)

    errors = validate_standalone_review_bundle(bundle)
    assert any("preflight_status" in error for error in errors)
    assert any("calculation_status" in error for error in errors)
    assert any("evidence_status" in error for error in errors)


def test_public_bundle_validator_rejects_bool_as_integer_and_normative_claim(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    result = run_standalone_beam_case(
        parse_form_values(_form_values()),
        tmp_path / "semantic-type-tamper",
    )
    bundle = Path(result.report_zip_path or "")

    def mutate(payloads):
        payloads["standalone_review_manifest.json"]["project_use"] = 0
        payloads["standalone_review_metadata.json"]["units_layer"][
            "normative_formula_asserted"
        ] = True

    _rewrite_review_bundle_json(bundle, mutate)

    errors = validate_standalone_review_bundle(bundle)
    assert any("project_use" in error for error in errors)
    assert any("normative_formula_asserted" in error for error in errors)


def test_public_bundle_validator_rejects_duplicate_manifest_record(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    result = run_standalone_beam_case(
        parse_form_values(_form_values()),
        tmp_path / "duplicate-record-tamper",
    )
    bundle = Path(result.report_zip_path or "")

    def mutate(payloads):
        manifest = payloads["standalone_review_manifest.json"]
        manifest["files"].append(dict(manifest["files"][0]))

    _rewrite_review_bundle_json(bundle, mutate)

    errors = validate_standalone_review_bundle(bundle)
    assert any("record count" in error or "duplicated" in error for error in errors)


def test_public_bundle_validator_rejects_deterministic_report_safety_tamper(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    result = run_standalone_beam_case(
        parse_form_values(_form_values()),
        tmp_path / "deterministic-safety-tamper",
    )
    bundle = Path(result.report_zip_path or "")

    def mutate(payloads):
        report = payloads["deterministic_report/report.json"]
        report["project_use"] = True
        report["report"]["project_use"] = True
        report["report"]["protocol"]["project_use"] = True

    _rewrite_review_bundle_json(bundle, mutate)

    errors = validate_standalone_review_bundle(bundle, expected_result=result)
    assert any("project_use" in error for error in errors)


def test_public_bundle_validator_binds_calculation_status_to_report(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    result = run_standalone_beam_case(
        parse_form_values(_form_values()),
        tmp_path / "calculation-status-tamper",
    )
    bundle = Path(result.report_zip_path or "")

    def mutate(payloads):
        payloads["standalone_bundle_status.json"]["calculation_status"] = "pass"
        payloads["workflow_summary.json"]["calculation_status"] = "pass"

    _rewrite_review_bundle_json(bundle, mutate)

    errors = validate_standalone_review_bundle(bundle)
    assert any("deterministic report" in error for error in errors)


def test_gui_gate_rejects_tampered_top_level_html(tmp_path, monkeypatch):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    output_dir = tmp_path / "html-tamper"
    result = run_standalone_beam_case(
        parse_form_values(_form_values()),
        output_dir,
    )
    index_path = Path(result.report_index_path or "")
    index_path.write_text(
        index_path.read_text(encoding="utf-8") + "\n<p>APPROVED</p>\n",
        encoding="utf-8",
    )

    errors = verify_gui_result(result, output_dir)
    assert any("верхнеуровневый отчёт" in error.casefold() for error in errors)


def test_public_bundle_validator_rejects_tampered_human_facing_files(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    result = run_standalone_beam_case(
        parse_form_values(_form_values()),
        tmp_path / "human-facing-tamper",
    )
    bundle = Path(result.report_zip_path or "")
    _rewrite_review_bundle_text(
        bundle,
        {
            "index.html": "<h1>APPROVED FOR PROJECT USE</h1>",
            "README_REVIEW_BUNDLE.md": "project_use=true\nAPPROVED\n",
            "deterministic_report/report.md": "project_use=true\nAPPROVED\n",
            "deterministic_report/report.html": "<p>APPROVED FOR PROJECT USE</p>",
        },
    )

    errors = validate_standalone_review_bundle(bundle, expected_result=result)
    assert any("bundle index" in error for error in errors)
    assert any("bundle README" in error for error in errors)
    assert any("report Markdown" in error for error in errors)
    assert any("report HTML" in error for error in errors)


def test_verify_gui_result_rejects_failed_result_even_if_old_report_exists(tmp_path):
    output_dir = tmp_path / "failed"
    output_dir.mkdir()
    report = output_dir / "standalone_index.html"
    report.write_text("stale report", encoding="utf-8")
    failed = replace(
        _run_result(report),
        status="fail",
        errors=("calculation failed",),
    )

    errors = verify_gui_result(failed, output_dir)

    assert errors
    assert any("fail" in error.lower() for error in errors)


@pytest.mark.parametrize("stale_kind", ("missing", "outside"))
def test_verify_gui_result_rejects_missing_or_outside_report(tmp_path, stale_kind):
    output_dir = tmp_path / "current"
    output_dir.mkdir()
    if stale_kind == "missing":
        stale_report = output_dir / "missing-index.html"
    else:
        stale_report = tmp_path / "previous" / "standalone_index.html"
        stale_report.parent.mkdir()
        stale_report.write_text("previous report", encoding="utf-8")

    errors = verify_gui_result(_run_result(stale_report), output_dir)

    assert errors


@pytest.mark.parametrize(
    ("overrides", "unsafe_term"),
    (
        ({"project_use": True}, "project_use"),
        ({"requires_engineer_review": False}, "инженер"),
    ),
)
def test_verify_gui_result_rejects_relaxed_safety_flags(tmp_path, overrides, unsafe_term):
    output_dir = tmp_path / "unsafe"
    output_dir.mkdir()
    report = output_dir / "standalone_index.html"
    report.write_text("unsafe report", encoding="utf-8")
    review_bundle = output_dir / "standalone_review_bundle.zip"
    review_bundle.write_bytes(b"review bundle placeholder")

    errors = verify_gui_result(
        _run_result(report, report_zip_path=str(review_bundle), **overrides),
        output_dir,
    )

    assert errors
    assert any(unsafe_term in error.lower() for error in errors)


@pytest.mark.parametrize(
    ("overrides", "expected_fragment"),
    (
        ({"element_type": "column"}, "прямоугольной балке"),
        ({"load_duration": "long"}, "кратковременному"),
        ({"status_scope": "diagnostic"}, "публичную область"),
        ({"completeness_status": "complete"}, "incomplete"),
    ),
)
def test_verify_gui_result_rejects_scope_expansion(
    tmp_path,
    overrides,
    expected_fragment,
):
    output_dir = tmp_path / "expanded-scope"
    output_dir.mkdir()
    report = output_dir / "standalone_index.html"
    report.write_text("unsafe report", encoding="utf-8")
    review_bundle = output_dir / "standalone_review_bundle.zip"
    review_bundle.write_bytes(b"review bundle placeholder")

    errors = verify_gui_result(
        _run_result(report, report_zip_path=str(review_bundle), **overrides),
        output_dir,
    )

    assert any(expected_fragment in error for error in errors)
