"""Headless logic for the research-only standalone engineer interface.

This module contains no calculation formulas.  It converts text fields to the
existing public standalone DTO, delegates engineering validation to the
existing adapter, and fail-closes links returned to the desktop view.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import zipfile
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime
from math import isfinite
from pathlib import Path
from uuid import uuid4

from sp63_core.standalone import (
    StandaloneBeamInput,
    StandaloneRunResult,
    adapt_standalone_beam_input,
    validate_standalone_index,
    validate_standalone_review_bundle,
)

FORM_FIELDS = (
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
)

NUMERIC_FIELDS = (
    "b_mm",
    "h_mm",
    "cover_mm",
    "stirrup_diameter_mm",
    "moment_kNm",
    "shear_kN",
)

FIELD_LABELS_RU = {
    "case_id": "Идентификатор расчёта",
    "b_mm": "Ширина сечения b",
    "h_mm": "Высота сечения h",
    "cover_mm": "Расстояние до наружной поверхности хомута",
    "stirrup_diameter_mm": "Диаметр хомута",
    "concrete_class": "Класс бетона",
    "longitudinal_rebar_class": "Класс продольной арматуры",
    "stirrup_rebar_class": "Класс поперечной арматуры",
    "moment_kNm": "Модуль изгибающего момента |M|",
    "shear_kN": "Модуль поперечной силы |Q|",
    "tension_face": "Растянутая грань",
}


@dataclass(frozen=True, slots=True)
class GuiStatusView:
    """Safety-preserving Russian presentation of a standalone result."""

    title: str
    tone: str
    overall: str
    preflight: str
    calculation: str
    evidence: str
    project_use_text: str
    review_text: str
    details: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GuiResultSummary:
    """Whitelisted presentation extracted from one validated public review ZIP."""

    input_rows: tuple[tuple[str, str], ...]
    status_rows: tuple[tuple[str, str], ...]
    proposal_rows: tuple[tuple[str, str], ...]
    unchecked_lines: tuple[str, ...]
    safety_lines: tuple[str, ...]
    outside_applicability: bool


@dataclass(frozen=True, slots=True)
class GuiDiagramModel:
    """Exact validated input values used by the non-engineering canvas sketch."""

    b_mm: float
    h_mm: float
    cover_mm: float
    stirrup_diameter_mm: float
    moment_kNm: float
    shear_kN: float
    tension_face: str


_GUI_JSON_MEMBER_LIMIT = 2 * 1024 * 1024
_SAFETY_VALUES = {
    "status_scope": "public",
    "completeness_status": "incomplete",
    "evidence_status": "needs_engineer_review",
    "project_use_status": "prohibited",
    "project_use": False,
    "requires_engineer_review": True,
}
_REPORT_FIELDS = {
    "checks",
    "command",
    "completeness_status",
    "evidence_status",
    "geometry",
    "input_data",
    "limitations",
    "materials",
    "overall_status",
    "project_use",
    "project_use_status",
    "reinforcement",
    "report",
    "report_type",
    "requires_engineer_review",
    "serviceability_status",
    "source",
    "status",
    "status_scope",
    "strength_status",
    "warnings",
}
_NESTED_REPORT_FIELDS = (_REPORT_FIELDS - {"command", "source", "report"}) | {"protocol"}
_PROTOCOL_FIELDS = _NESTED_REPORT_FIELDS - {"limitations", "protocol", "report_type"}


def parse_decimal(text: object, field_label: str) -> float:
    """Parse one finite decimal using either comma or dot, never guessing groups."""
    if isinstance(text, bool):
        raise ValueError(f"Поле «{field_label}» должно быть числом.")
    raw = str(text).strip()
    if not raw:
        raise ValueError(f"Заполните поле «{field_label}».")
    if "," in raw and "." in raw:
        raise ValueError(
            f"В поле «{field_label}» используйте только один десятичный разделитель."
        )
    try:
        value = float(raw.replace(",", "."))
    except ValueError as exc:
        raise ValueError(f"Поле «{field_label}» должно быть числом.") from exc
    if not isfinite(value):
        raise ValueError(f"Поле «{field_label}» должно содержать конечное число.")
    return value


def parse_form_values(values: Mapping[str, object]) -> StandaloneBeamInput:
    """Build and validate the exact existing eleven-field standalone DTO."""
    unknown = sorted(set(values) - set(FORM_FIELDS))
    if unknown:
        raise ValueError("Интерфейс получил неподдерживаемые поля: " + ", ".join(unknown))
    missing = [field for field in FORM_FIELDS if field not in values]
    if missing:
        labels = ", ".join(FIELD_LABELS_RU[field] for field in missing)
        raise ValueError(f"Не заполнены обязательные поля: {labels}.")

    case_id = str(values["case_id"]).strip()
    if not case_id:
        raise ValueError("Заполните поле «Идентификатор расчёта».")

    numbers = {
        field: parse_decimal(values[field], FIELD_LABELS_RU[field])
        for field in NUMERIC_FIELDS
    }
    input_data = StandaloneBeamInput(
        case_id=case_id,
        b_mm=numbers["b_mm"],
        h_mm=numbers["h_mm"],
        cover_mm=numbers["cover_mm"],
        stirrup_diameter_mm=numbers["stirrup_diameter_mm"],
        concrete_class=str(values["concrete_class"]).strip(),
        longitudinal_rebar_class=str(values["longitudinal_rebar_class"]).strip(),
        stirrup_rebar_class=str(values["stirrup_rebar_class"]).strip(),
        moment_kNm=numbers["moment_kNm"],
        shear_kN=numbers["shear_kN"],
        tension_face=str(values["tension_face"]).strip(),
    )
    try:
        adapt_standalone_beam_input(input_data)
    except (TypeError, ValueError) as exc:
        raise ValueError(_translate_backend_validation(str(exc))) from exc
    return input_data


def next_output_dir(
    root: Path,
    case_id: str | None = None,
    now: datetime | None = None,
) -> Path:
    """Return a fresh opaque run directory below ``root`` without creating it.

    ``case_id`` is intentionally ignored so identifiers, personal data, path
    separators, and Windows reserved names never become filesystem names.
    """
    del case_id
    output_root = Path(root).resolve()
    timestamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    return output_root / f"run-{timestamp}-{uuid4().hex[:10]}"


def status_view_model(result: StandaloneRunResult) -> GuiStatusView:
    """Translate backend states without turning a local pass into approval."""
    if result.status == "fail":
        title = "Расчётный маршрут не выполнен"
        tone = "danger"
    elif (
        result.status == "outside_applicability"
        or result.calculation_status == "outside_applicability"
    ):
        title = (
            "Диагностический пакет сформирован; результат вне подтверждённой "
            "области применимости"
        )
        tone = "danger"
    elif result.status == "review_required":
        title = "Сформирован диагностический пакет; требуется инженерная проверка"
        tone = "warning"
    else:
        title = "Расчётный маршрут не выполнен"
        tone = "danger"

    overall = {
        "review_required": "Общий статус: требуется инженерная проверка (review_required)",
        "outside_applicability": (
            "Общий статус: вне подтверждённой области применимости "
            "(outside_applicability)"
        ),
        "fail": "Общий статус: расчётный маршрут не выполнен (fail)",
    }.get(result.status, f"Общий статус: неподдерживаемое значение ({result.status})")
    preflight = {
        "pass": "Исходные данные прошли только техническую проверку (pass)",
        "fail": "Техническая проверка исходных данных не пройдена (fail)",
        "not_run": "Техническая проверка не выполнялась (not_run)",
    }.get(result.preflight_status, f"Технический статус: {result.preflight_status}")
    calculation = {
        "outside_applicability": (
            "Расчёт: вне подтверждённой области применимости (outside_applicability)"
        ),
        "review_required": "Расчёт: требуется инженерная проверка (review_required)",
        "fail": "Расчётный маршрут не выполнен (fail)",
        "not_run": "Расчётный маршрут не запускался (not_run)",
        "pass": (
            "Локальная техническая проверка выполнена (pass); это не проектный допуск"
        ),
    }.get(result.calculation_status, f"Статус маршрута: {result.calculation_status}")
    evidence = {
        "needs_engineer_review": (
            "Инженерные подтверждения требуются (needs_engineer_review)"
        ),
        "fail": "Инженерные подтверждения не приняты (fail)",
        "not_run": "Проверка подтверждений не выполнялась (not_run)",
        "pass": (
            "Локальная проверка подтверждений выполнена (pass); требуется "
            "инженерная рецензия"
        ),
    }.get(result.evidence_status, f"Статус подтверждений: {result.evidence_status}")
    details = tuple(
        _translate_result_detail(message)
        for message in (*result.errors, *result.warnings)
    )
    return GuiStatusView(
        title=title,
        tone=tone,
        overall=overall,
        preflight=preflight,
        calculation=calculation,
        evidence=evidence,
        project_use_text="Применение в проекте ЗАПРЕЩЕНО (project_use=false)",
        review_text=(
            "Требуется инженерная проверка; подбор арматуры — только диагностическое "
            "предложение"
        ),
        details=details,
    )


def build_diagram_model(input_data: StandaloneBeamInput) -> GuiDiagramModel:
    """Echo validated user units for a conditional, explicitly non-scale sketch."""
    adapt_standalone_beam_input(input_data)
    return GuiDiagramModel(
        b_mm=float(input_data.b_mm),
        h_mm=float(input_data.h_mm),
        cover_mm=float(input_data.cover_mm),
        stirrup_diameter_mm=float(input_data.stirrup_diameter_mm),
        moment_kNm=float(input_data.moment_kNm),
        shear_kN=float(input_data.shear_kN),
        tension_face=input_data.tension_face,
    )


def load_gui_result_summary(
    result: StandaloneRunResult,
    output_dir: Path,
    expected_input: StandaloneBeamInput,
) -> GuiResultSummary:
    """Load only whitelisted fields from the validated public review package.

    No result is read from the mutable workflow directory.  The public ZIP is
    validated before and after extraction, and every displayed input is bound
    to the exact DTO used for the current GUI run.
    """
    gate_errors = verify_gui_result(result, output_dir)
    if gate_errors:
        raise ValueError("Результат не прошёл защитную проверку: " + "; ".join(gate_errors))
    if not result.report_zip_path:
        raise ValueError("В результате отсутствует публичный пакет для рецензента.")
    try:
        bundle_path = Path(result.report_zip_path).resolve(strict=True)
    except OSError as exc:
        raise ValueError("Публичный пакет результата не найден.") from exc
    return load_gui_result_summary_from_bundle(result, bundle_path, expected_input)


def load_gui_result_summary_from_bundle(
    result: StandaloneRunResult,
    bundle_path: Path,
    expected_input: StandaloneBeamInput,
) -> GuiResultSummary:
    """Load a summary from one immutable-by-digest validated bundle snapshot."""
    bundle_path = Path(bundle_path)
    pre_read_errors = verify_review_bundle(result, bundle_path)
    if pre_read_errors:
        raise ValueError(
            "Публичный пакет не прошёл защитную проверку: " + "; ".join(pre_read_errors)
        )

    try:
        digest_before = _file_sha256(bundle_path)
        with zipfile.ZipFile(bundle_path, "r") as archive:
            input_payload = _read_gui_json_member(archive, "standalone_input.json")
            canonical_payload = _read_gui_json_member(archive, "canonical_input.json")
            report_payload = _read_gui_json_member(
                archive,
                "deterministic_report/report.json",
            )
    except (OSError, KeyError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        raise ValueError("Публичный пакет результата не удалось прочитать.") from exc

    post_read_errors = verify_review_bundle(result, bundle_path)
    try:
        digest_after = _file_sha256(bundle_path)
    except OSError as exc:
        raise ValueError("Публичный пакет исчез во время чтения.") from exc
    if post_read_errors or digest_after != digest_before:
        raise ValueError(
            "Публичный пакет изменился во время чтения: "
            + "; ".join(post_read_errors or ("SHA-256 файла изменился",))
        )

    normalized_input = _validated_input_payload(input_payload)
    expected_payload = _normalized_expected_input(expected_input)
    if normalized_input != expected_payload:
        raise ValueError(
            "Исходные данные в публичном пакете не совпадают с текущим запуском GUI."
        )
    if result.case_id != expected_payload["case_id"]:
        raise ValueError("Идентификатор результата не совпадает с текущими исходными данными.")

    canonical = adapt_standalone_beam_input(expected_input)
    expected_canonical = _canonical_input_payload(canonical)
    if not _json_exact_equal(canonical_payload, expected_canonical):
        raise ValueError("Канонические данные в пакете не совпадают с текущим запуском GUI.")

    report = _require_mapping(report_payload, "верхнеуровневый публичный отчёт")
    nested = _require_mapping(report.get("report"), "вложенный публичный отчёт")
    protocol = _require_mapping(nested.get("protocol"), "публичный протокол")
    _require_exact_keys(report, _REPORT_FIELDS, "верхнеуровневый публичный отчёт")
    _require_exact_keys(nested, _NESTED_REPORT_FIELDS, "вложенный публичный отчёт")
    _require_exact_keys(protocol, _PROTOCOL_FIELDS, "публичный протокол")
    _reject_diagnostic_keys(report)
    _require_exact(report, "command", "engineering-workflow deterministic-report")
    _require_exact(report, "source", "input_json")
    _require_exact(report, "report_type", "rectangular_design_calculation_report")
    _require_exact(nested, "report_type", "rectangular_design_calculation_report")
    for label, payload in (
        ("верхнеуровневый отчёт", report),
        ("вложенный отчёт", nested),
        ("протокол", protocol),
    ):
        for field, expected in _SAFETY_VALUES.items():
            _require_exact(payload, field, expected, label=label)

    for field in ("input_data", "geometry", "reinforcement", "checks"):
        if not _json_exact_equal(report.get(field), nested.get(field)):
            raise ValueError(
                f"Поле {field} расходится между копиями публичного отчёта."
            )
    for field in ("status", "strength_status", "serviceability_status", "overall_status"):
        top_value = _require_string(report, field, "верхнеуровневый отчёт")
        if _require_string(nested, field, "вложенный отчёт") != top_value:
            raise ValueError(f"Статус {field} расходится между копиями отчёта.")
        if _require_string(protocol, field, "протокол") != top_value:
            raise ValueError(f"Статус {field} расходится с публичным протоколом.")

    report_status = _require_allowed_status(
        report,
        "status",
        {"outside_applicability"},
    )
    strength_status = _require_allowed_status(
        report,
        "strength_status",
        {"outside_applicability"},
    )
    serviceability_status = _require_allowed_status(
        report,
        "serviceability_status",
        {"not_checked"},
    )
    _require_exact(report, "overall_status", report_status)
    if result.calculation_status != report_status:
        raise ValueError("Статус текущего запуска не совпадает с публичным отчётом.")

    report_input = _require_mapping(report.get("input_data"), "исходные данные отчёта")
    protocol_input = _require_mapping(protocol.get("input_data"), "исходные данные протокола")
    expected_report_input = _json_compatible(asdict(canonical))
    if not _json_exact_equal(report_input, expected_report_input):
        raise ValueError("Полный набор исходных данных отчёта не соответствует текущему запуску.")
    for field, expected in expected_report_input.items():
        _require_exact(report_input, field, expected, label="исходные данные отчёта")
    for field in (
        "M",
        "Q",
        "local_axes_id",
        "moment_axis",
        "tension_face",
        "load_duration",
        "Mser",
        "check_cracks",
        "check_crack_width",
        "check_deflection",
    ):
        _require_exact(
            protocol_input,
            field,
            expected_report_input[field],
            label="исходные данные протокола",
        )
    _require_exact(
        protocol_input,
        "moment_value_semantics",
        "non_negative_magnitude",
        label="исходные данные протокола",
    )

    checks = _require_mapping(report.get("checks"), "публичные проверки")
    protocol_checks = _require_mapping(protocol.get("checks"), "проверки протокола")
    if set(checks) != {"bending", "shear"}:
        raise ValueError("Набор публичных проверок не соответствует автономному маршруту.")
    if not _json_exact_equal(checks, protocol_checks):
        raise ValueError("Публичные проверки расходятся с проверками протокола.")
    bending = _require_mapping(checks.get("bending"), "проверка изгиба")
    shear = _require_mapping(checks.get("shear"), "проверка поперечной силы")
    bending_status = _require_allowed_status(
        bending,
        "status",
        {"outside_applicability"},
    )
    _require_exact(bending, "public_status", bending_status, label="проверка изгиба")
    _require_exact(bending, "status_scope", "public", label="проверка изгиба")
    _require_exact(bending, "Mult", None, label="проверка изгиба")
    _require_exact(bending, "utilization", None, label="проверка изгиба")
    _reject_forbidden_bending_intermediate(bending.get("intermediate_values"))
    _require_exact(bending, "capacity_applicable", False, label="проверка изгиба")
    _require_exact(
        bending,
        "capacity_publication_allowed",
        False,
        label="проверка изгиба",
    )
    _require_exact(bending, "clause_8_1_3_status", "not_checked", label="проверка изгиба")
    _require_exact(
        bending,
        "clause_8_1_3_decision_status",
        "OPEN_QUESTION",
        label="проверка изгиба",
    )
    shear_status = _require_allowed_status(
        shear,
        "status",
        {"pass"},
    )

    geometry = _require_mapping(report.get("geometry"), "геометрия отчёта")
    protocol_geometry = _require_mapping(protocol.get("geometry"), "геометрия протокола")
    for field in (
        "b",
        "h",
        "cover",
        "stirrup_diameter_for_geometry",
        "local_axes_id",
        "moment_axis",
        "tension_face",
    ):
        _require_exact(
            geometry,
            field,
            expected_report_input[field],
            label="геометрия отчёта",
        )
        _require_exact(
            protocol_geometry,
            field,
            expected_report_input[field],
            label="геометрия протокола",
        )

    reinforcement = _require_mapping(report.get("reinforcement"), "подбор арматуры")
    protocol_reinforcement = _require_mapping(
        protocol.get("reinforcement"),
        "подбор арматуры протокола",
    )
    longitudinal = _require_mapping(reinforcement.get("longitudinal"), "продольная арматура")
    transverse = _require_mapping(reinforcement.get("transverse"), "поперечная арматура")
    longitudinal_scheme = _longitudinal_proposal_text(longitudinal)
    transverse_scheme = _transverse_proposal_text(transverse)
    _require_exact(
        protocol_reinforcement,
        "main",
        _require_string(longitudinal, "scheme", "продольная арматура"),
        label="подбор арматуры протокола",
    )
    _require_exact(
        geometry,
        "selected_longitudinal_scheme",
        longitudinal["scheme"],
        label="геометрия отчёта",
    )
    _require_exact(
        protocol_reinforcement,
        "stirrups",
        _require_string(transverse, "scheme", "поперечная арматура"),
        label="подбор арматуры протокола",
    )
    _require_exact(
        geometry,
        "selected_transverse_scheme",
        transverse["scheme"],
        label="геометрия отчёта",
    )

    input_rows = (
        ("Идентификатор", str(expected_payload["case_id"])),
        (
            "Сечение b × h",
            f"{_format_gui_number(expected_input.b_mm)} × "
            f"{_format_gui_number(expected_input.h_mm)} мм",
        ),
        (
            "cover",
            f"{_format_gui_number(expected_input.cover_mm)} мм до наружной поверхности хомута",
        ),
        (
            "Диаметр хомута для геометрии",
            f"{_format_gui_number(expected_input.stirrup_diameter_mm)} мм",
        ),
        (
            "Материалы",
            f"бетон {canonical.concrete_class}; продольная {canonical.longitudinal_rebar_class}; "
            f"поперечная {canonical.stirrup_rebar_class}",
        ),
        (
            "Введённые модули усилий",
            f"|M| = {_format_gui_number(expected_input.moment_kNm)} кН·м; "
            f"|Q| = {_format_gui_number(expected_input.shear_kN)} кН",
        ),
        ("Растянутая грань", expected_input.tension_face),
        ("Локальная ось момента", str(canonical.moment_axis)),
    )
    status_rows = (
        ("Общий статус", _public_status_text(report_status, "overall")),
        ("Прочность", _public_status_text(strength_status, "strength")),
        ("Изгиб", _public_status_text(bending_status, "bending")),
        ("Поперечная сила", _public_status_text(shear_status, "shear")),
        ("Предельные состояния II группы", _public_status_text(serviceability_status, "sls")),
        ("Полнота", "Неполный результат (incomplete)"),
        ("Подтверждения", "Требуется инженерная проверка (needs_engineer_review)"),
    )
    return GuiResultSummary(
        input_rows=input_rows,
        status_rows=status_rows,
        proposal_rows=(
            ("Продольная арматура", longitudinal_scheme),
            ("Поперечная арматура", transverse_scheme),
        ),
        unchecked_lines=(
            "Трещинообразование не проверялось.",
            "Ширина раскрытия трещин не проверялась.",
            "Прогиб не проверялся.",
            "Размещение, анкеровка и физическое сопоставление локальных граней не подтверждены.",
        ),
        safety_lines=(
            "project_use=false — применение в проекте запрещено.",
            "requires_engineer_review=true — требуется инженерная проверка.",
            "Подбор арматуры: diagnostic_only — только диагностическое предложение.",
            "Проверена целостность файлов; корректность расчёта этим не подтверждается.",
            "Изгибная несущая способность и её коэффициент использования не публикуются.",
        ),
        outside_applicability=(
            "outside_applicability"
            in {report_status, strength_status, bending_status}
        ),
    )


def summary_as_text(summary: GuiResultSummary) -> str:
    """Return a copyable safety-labelled rendering without adding calculations."""
    lines = ["СВОДКА ПРОВЕРЕННОГО ДИАГНОСТИЧЕСКОГО ПАКЕТА", ""]
    for heading, rows in (
        ("ИСХОДНЫЕ ДАННЫЕ", summary.input_rows),
        ("ПУБЛИЧНЫЕ СТАТУСЫ", summary.status_rows),
        ("ДИАГНОСТИЧЕСКИЕ ПРЕДЛОЖЕНИЯ", summary.proposal_rows),
    ):
        lines.append(heading)
        lines.extend(f"{label}: {value}" for label, value in rows)
        lines.append("")
    lines.append("НЕПРОВЕРЕННЫЕ УСЛОВИЯ")
    lines.extend(f"• {line}" for line in summary.unchecked_lines)
    lines.append("")
    lines.append("ОБЯЗАТЕЛЬНЫЕ ОГРАНИЧЕНИЯ")
    lines.extend(f"• {line}" for line in summary.safety_lines)
    return "\n".join(lines).rstrip() + "\n"


def verify_gui_result(
    result: StandaloneRunResult,
    output_dir: Path,
) -> tuple[str, ...]:
    """Fail-close report actions unless the public result contract is safe."""
    errors: list[str] = []
    if result.status not in ("review_required", "outside_applicability"):
        errors.append(
            f"Общий статус {result.status} не разрешает открывать или передавать результат."
        )
    if result.project_use is not False or result.project_use_status != "prohibited":
        errors.append("Нарушен обязательный запрет project_use=false.")
    if result.requires_engineer_review is not True:
        errors.append("В результате отсутствует обязательная инженерная проверка.")
    if result.ml_included is not False or result.ml_is_advisory_only is not True:
        errors.append("Нарушены ограничения на использование ML.")
    if result.reinforcement_selection_status != "diagnostic_only":
        errors.append("Статус подбора арматуры не является diagnostic_only.")
    if result.element_type != "rectangular_beam":
        errors.append("Результат относится не к прямоугольной балке.")
    if result.load_duration != "short":
        errors.append("Результат относится не к кратковременному маршруту.")
    if result.status_scope != "public":
        errors.append("Результат не имеет обязательную публичную область статуса.")
    if result.completeness_status != "incomplete":
        errors.append("Результат не имеет обязательный статус incomplete.")
    if result.errors:
        errors.append("Расчётный маршрут вернул ошибки.")

    root = Path(output_dir).resolve()
    required_paths = {
        "верхнеуровневый HTML-отчёт": result.report_index_path,
        "архив для инженерной рецензии": result.report_zip_path,
    }
    safe_paths: dict[str, Path] = {}
    for label, raw_path in required_paths.items():
        if not raw_path:
            errors.append(f"Отсутствует {label}.")
            continue
        path = Path(raw_path)
        try:
            resolved = path.resolve(strict=True)
        except OSError:
            errors.append(f"Не найден {label}.")
            continue
        if not resolved.is_file():
            errors.append(f"{label.capitalize()} не является файлом.")
            continue
        if not resolved.is_relative_to(root):
            errors.append(f"{label.capitalize()} находится вне каталога текущего запуска.")
            continue
        if _path_has_symlink(path, stop=root):
            errors.append(f"{label.capitalize()} проходит через символическую ссылку.")
            continue
        safe_paths[label] = resolved

    if result.report_index_path and Path(result.report_index_path).name != "standalone_index.html":
        errors.append("Выбран не верхнеуровневый standalone_index.html.")
    safe_review_bundle = safe_paths.get("архив для инженерной рецензии")
    safe_index = safe_paths.get("верхнеуровневый HTML-отчёт")
    if safe_index is not None:
        errors.extend(
            "Верхнеуровневый отчёт не прошёл проверку: " + error
            for error in validate_standalone_index(
                safe_index,
                expected_result=result,
            )
        )
    if (
        result.report_zip_path
        and Path(result.report_zip_path).name != "standalone_review_bundle.zip"
    ):
        errors.append("Выбран не публичный standalone_review_bundle.zip.")
    if (
        result.report_zip_path
        and Path(result.report_zip_path).name == "standalone_review_bundle.zip"
        and safe_review_bundle is not None
    ):
        errors.extend(
            "Архив для рецензента не прошёл проверку: " + error
            for error in verify_review_bundle(result, safe_review_bundle)
        )
    return tuple(dict.fromkeys(errors))


def verify_review_bundle(
    result: StandaloneRunResult,
    bundle_path: Path,
) -> tuple[str, ...]:
    """Revalidate one copied or in-place public bundle against the current run."""
    expected_build_id, errors = _expected_build_identity()
    validation_errors = validate_standalone_review_bundle(
        Path(bundle_path),
        expected_result=result,
        expected_build_id=expected_build_id,
    )
    return tuple(dict.fromkeys((*errors, *validation_errors)))


def _path_has_symlink(path: Path, *, stop: Path) -> bool:
    current = Path(path)
    stop_resolved = Path(stop).resolve()
    while True:
        if current.is_symlink():
            return True
        if current.resolve() == stop_resolved or current.parent == current:
            return False
        current = current.parent


def _expected_build_identity() -> tuple[str | None, tuple[str, ...]]:
    """Normalize the launcher identity before comparing it with the validated ZIP."""
    expected = os.environ.get("GBK_BUILD_ID")
    if expected in (None, "source-unverified"):
        return None, ()
    match = re.fullmatch(r"wheel-sha256:([0-9a-fA-F]{64})", expected)
    if match is None:
        return None, ("Идентификатор запущенной сборки имеет недопустимый формат.",)
    return f"wheel-sha256:{match.group(1).lower()}", ()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _read_gui_json_member(archive: zipfile.ZipFile, name: str) -> dict[str, object]:
    info = archive.getinfo(name)
    if info.file_size > _GUI_JSON_MEMBER_LIMIT:
        raise ValueError(f"Файл {name} превышает допустимый размер для интерфейса.")
    raw = archive.read(info)
    if len(raw) != info.file_size:
        raise ValueError(f"Размер файла {name} изменился во время чтения.")
    payload = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_json_object_without_duplicates,
    )
    if type(payload) is not dict:
        raise ValueError(f"Файл {name} должен содержать JSON-объект.")
    return payload


def _json_object_without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, value in pairs:
        if key in payload:
            raise ValueError(f"JSON содержит повторяющийся ключ: {key}.")
        payload[key] = value
    return payload


def _json_compatible(value: object) -> object:
    if isinstance(value, dict):
        return {key: _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_compatible(item) for item in value]
    return value


def _json_exact_equal(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(actual) == set(expected) and all(
            _json_exact_equal(actual[key], item) for key, item in expected.items()
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _json_exact_equal(actual_item, expected_item)
            for actual_item, expected_item in zip(actual, expected, strict=True)
        )
    return actual == expected


def _canonical_input_payload(canonical: object) -> dict[str, object]:
    full_payload = _json_compatible(asdict(canonical))
    if not isinstance(full_payload, dict):
        raise ValueError("Канонические исходные данные имеют недопустимый тип.")
    fields = {
        "b",
        "h",
        "cover",
        "stirrup_diameter_for_geometry",
        "concrete_class",
        "longitudinal_rebar_class",
        "stirrup_rebar_class",
        "M",
        "Q",
        "local_axes_id",
        "moment_axis",
        "tension_face",
        "load_duration",
        "check_cracks",
        "check_crack_width",
        "check_deflection",
    }
    return {field: full_payload[field] for field in fields}


def _normalized_expected_input(input_data: StandaloneBeamInput) -> dict[str, object]:
    adapt_standalone_beam_input(input_data)
    payload = asdict(input_data)
    return {
        "element_type": "rectangular_beam",
        "load_duration": "short",
        "case_id": str(payload["case_id"]).strip(),
        "b_mm": float(payload["b_mm"]),
        "h_mm": float(payload["h_mm"]),
        "cover_mm": float(payload["cover_mm"]),
        "stirrup_diameter_mm": float(payload["stirrup_diameter_mm"]),
        "concrete_class": str(payload["concrete_class"]).strip().upper(),
        "longitudinal_rebar_class": str(payload["longitudinal_rebar_class"]).strip().upper(),
        "stirrup_rebar_class": str(payload["stirrup_rebar_class"]).strip().upper(),
        "moment_kNm": float(payload["moment_kNm"]),
        "shear_kN": float(payload["shear_kN"]),
        "tension_face": str(payload["tension_face"]),
    }


def _validated_input_payload(payload: Mapping[str, object]) -> dict[str, object]:
    expected_fields = set(FORM_FIELDS) | {"element_type", "load_duration"}
    if set(payload) != expected_fields:
        raise ValueError("standalone_input.json не соответствует контракту полей GUI.")
    if payload.get("element_type") != "rectangular_beam":
        raise ValueError("Публичный пакет относится не к прямоугольной балке.")
    if payload.get("load_duration") != "short":
        raise ValueError("Публичный пакет относится не к кратковременному маршруту.")
    normalized: dict[str, object] = {}
    normalized["element_type"] = "rectangular_beam"
    normalized["load_duration"] = "short"
    for field in NUMERIC_FIELDS:
        value = payload[field]
        if isinstance(value, bool) or type(value) not in (int, float):
            raise ValueError(f"Поле {field} в публичном пакете не является конечным числом.")
        try:
            numeric_value = float(value)
        except (OverflowError, ValueError) as exc:
            raise ValueError(
                f"Поле {field} в публичном пакете не является конечным числом."
            ) from exc
        if not isfinite(numeric_value):
            raise ValueError(f"Поле {field} в публичном пакете не является конечным числом.")
        normalized[field] = numeric_value
    for field in set(FORM_FIELDS) - set(NUMERIC_FIELDS):
        value = payload[field]
        if type(value) is not str:
            raise ValueError(f"Поле {field} в публичном пакете должно быть строкой.")
        normalized[field] = value
    return normalized


def _require_mapping(value: object, label: str) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{label.capitalize()} должен быть JSON-объектом.")
    return value


def _require_exact_keys(
    payload: Mapping[str, object],
    expected: set[str],
    label: str,
) -> None:
    if set(payload) != expected:
        raise ValueError(f"{label.capitalize()} содержит неподдерживаемый набор полей.")


def _require_exact(
    payload: Mapping[str, object],
    field: str,
    expected: object,
    *,
    label: str = "публичный отчёт",
) -> None:
    actual = payload.get(field)
    if type(actual) is not type(expected) or actual != expected:
        raise ValueError(f"{label.capitalize()}: поле {field} не соответствует контракту.")


def _require_string(payload: Mapping[str, object], field: str, label: str) -> str:
    value = payload.get(field)
    if type(value) is not str or not value:
        raise ValueError(f"{label.capitalize()}: поле {field} должно быть непустой строкой.")
    return value


def _require_allowed_status(
    payload: Mapping[str, object],
    field: str,
    allowed: set[str],
) -> str:
    value = _require_string(payload, field, "публичный отчёт")
    if value not in allowed:
        raise ValueError(f"Публичный статус {field}={value!r} не разрешён для показа в GUI.")
    return value


def _reject_diagnostic_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str) and key.startswith("diagnostic_"):
                raise ValueError("Публичный отчёт содержит закрытое диагностическое поле.")
            _reject_diagnostic_keys(item)
    elif isinstance(value, list):
        for item in value:
            _reject_diagnostic_keys(item)


def _reject_forbidden_bending_intermediate(value: object) -> None:
    payload = _require_mapping(value, "промежуточные данные изгиба")
    for key, item in payload.items():
        if key in {"Mult", "utilization"}:
            raise ValueError(
                "Публичный отчёт содержит подавленную величину в промежуточных данных изгиба."
            )
        if isinstance(item, (dict, list)):
            _reject_forbidden_bending_nested(item)


def _reject_forbidden_bending_nested(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"Mult", "utilization"}:
                raise ValueError(
                    "Публичный отчёт содержит подавленную величину в данных изгиба."
                )
            _reject_forbidden_bending_nested(item)
    elif isinstance(value, list):
        for item in value:
            _reject_forbidden_bending_nested(item)


def _require_positive_integer(payload: Mapping[str, object], field: str, label: str) -> int:
    value = payload.get(field)
    if type(value) is not int or value <= 0:
        raise ValueError(f"{label.capitalize()}: поле {field} должно быть положительным целым.")
    return value


def _proposal_display(scheme: str) -> str:
    return (
        f"{scheme} — диагностическое предложение программы; "
        "не является назначением арматуры"
    )


def _longitudinal_proposal_text(payload: Mapping[str, object]) -> str:
    _require_exact_keys(
        payload,
        {
            "scheme",
            "bar_count",
            "diameter",
            "As",
            "h0",
            "reinforcement_ratio_percent",
            "constructive_status",
            "layout_feasible",
            "status",
        },
        "продольная арматура",
    )
    _require_exact(payload, "status", "outside_applicability", label="продольная арматура")
    _require_exact(payload, "constructive_status", "pass", label="продольная арматура")
    _require_exact(payload, "layout_feasible", True, label="продольная арматура")
    bar_count = _require_positive_integer(payload, "bar_count", "продольная арматура")
    diameter = _require_positive_integer(payload, "diameter", "продольная арматура")
    expected_scheme = f"{bar_count}D{diameter}"
    if len(expected_scheme) > 64:
        raise ValueError("Строка схемы продольной арматуры превышает допустимую длину.")
    _require_exact(payload, "scheme", expected_scheme, label="продольная арматура")
    return _proposal_display(expected_scheme)


def _transverse_proposal_text(payload: Mapping[str, object]) -> str:
    _require_exact_keys(
        payload,
        {
            "scheme",
            "diameter",
            "Asw",
            "spacing",
            "legs",
            "constructive_status",
            "status",
        },
        "поперечная арматура",
    )
    _require_exact(payload, "status", "pass", label="поперечная арматура")
    _require_exact(payload, "constructive_status", "pass", label="поперечная арматура")
    diameter = _require_positive_integer(payload, "diameter", "поперечная арматура")
    spacing = _require_positive_integer(payload, "spacing", "поперечная арматура")
    legs = _require_positive_integer(payload, "legs", "поперечная арматура")
    expected_scheme = f"D{diameter}/{spacing}, {legs} legs"
    if len(expected_scheme) > 64:
        raise ValueError("Строка схемы поперечной арматуры превышает допустимую длину.")
    _require_exact(payload, "scheme", expected_scheme, label="поперечная арматура")
    return _proposal_display(expected_scheme)


def _public_status_text(status: str, context: str) -> str:
    if status == "outside_applicability":
        if context == "bending":
            return (
                "Вне подтверждённой области применимости "
                "(outside_applicability); несущая способность не публикуется"
            )
        return "Вне подтверждённой области применимости (outside_applicability)"
    if status == "pass" and context == "shear":
        return "Локальная техническая проверка: pass; не является проектным допуском"
    if status == "not_checked" and context == "sls":
        return "Не проверялись (not_checked)"
    if status == "review_or_fail":
        return "Требуется инженерное решение либо отказ (review_or_fail)"
    if status == "fail":
        return "Проверка не пройдена (fail)"
    raise ValueError(f"Статус {status!r} не имеет безопасного представления для GUI.")


def _format_gui_number(value: object) -> str:
    if isinstance(value, bool) or type(value) not in (int, float) or not isfinite(value):
        raise ValueError("Интерфейс получил некорректное числовое значение.")
    return f"{float(value):g}"


def _translate_result_detail(message: str) -> str:
    known = {
        (
            "Research-only rectangular-beam preview. It does not certify a design, "
            "publish bending capacity, or authorize project use."
        ): (
            "Исследовательский просмотр прямоугольной балки не сертифицирует расчёт, "
            "не публикует утверждённую несущую способность и не разрешает применение "
            "в проекте."
        ),
        (
            "Slab-strip mode is unavailable pending a separate engineering specification."
        ): "Режим полосы плиты недоступен до отдельной инженерной спецификации.",
        (
            "Any selected longitudinal or transverse reinforcement scheme and any local "
            "'pass' are diagnostic proposals only, not an approved design decision."
        ): (
            "Любая предложенная схема продольной или поперечной арматуры и любой "
            "локальный статус pass являются только диагностикой, а не утверждённым "
            "проектным решением."
        ),
        (
            "This workflow does not certify the design. Deterministic SP63 verification "
            "and engineer review are mandatory. ML, if included, is advisory-only."
        ): (
            "Маршрут не сертифицирует проектное решение. Обязательны "
            "детерминированная проверка и инженерная рецензия; ML в этом "
            "автономном маршруте не используется."
        ),
        (
            "This static index does not certify the design. Deterministic SP63 "
            "verification and engineer review are mandatory. ML, if present, is "
            "advisory-only."
        ): (
            "Статический указатель не сертифицирует проектное решение. Обязательны "
            "детерминированная проверка и инженерная рецензия."
        ),
        (
            "ML readiness outputs were not found; deterministic-only workflow index "
            "generated."
        ): (
            "Материалы готовности ML отсутствуют; сформирован только "
            "детерминированный указатель маршрута."
        ),
    }
    if message in known:
        return known[message]
    return "Техническое сообщение для рецензии: " + message


def _translate_backend_validation(message: str) -> str:
    translations = {
        "case_id must be a non-empty string": "Идентификатор расчёта не заполнен.",
        "case_id must be at most 100 characters": (
            "Идентификатор расчёта должен содержать не более 100 символов."
        ),
        "case_id must not contain control characters": (
            "Идентификатор расчёта содержит недопустимый управляющий символ."
        ),
        "cover_mm must be less than h_mm": (
            "Расстояние до наружной поверхности хомута должно быть меньше высоты h."
        ),
        "moment_kNm must be non-negative": (
            "Модуль изгибающего момента |M| не может быть отрицательным."
        ),
        "shear_kN must be non-negative": (
            "Модуль поперечной силы |Q| не может быть отрицательным."
        ),
        "tension_face must be 'local_y_min' or 'local_y_max'": (
            "Выберите растянутую грань: local_y_min или local_y_max."
        ),
    }
    if message in translations:
        return translations[message]
    field_names = {
        "b_mm": "Ширина b",
        "h_mm": "Высота h",
        "cover_mm": "Расстояние до наружной поверхности хомута",
        "stirrup_diameter_mm": "Диаметр хомута",
        "concrete_class": "Класс бетона",
        "longitudinal_rebar_class": "Класс продольной арматуры",
        "stirrup_rebar_class": "Класс поперечной арматуры",
    }
    translated = message
    for source, label in field_names.items():
        translated = translated.replace(source, label)
    translated = translated.replace("must be positive", "должно быть положительным")
    translated = translated.replace("must be one of:", "допускает только:")
    return translated
