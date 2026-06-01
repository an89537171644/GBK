"""Input form schema and validation hints for future engineering UI wrappers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.materials.concrete import CONCRETE_CATALOG
from sp63_core.materials.rebar import (
    REBAR_CATALOG,
    STIRRUP_DIAMETERS,
)

SCHEMA_WARNING = (
    "This schema is for future UI/input forms only. It does not perform design "
    "calculations and does not approve ML for project use."
)

MANDATORY_WARNINGS = (
    SCHEMA_WARNING,
    "Deterministic SP63 checks remain mandatory.",
    "Engineer review remains mandatory.",
    "ML output is advisory-only and must not be shown as a design decision.",
    "ml_ready_for_project_use is not user-settable and must remain false.",
    "Material verification and external validation are separate engineer-review gates.",
)

VALIDATION_RULES: tuple[dict[str, Any], ...] = (
    {
        "rule_id": "positive_dimensions",
        "fields": ("b", "h", "cover", "stirrup_diameter_for_geometry"),
        "message": "Geometry dimensions must be positive values in millimetres.",
        "severity": "error",
    },
    {
        "rule_id": "effective_depth_geometry",
        "fields": ("h", "cover", "stirrup_diameter_for_geometry"),
        "message": "h must exceed cover and leave positive effective depth.",
        "severity": "error",
    },
    {
        "rule_id": "cover_less_than_h",
        "fields": ("cover", "h"),
        "message": "cover must be less than h.",
        "severity": "error",
    },
    {
        "rule_id": "span_greater_than_h",
        "fields": ("span", "h"),
        "message": "span should be greater than h when span is provided.",
        "severity": "warning",
    },
    {
        "rule_id": "nonnegative_forces",
        "fields": ("M", "Q", "Mser"),
        "message": "M, Q, and Mser must be nonnegative when provided.",
        "severity": "error",
    },
    {
        "rule_id": "service_moment_not_above_design_moment",
        "fields": ("Mser", "M"),
        "message": "Current input convention expects Mser <= M when both values are provided.",
        "severity": "warning",
    },
    {
        "rule_id": "material_classes_exist",
        "fields": ("concrete_class", "longitudinal_rebar_class", "stirrup_rebar_class"),
        "message": "Selected material classes must exist in the material catalog.",
        "severity": "error",
    },
    {
        "rule_id": "dataset_required_for_ml_readiness",
        "fields": ("include_ml_readiness", "dataset_path"),
        "message": "dataset_path is required when include_ml_readiness is true.",
        "severity": "error",
    },
    {
        "rule_id": "optional_external_csv_exists",
        "fields": ("external_validation_csv",),
        "message": "external_validation_csv must point to an existing file when provided.",
        "severity": "error",
    },
    {
        "rule_id": "optional_material_csv_exists",
        "fields": ("material_verification_csv",),
        "message": "material_verification_csv must point to an existing file when provided.",
        "severity": "error",
    },
    {
        "rule_id": "ml_ready_not_user_settable",
        "fields": (),
        "message": "ml_ready_for_project_use must not be an input field or user-settable flag.",
        "severity": "error",
    },
)


@dataclass(frozen=True)
class InputFormSchemaResult:
    """Result for the future input form schema export."""

    status: str
    schema_status: str
    output_dir: str | None
    field_count: int
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    validation_rules_count: int
    json_data: dict[str, Any]
    markdown: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_input_form_schema(
    *,
    output_dir: Path | None = None,
) -> InputFormSchemaResult:
    """Build schema metadata and validation hints for a future input form."""
    groups = _schema_groups()
    fields = [field for group in groups for field in group["fields"]]
    required_fields = tuple(field["name"] for field in fields if field.get("required") is True)
    optional_fields = tuple(field["name"] for field in fields if field.get("required") is not True)
    json_data: dict[str, Any] = {
        "schema_type": "engineering_input_form_schema",
        "status": "pass",
        "schema_status": "pass",
        "groups": groups,
        "validation_rules": list(VALIDATION_RULES),
        "mandatory_warnings": list(MANDATORY_WARNINGS),
        "required_fields": list(required_fields),
        "optional_fields": list(optional_fields),
        "field_count": len(fields),
        "validation_rules_count": len(VALIDATION_RULES),
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "ml_ready_for_project_use": False,
    }
    markdown = render_input_form_schema_markdown(json_data)
    result = InputFormSchemaResult(
        status="pass",
        schema_status="pass",
        output_dir=str(output_dir) if output_dir is not None else None,
        field_count=len(fields),
        required_fields=required_fields,
        optional_fields=optional_fields,
        validation_rules_count=len(VALIDATION_RULES),
        json_data=json_data,
        markdown=markdown,
        warnings=MANDATORY_WARNINGS,
        errors=(),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    if output_dir is not None:
        _write_schema_files(Path(output_dir), result)
    return result


def render_input_form_schema_markdown(json_data: dict[str, Any]) -> str:
    """Render input form schema metadata as Markdown."""
    lines = [
        "# Engineering Input Form Schema",
        "",
        SCHEMA_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
    ]
    for section_title, group_name in (
        ("Geometry fields", "geometry"),
        ("Material fields", "materials"),
        ("Load fields", "loads"),
        ("Serviceability check fields", "checks"),
        ("Workflow fields", "workflow"),
        ("Optional ML-readiness fields", "ml_readiness"),
    ):
        lines.extend([f"## {section_title}", ""])
        group = _group_by_name(json_data["groups"], group_name)
        lines.extend(_field_table_lines(group["fields"]))
        lines.append("")

    lines.extend(
        [
            "## Validation rules",
            "",
            *_validation_rule_lines(tuple(json_data["validation_rules"])),
            "",
            "## Mandatory warnings",
            "",
            *_bullet_lines(tuple(json_data["mandatory_warnings"])),
            "",
            "## Limitations",
            "",
            "- This schema is metadata only.",
            "- It does not validate or calculate a design by itself.",
            "- It does not implement a GUI, web server, or JavaScript calculator.",
            "- It does not change formulas, materials, or reinforcement selection.",
            "- It does not approve ML for project use.",
            "- Future UI layers must keep deterministic status and engineer review visible.",
        ]
    )
    return "\n".join(lines) + "\n"


def _schema_groups() -> list[dict[str, Any]]:
    concrete_options = tuple(sorted(CONCRETE_CATALOG))
    rebar_options = tuple(sorted(REBAR_CATALOG))
    return [
        {
            "group": "geometry",
            "title": "Geometry",
            "title_ru": "Геометрия",
            "fields": [
                _number_field(
                    "b",
                    "Section width b",
                    "Ширина сечения b",
                    "mm",
                    True,
                    300,
                    100,
                    2000,
                ),
                _number_field(
                    "h",
                    "Section height h",
                    "Высота сечения h",
                    "mm",
                    True,
                    500,
                    150,
                    3000,
                ),
                _number_field(
                    "cover",
                    "Concrete cover",
                    "Защитный слой",
                    "mm",
                    True,
                    32,
                    10,
                    150,
                ),
                _number_field(
                    "stirrup_diameter_for_geometry",
                    "Stirrup diameter for geometry",
                    "Диаметр хомута для геометрии",
                    "mm",
                    True,
                    8,
                    4,
                    32,
                    options=tuple(STIRRUP_DIAMETERS),
                ),
                _number_field("span", "Span", "Prolet", "mm", False, 6000, 500, 30000),
            ],
        },
        {
            "group": "materials",
            "title": "Materials",
            "title_ru": "Материалы",
            "fields": [
                _select_field(
                    "concrete_class",
                    "Concrete class",
                    "Класс бетона",
                    True,
                    "B25",
                    concrete_options,
                    "material_catalog",
                ),
                _select_field(
                    "longitudinal_rebar_class",
                    "Longitudinal rebar class",
                    "Класс продольной арматуры",
                    True,
                    "A500",
                    rebar_options,
                    "material_catalog",
                ),
                _select_field(
                    "stirrup_rebar_class",
                    "Stirrup rebar class",
                    "Класс поперечной арматуры",
                    True,
                    "A240",
                    rebar_options,
                    "material_catalog",
                ),
            ],
        },
        {
            "group": "loads",
            "title": "Loads and internal forces",
            "title_ru": "Нагрузки и усилия",
            "fields": [
                _number_field(
                    "M",
                    "Design bending moment",
                    "Расчётный изгибающий момент",
                    "N*mm",
                    True,
                    150000000,
                    0,
                    None,
                ),
                _number_field(
                    "Q",
                    "Design shear force",
                    "Расчётная поперечная сила",
                    "N",
                    True,
                    80000,
                    0,
                    None,
                ),
                _number_field(
                    "Mser",
                    "Service bending moment",
                    "Эксплуатационный момент",
                    "N*mm",
                    False,
                    30000000,
                    0,
                    None,
                ),
            ],
        },
        {
            "group": "checks",
            "title": "Serviceability checks",
            "title_ru": "Проверки эксплуатационной пригодности",
            "fields": [
                _boolean_field(
                    "check_cracks",
                    "Check crack formation",
                    "Проверять образование трещин",
                    False,
                    True,
                ),
                _boolean_field(
                    "check_crack_width",
                    "Check crack width",
                    "Проверять ширину раскрытия трещин",
                    False,
                    True,
                ),
                _boolean_field(
                    "check_deflection",
                    "Check deflection",
                    "Проверять прогиб",
                    False,
                    True,
                ),
                _number_field(
                    "acrc_limit",
                    "Crack width limit",
                    "Предельная ширина раскрытия трещин",
                    "mm",
                    False,
                    0.3,
                    0,
                    None,
                ),
                _number_field(
                    "deflection_limit",
                    "Explicit deflection limit",
                    "Явный предельный прогиб",
                    "mm",
                    False,
                    None,
                    0,
                    None,
                ),
                _number_field(
                    "deflection_limit_ratio",
                    "Deflection span ratio",
                    "Относительный предел прогиба",
                    "-",
                    False,
                    250,
                    1,
                    None,
                ),
                _select_field(
                    "load_duration",
                    "Load duration",
                    "Длительность нагрузки",
                    False,
                    "short",
                    ("short", "long"),
                    "design_input_options",
                ),
            ],
        },
        {
            "group": "workflow",
            "title": "Output and workflow",
            "title_ru": "Вывод и workflow",
            "fields": [
                _path_field(
                    "output_dir",
                    "Output directory",
                    "Папка вывода",
                    False,
                    "reports/engineering_workflow",
                ),
                _boolean_field(
                    "create_zip",
                    "Create ZIP archive",
                    "Создать ZIP-архив",
                    False,
                    True,
                ),
                _boolean_field(
                    "with_index",
                    "Create static index",
                    "Создать статический index",
                    False,
                    True,
                ),
                _boolean_field(
                    "include_ml_readiness",
                    "Include ML readiness",
                    "Включить ML readiness",
                    False,
                    False,
                ),
            ],
        },
        {
            "group": "ml_readiness",
            "title": "Optional ML-readiness inputs",
            "title_ru": "Дополнительные поля ML readiness",
            "fields": [
                _path_field(
                    "dataset_path",
                    "Dataset path",
                    "Путь к dataset",
                    False,
                    "data/report_dataset.jsonl",
                ),
                _path_field(
                    "external_validation_csv",
                    "External validation CSV",
                    "CSV внешней валидации",
                    False,
                    "docs/validation/samples/external_validation_filled_sample.csv",
                ),
                _path_field(
                    "material_verification_csv",
                    "Material verification CSV",
                    "CSV проверки материалов",
                    False,
                    "docs/materials/material_verification_engineer_filled.csv",
                ),
            ],
        },
    ]


def _number_field(
    name: str,
    label: str,
    label_ru: str,
    unit: str,
    required: bool,
    default: int | float | None,
    minimum: int | float | None,
    maximum: int | float | None,
    *,
    options: tuple[int, ...] | None = None,
) -> dict[str, Any]:
    field: dict[str, Any] = {
        "name": name,
        "label": label,
        "label_ru": label_ru,
        "type": "number",
        "unit": unit,
        "required": required,
        "default": default,
        "min": minimum,
        "max": maximum,
        "engineering_hint": "Use project-consistent units and verify assumptions before use.",
        "validation_message": f"{name} must satisfy the declared engineering range.",
    }
    if options is not None:
        field["options"] = list(options)
    return field


def _select_field(
    name: str,
    label: str,
    label_ru: str,
    required: bool,
    default: str,
    options: tuple[str, ...],
    options_source: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "label": label,
        "label_ru": label_ru,
        "type": "select",
        "unit": None,
        "required": required,
        "default": default,
        "options": list(options),
        "options_source": options_source,
        "example": default,
        "engineering_hint": "Material catalog values require engineer review.",
        "validation_message": f"{name} must be one of the supported catalog options.",
    }


def _boolean_field(
    name: str,
    label: str,
    label_ru: str,
    required: bool,
    default: bool,
) -> dict[str, Any]:
    return {
        "name": name,
        "label": label,
        "label_ru": label_ru,
        "type": "boolean",
        "unit": None,
        "required": required,
        "default": default,
        "engineering_hint": "Serviceability checks can produce review_required results.",
        "validation_message": f"{name} must be true or false.",
    }


def _path_field(
    name: str,
    label: str,
    label_ru: str,
    required: bool,
    example: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "label": label,
        "label_ru": label_ru,
        "type": "path",
        "unit": None,
        "required": required,
        "default": None,
        "example": example,
        "engineering_hint": "Use a local project path. Do not include private documents.",
        "validation_message": f"{name} must point to an existing file or directory when required.",
    }


def _write_schema_files(output_dir: Path, result: InputFormSchemaResult) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "input_form_schema.json").write_text(
        json.dumps(result.json_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "input_form_schema.md").write_text(result.markdown, encoding="utf-8")


def _group_by_name(groups: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for group in groups:
        if group["group"] == name:
            return group
    raise KeyError(name)


def _field_table_lines(fields: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Field | Type | Unit | Required | Default/example | Hint |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for field in fields:
        default = field.get("default")
        example = field.get("example")
        default_or_example = example if default is None and example is not None else default
        lines.append(
            "| `{name}` | {type_} | {unit} | {required} | {default} | {hint} |".format(
                name=field["name"],
                type_=field["type"],
                unit=field.get("unit") or "-",
                required=str(field["required"]).lower(),
                default="-" if default_or_example is None else default_or_example,
                hint=field["engineering_hint"],
            )
        )
    return lines


def _validation_rule_lines(rules: tuple[dict[str, Any], ...]) -> list[str]:
    lines = []
    for rule in rules:
        fields = ", ".join(f"`{field}`" for field in rule["fields"]) or "schema-level"
        lines.append(f"- `{rule['rule_id']}` ({rule['severity']}): {fields} - {rule['message']}")
    return lines


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]
