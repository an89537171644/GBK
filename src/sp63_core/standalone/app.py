"""User-facing entry point for the standalone rectangular-beam draft MVP."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from sp63_core.standalone import StandaloneBeamInput, run_standalone_beam_case

SUPPORTED_ELEMENT_TYPE = "rectangular_beam"
SUPPORTED_LOAD_DURATION = "short"
INPUT_FIELDS = (
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
OPTIONAL_SCOPE_FIELDS = ("element_type", "load_duration")
SAFETY_NOTICE_RU = (
    "ИССЛЕДОВАТЕЛЬСКИЙ ЧЕРНОВИК: результат не предназначен для проектного применения. "
    "Обязательны детерминированная проверка и инженерная рецензия."
)


def build_parser() -> argparse.ArgumentParser:
    """Build the narrow standalone command-line interface."""
    parser = argparse.ArgumentParser(
        prog="gbk-standalone",
        description="Автономный черновой маршрут GBK для прямоугольной балки.",
    )
    parser.add_argument(
        "--input-json",
        type=Path,
        help="JSON с исходными данными балки; без параметра запускается мастер ввода.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Каталог результата (по умолчанию создаётся рядом с входным файлом).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Напечатать машинно-читаемый итоговый JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run a JSON case or the Russian interactive input wizard."""
    args = build_parser().parse_args(argv)
    try:
        if args.input_json is not None:
            input_data = load_standalone_input(args.input_json)
            output_dir = args.output_dir or _default_json_output_dir(args.input_json)
            _ensure_input_outside_output(args.input_json, output_dir)
        else:
            input_data = collect_interactive_input()
            output_dir = args.output_dir or Path.cwd() / "GBK-output" / "interactive"

        result = run_standalone_beam_case(input_data, output_dir=output_dir)
        payload = {"command": "standalone-beam", **asdict(result)}
        _print_result(payload, as_json=args.json, error=result.status == "fail")
        return 0 if result.status != "fail" else 2
    except (EOFError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        payload = _error_payload(str(exc))
        _print_result(payload, as_json=args.json, error=True)
        return 2


def load_standalone_input(path: Path) -> StandaloneBeamInput:
    """Load the deliberately narrow public input contract from JSON."""
    with Path(path).open(encoding="utf-8") as input_file:
        data = json.load(input_file, object_pairs_hook=_reject_duplicate_keys)
    if not isinstance(data, dict):
        raise ValueError("Входной JSON должен содержать один объект.")

    allowed_fields = set((*INPUT_FIELDS, *OPTIONAL_SCOPE_FIELDS))
    unknown_fields = sorted(set(data) - allowed_fields)
    if unknown_fields:
        raise ValueError("Неизвестные поля: " + ", ".join(unknown_fields))

    missing_fields = [field for field in INPUT_FIELDS if field not in data]
    if missing_fields:
        raise ValueError("Не заполнены обязательные поля: " + ", ".join(missing_fields))

    element_type = data.get("element_type", SUPPORTED_ELEMENT_TYPE)
    if element_type != SUPPORTED_ELEMENT_TYPE:
        raise ValueError(
            "В первой версии поддерживается только element_type=rectangular_beam; "
            f"получено: {element_type!r}."
        )
    load_duration = data.get("load_duration", SUPPORTED_LOAD_DURATION)
    if load_duration != SUPPORTED_LOAD_DURATION:
        raise ValueError(
            "В первой версии поддерживается только load_duration=short; "
            f"получено: {load_duration!r}."
        )

    return StandaloneBeamInput(**{field: data[field] for field in INPUT_FIELDS})


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Входной JSON содержит повторяющееся поле: {key}")
        result[key] = value
    return result


def collect_interactive_input() -> StandaloneBeamInput:
    """Collect a single beam case without exposing unsupported modes."""
    print("\nGBK — автономный черновой расчёт отдельной балки")
    print(SAFETY_NOTICE_RU)
    print("Поддерживается только прямоугольная балка и кратковременный маршрут.\n")
    print(
        "M вводится как неотрицательный модуль; знак момента не выбирает грань. "
        "Физическое сопоставление local_y_min/local_y_max должен проверить инженер.\n"
    )
    values: dict[str, Any] = {
        "case_id": _prompt("Идентификатор расчёта", "beam-001"),
        "b_mm": _prompt_float("Ширина b, мм", 300.0),
        "h_mm": _prompt_float("Высота h, мм", 500.0),
        "cover_mm": _prompt_float(
            "От грани бетона до наружной поверхности хомута cover, мм",
            32.0,
        ),
        "stirrup_diameter_mm": _prompt_float("Диаметр хомута для геометрии, мм", 8.0),
        "concrete_class": _prompt("Класс бетона", "B25"),
        "longitudinal_rebar_class": _prompt("Класс продольной арматуры", "A500"),
        "stirrup_rebar_class": _prompt("Класс поперечной арматуры", "A240"),
        "moment_kNm": _prompt_float("Изгибающий момент M, кН·м", 150.0),
        "shear_kN": _prompt_float("Поперечная сила Q, кН", 80.0),
        "tension_face": _prompt("Растянутая грань (local_y_min/local_y_max)", "local_y_min"),
    }
    return StandaloneBeamInput(**values)


def _prompt(label: str, default: str) -> str:
    value = input(f"{label} [{default}]: ").strip()
    return value or default


def _prompt_float(label: str, default: float) -> float:
    raw_value = _prompt(label, f"{default:g}").replace(",", ".")
    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(f"Поле «{label}» должно быть числом.") from exc


def _default_json_output_dir(input_path: Path) -> Path:
    return Path(input_path).resolve().parent / "output" / Path(input_path).stem


def _ensure_input_outside_output(input_path: Path, output_dir: Path) -> None:
    source = Path(input_path).resolve()
    output = Path(output_dir).resolve()
    if source == output or source.is_relative_to(output):
        raise ValueError(
            "Каталог результата не должен содержать исходный JSON. "
            "Выберите отдельный каталог результата."
        )


def _error_payload(message: str) -> dict[str, Any]:
    return {
        "command": "standalone-beam",
        "status": "fail",
        "project_use": False,
        "project_use_status": "prohibited",
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "ml_included": False,
        "reinforcement_selection_status": "diagnostic_only",
        "warnings": [SAFETY_NOTICE_RU],
        "errors": [message],
    }


def _print_result(payload: dict[str, Any], *, as_json: bool, error: bool = False) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False))
        return

    stream = sys.stderr if error else sys.stdout
    print("", file=stream)
    print(SAFETY_NOTICE_RU, file=stream)
    print(f"Статус выполнения: {payload['status']}", file=stream)
    if payload.get("preflight_status"):
        print(f"Предварительная проверка: {payload['preflight_status']}", file=stream)
    if payload.get("calculation_status"):
        print(f"Статус расчётного маршрута: {payload['calculation_status']}", file=stream)
    if payload.get("evidence_status"):
        print(f"Статус инженерных подтверждений: {payload['evidence_status']}", file=stream)
    print("project_use=false; requires_engineer_review=true", file=stream)
    print("Этот статус не является утверждением расчёта или несущей способности.", file=stream)
    if payload.get("report_index_path"):
        print(f"Отчёт: {payload['report_index_path']}", file=stream)
    if payload.get("report_zip_path"):
        print(f"Архив для передачи рецензенту: {payload['report_zip_path']}", file=stream)
    for message in payload.get("warnings", ()):
        print(f"Предупреждение: {message}", file=stream)
    for message in payload.get("errors", ()):
        print(f"Ошибка: {message}", file=stream)


if __name__ == "__main__":
    raise SystemExit(main())
