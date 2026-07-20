import hashlib
import json
import zipfile
from dataclasses import asdict, replace
from datetime import datetime
from pathlib import Path

import pytest

import sp63_core.standalone.gui_logic as gui_logic_module
from sp63_core.report import (
    render_rectangular_design_report_html,
    render_rectangular_design_report_markdown,
)
from sp63_core.standalone import (
    run_standalone_beam_case,
    validate_standalone_review_bundle,
)
from sp63_core.standalone.gui import EngineerGui
from sp63_core.standalone.gui_logic import (
    blocked_result_messages,
    build_diagram_model,
    load_gui_result_summary,
    next_output_dir,
    parse_decimal,
    parse_form_values,
    status_view_model,
    summary_as_text,
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
        "standalone_input.json",
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

    nested_report = payloads["deterministic_report/report.json"]["report"]
    entries["deterministic_report/report.md"] = render_rectangular_design_report_markdown(
        nested_report
    ).encode("utf-8")
    entries["deterministic_report/report.html"] = render_rectangular_design_report_html(
        nested_report
    ).encode("utf-8")

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


def test_public_bundle_validator_accepts_platform_crlf_renderings(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    result = run_standalone_beam_case(
        parse_form_values(_form_values()),
        tmp_path / "platform-newlines",
    )
    bundle = Path(result.report_zip_path or "")
    with zipfile.ZipFile(bundle, "r") as archive:
        replacements = {
            name: archive.read(name)
            .decode("utf-8")
            .replace("\r\n", "\n")
            .replace("\n", "\r\n")
            for name in (
                "index.html",
                "README_REVIEW_BUNDLE.md",
                "deterministic_report/report.md",
                "deterministic_report/report.html",
            )
        }
    _rewrite_review_bundle_text(bundle, replacements)

    assert validate_standalone_review_bundle(bundle, expected_result=result) == ()


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


def test_uat_failed_selection_prioritizes_actionable_reason(tmp_path):
    input_data = parse_form_values(
        _form_values(
            b_mm="100",
            stirrup_rebar_class="A400",
            moment_kNm="150",
            shear_kN="80",
        )
    )
    output_dir = tmp_path / "uat-narrow-beam"

    result = run_standalone_beam_case(input_data, output_dir)
    gate_errors = verify_gui_result(result, output_dir)
    messages = blocked_result_messages(result, gate_errors)
    visible_text = "\n".join(messages).casefold()

    assert result.status == "fail"
    assert gate_errors
    assert "не выбран ни один проходящий диагностический вариант" in visible_text
    assert "вне подтверждённой области применимости" in visible_text
    assert "отсутствует верхнеуровневый html-отчёт" not in visible_text
    assert "отсутствует архив для инженерной рецензии" not in visible_text
    assert "protocol must be an object" not in visible_text
    assert "применение в проекте запрещено" in visible_text
    assert "не доказывает невозможность расчётного решения" in visible_text
    assert "не является рекомендацией" in visible_text


def test_failed_selection_message_does_not_mask_safety_violation(tmp_path):
    output_dir = tmp_path / "failed"
    output_dir.mkdir()
    failed = replace(
        _run_result(None),
        status="fail",
        project_use=True,
        errors=(
            "standalone review bundle failed: "
            "deterministic public report protocol must be an object",
        ),
        warnings=(
            "no passing diagnostic longitudinal reinforcement options; "
            "public ULS bending remains outside applicability",
        ),
    )

    gate_errors = verify_gui_result(failed, output_dir)
    messages = blocked_result_messages(failed, gate_errors)

    assert "project_use=false" in messages[0]


def test_missing_artifacts_remain_visible_for_exposable_result(tmp_path):
    output_dir = tmp_path / "missing"
    output_dir.mkdir()
    result = _run_result(None)

    gate_errors = verify_gui_result(result, output_dir)

    assert blocked_result_messages(result, gate_errors) == gate_errors
    assert any("HTML-отчёт" in message for message in gate_errors)
    assert any("архив" in message.casefold() for message in gate_errors)


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


def test_result_summary_loads_only_whitelisted_values_from_validated_public_zip(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    input_data = parse_form_values(_form_values())
    output_dir = tmp_path / "summary-run"
    result = run_standalone_beam_case(input_data, output_dir)

    summary = load_gui_result_summary(result, output_dir, input_data)
    visible = summary_as_text(summary)

    assert "300 × 500 мм" in visible
    assert "|M| = 150.5 кН·м" in visible
    assert "|Q| = 80.25 кН" in visible
    assert "local_y_min" in visible
    assert "6D14" in visible
    assert "D8/200, 2 legs" in visible
    assert "outside_applicability" in visible
    assert "Локальная техническая проверка: pass" in visible
    assert "не является проектным допуском" in visible
    assert "project_use=false" in visible
    assert "requires_engineer_review=true" in visible
    assert "diagnostic_only" in visible

    exposed_field_names: set[str] = set()

    def collect_field_names(value):
        if isinstance(value, dict):
            exposed_field_names.update(value)
            for item in value.values():
                collect_field_names(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                collect_field_names(item)

    collect_field_names(asdict(summary))
    assert exposed_field_names.isdisjoint(
        {
            "Mult",
            "Qult",
            "utilization",
            "x",
            "xi",
            "xi_R",
            "Rb",
            "Rs",
            "As",
            "Asw",
            "intermediate_values",
            "source_clause",
        }
    )


def test_result_summary_reads_validated_zip_not_mutable_workflow_report(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    input_data = parse_form_values(_form_values())
    output_dir = tmp_path / "zip-source-run"
    result = run_standalone_beam_case(input_data, output_dir)
    local_report = output_dir / "workflow" / "deterministic_report" / "report.json"
    assert local_report.is_file()
    local_report.write_text('{"unsafe": true}\n', encoding="utf-8")

    summary = load_gui_result_summary(result, output_dir, input_data)

    assert "6D14" in summary_as_text(summary)


def test_result_summary_rejects_tampered_public_report(tmp_path, monkeypatch):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    input_data = parse_form_values(_form_values())
    output_dir = tmp_path / "summary-safety-tamper"
    result = run_standalone_beam_case(input_data, output_dir)
    bundle = Path(result.report_zip_path or "")

    def mutate(payloads):
        report = payloads["deterministic_report/report.json"]
        report["project_use"] = True
        report["report"]["project_use"] = True
        report["report"]["protocol"]["project_use"] = True

    _rewrite_review_bundle_json(bundle, mutate)

    with pytest.raises(ValueError, match="защитную проверку"):
        load_gui_result_summary(result, output_dir, input_data)


def test_result_summary_rejects_bundle_input_not_matching_current_run(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    input_data = parse_form_values(_form_values())
    output_dir = tmp_path / "summary-input-tamper"
    result = run_standalone_beam_case(input_data, output_dir)
    bundle = Path(result.report_zip_path or "")

    def mutate(payloads):
        payloads["standalone_input.json"]["b_mm"] = 301.0

    _rewrite_review_bundle_json(bundle, mutate)
    assert verify_gui_result(result, output_dir) == ()

    with pytest.raises(ValueError, match="не совпадают"):
        load_gui_result_summary(result, output_dir, input_data)


def test_result_summary_rejects_overflowing_bundle_number_fail_closed(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    input_data = parse_form_values(_form_values())
    output_dir = tmp_path / "summary-overflow-tamper"
    result = run_standalone_beam_case(input_data, output_dir)
    bundle = Path(result.report_zip_path or "")

    def mutate(payloads):
        payloads["standalone_input.json"]["b_mm"] = 10**1000

    _rewrite_review_bundle_json(bundle, mutate)

    with pytest.raises(ValueError, match="конечным числом"):
        load_gui_result_summary(result, output_dir, input_data)


def test_gui_json_reader_rejects_duplicate_object_keys(tmp_path):
    archive_path = tmp_path / "duplicate-key.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("payload.json", '{"field": 1, "field": 2}')

    with (
        zipfile.ZipFile(archive_path, "r") as archive,
        pytest.raises(ValueError, match="повторяющийся ключ"),
    ):
        gui_logic_module._read_gui_json_member(archive, "payload.json")


def test_result_summary_rejects_bundle_digest_change_during_read(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    input_data = parse_form_values(_form_values())
    output_dir = tmp_path / "summary-digest-change"
    result = run_standalone_beam_case(input_data, output_dir)
    digests = iter(("a" * 64, "b" * 64))
    monkeypatch.setattr(gui_logic_module, "_file_sha256", lambda _path: next(digests))

    with pytest.raises(ValueError, match="изменился во время чтения"):
        load_gui_result_summary(result, output_dir, input_data)


def test_result_summary_binds_hidden_selection_defaults(tmp_path, monkeypatch):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    input_data = parse_form_values(_form_values())
    output_dir = tmp_path / "summary-selection-default-tamper"
    result = run_standalone_beam_case(input_data, output_dir)
    bundle = Path(result.report_zip_path or "")

    def mutate(payloads):
        report = payloads["deterministic_report/report.json"]
        report["input_data"]["main_bar_counts"] = [99]
        report["report"]["input_data"]["main_bar_counts"] = [99]

    _rewrite_review_bundle_json(bundle, mutate)
    assert verify_gui_result(result, output_dir) == ()

    with pytest.raises(ValueError, match="Полный набор исходных данных"):
        load_gui_result_summary(result, output_dir, input_data)


def test_result_summary_rejects_self_consistent_arbitrary_scheme_text(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    input_data = parse_form_values(_form_values())
    output_dir = tmp_path / "summary-scheme-tamper"
    result = run_standalone_beam_case(input_data, output_dir)
    bundle = Path(result.report_zip_path or "")

    def mutate(payloads):
        report = payloads["deterministic_report/report.json"]
        unsafe_scheme = "Mult=123; arbitrary"
        report["reinforcement"]["longitudinal"]["scheme"] = unsafe_scheme
        report["report"]["reinforcement"]["longitudinal"]["scheme"] = unsafe_scheme
        report["geometry"]["selected_longitudinal_scheme"] = unsafe_scheme
        report["report"]["geometry"]["selected_longitudinal_scheme"] = unsafe_scheme
        report["report"]["protocol"]["reinforcement"]["main"] = unsafe_scheme

    _rewrite_review_bundle_json(bundle, mutate)
    assert verify_gui_result(result, output_dir) == ()

    with pytest.raises(ValueError, match="scheme"):
        load_gui_result_summary(result, output_dir, input_data)


def test_result_summary_rejects_suppressed_bending_values_at_any_depth(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    input_data = parse_form_values(_form_values())
    output_dir = tmp_path / "summary-bending-intermediate-tamper"
    result = run_standalone_beam_case(input_data, output_dir)
    bundle = Path(result.report_zip_path or "")

    def mutate(payloads):
        report = payloads["deterministic_report/report.json"]
        for checks in (
            report["checks"],
            report["report"]["checks"],
            report["report"]["protocol"]["checks"],
        ):
            checks["bending"]["intermediate_values"]["Mult"] = 123.0

    _rewrite_review_bundle_json(bundle, mutate)
    assert verify_gui_result(result, output_dir) == ()

    with pytest.raises(ValueError, match="подавленную величину"):
        load_gui_result_summary(result, output_dir, input_data)


def test_result_summary_rejects_check_status_disagreement_with_protocol(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    input_data = parse_form_values(_form_values())
    output_dir = tmp_path / "summary-check-tamper"
    result = run_standalone_beam_case(input_data, output_dir)
    bundle = Path(result.report_zip_path or "")

    def mutate(payloads):
        report = payloads["deterministic_report/report.json"]
        report["report"]["protocol"]["checks"]["shear"]["status"] = "fail"

    _rewrite_review_bundle_json(bundle, mutate)
    assert verify_gui_result(result, output_dir) == ()

    with pytest.raises(ValueError, match="расходятся"):
        load_gui_result_summary(result, output_dir, input_data)


def test_result_action_revalidates_bundle_binding_after_display(tmp_path, monkeypatch):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    input_data = parse_form_values(_form_values())
    output_dir = tmp_path / "summary-post-display-tamper"
    result = run_standalone_beam_case(input_data, output_dir)
    original_summary = load_gui_result_summary(result, output_dir, input_data)
    bundle = Path(result.report_zip_path or "")

    def mutate(payloads):
        payloads["standalone_input.json"]["b_mm"] = 301.0

    _rewrite_review_bundle_json(bundle, mutate)

    app = object.__new__(EngineerGui)
    app._current_result = result
    app._current_output_dir = output_dir
    app._current_input = input_data
    app._current_summary = original_summary
    app._form_values = lambda: _form_values()
    invalidations = []
    app._invalidate_action = lambda title, errors: invalidations.append((title, errors))

    current = EngineerGui._validated_current_result(app, "Действие заблокировано")

    assert current is None
    assert invalidations
    assert "не совпадают" in " ".join(invalidations[0][1])


def test_result_summary_never_turns_local_pass_into_approval(tmp_path, monkeypatch):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)
    input_data = parse_form_values(_form_values())
    output_dir = tmp_path / "summary-wording"
    result = run_standalone_beam_case(input_data, output_dir)

    visible = summary_as_text(load_gui_result_summary(result, output_dir, input_data))
    lowered = visible.casefold()

    assert "локальная техническая проверка: pass" in lowered
    assert "не является проектным допуском" in lowered
    assert "требуется инженерная проверка" in lowered
    assert "расчёт утверждён" not in lowered
    assert "разрешено проектное применение" not in lowered
    assert "соответствует нормам" not in lowered


@pytest.mark.parametrize("tension_face", ("local_y_min", "local_y_max"))
def test_technical_diagram_model_echoes_only_validated_input(tension_face):
    input_data = parse_form_values(_form_values(tension_face=tension_face))

    diagram = build_diagram_model(input_data)

    assert asdict(diagram) == {
        "b_mm": 300.0,
        "h_mm": 500.0,
        "cover_mm": 32.0,
        "stirrup_diameter_mm": 8.0,
        "moment_kNm": 150.5,
        "shear_kN": 80.25,
        "tension_face": tension_face,
    }


def test_canvas_wording_marks_sketch_as_conditional_and_not_a_drawing():
    source = Path("src/sp63_core/standalone/gui.py").read_text(encoding="utf-8")

    assert "УСЛОВНАЯ СХЕМА ИСХОДНЫХ ДАННЫХ — НЕ В МАСШТАБЕ" in source
    assert "Не является рабочим чертежом, схемой армирования" in source
    assert "Ориентация local_y_min/local_y_max в реальном элементе не задана" in source
    assert "Знак и направление усилий этой схемой не задаются" in source
