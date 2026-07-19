"""Headless logic for the research-only standalone engineer interface.

This module contains no calculation formulas.  It converts text fields to the
existing public standalone DTO, delegates engineering validation to the
existing adapter, and fail-closes links returned to the desktop view.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
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
