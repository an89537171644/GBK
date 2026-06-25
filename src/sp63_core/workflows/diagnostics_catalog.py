"""Human-friendly diagnostics catalog for engineering workflow messages.

The catalog is static documentation metadata. It does not run deterministic
checks and does not change calculation behavior.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DIAGNOSTICS_WARNING = (
    "Diagnostics catalog messages are guidance only. Deterministic SP63 "
    "verification and engineer review remain mandatory."
)

_DIAGNOSTICS: tuple[dict[str, str], ...] = (
    {
        "code": "missing_required_field",
        "category": "input_preflight",
        "severity": "error",
        "title_en": "Missing required field",
        "title_ru": "Не заполнено обязательное поле",
        "message_en": "A required engineering input field is missing.",
        "message_ru": "В исходных данных отсутствует обязательное поле.",
        "recommended_action_en": "Fill all required geometry, material, and load fields.",
        "recommended_action_ru": "Заполните обязательные поля геометрии, материалов и нагрузок.",
        "related_command": "python -m sp63_core input-preflight --input-json input.json --json",
    },
    {
        "code": "invalid_geometry",
        "category": "geometry",
        "severity": "error",
        "title_en": "Invalid geometry",
        "title_ru": "Некорректная геометрия",
        "message_en": "Geometry values are outside the supported beam assumptions.",
        "message_ru": "Геометрия выходит за пределы поддержанных предпосылок балки.",
        "recommended_action_en": "Review section dimensions, cover, and effective depth.",
        "recommended_action_ru": "Проверьте размеры сечения, защитный слой и рабочую высоту.",
        "related_command": "python -m sp63_core input-preflight --input-json input.json --json",
    },
    {
        "code": "cover_greater_or_equal_h",
        "category": "geometry",
        "severity": "error",
        "title_en": "Cover is not smaller than height",
        "title_ru": "Защитный слой не меньше высоты",
        "message_en": "Concrete cover must be smaller than the section height.",
        "message_ru": "Защитный слой должен быть меньше высоты сечения.",
        "recommended_action_en": "Correct cover or section height before running calculations.",
        "recommended_action_ru": "Исправьте защитный слой или высоту сечения до расчета.",
        "related_command": "python -m sp63_core input-preflight --input-json input.json --json",
    },
    {
        "code": "unknown_material_class",
        "category": "materials",
        "severity": "error",
        "title_en": "Unknown material class",
        "title_ru": "Неизвестный класс материала",
        "message_en": "The requested concrete or reinforcement class is not in the catalog.",
        "message_ru": "Указанный класс бетона или арматуры отсутствует в каталоге.",
        "recommended_action_en": "Use a supported catalog class or add it through a reviewed task.",
        "recommended_action_ru": (
            "Используйте поддержанный класс или добавьте его отдельной ревизией."
        ),
        "related_command": "python -m sp63_core materials-audit --json",
    },
    {
        "code": "material_catalog_review_required",
        "category": "materials",
        "severity": "warning",
        "title_en": "Material catalog requires review",
        "title_ru": "Каталог материалов требует проверки",
        "message_en": "Material values are draft until engineer verification is complete.",
        "message_ru": "Значения материалов остаются draft до инженерной сверки.",
        "recommended_action_en": "Fill and review the material verification CSV.",
        "recommended_action_ru": "Заполните и проверьте CSV сверки материалов.",
        "related_command": "python -m sp63_core materials-audit --verification-template",
    },
    {
        "code": "negative_load",
        "category": "loads",
        "severity": "error",
        "title_en": "Negative load value",
        "title_ru": "Отрицательная нагрузка",
        "message_en": "Moment, shear, and service moment inputs must be nonnegative.",
        "message_ru": "Момент, поперечная сила и сервисный момент должны быть неотрицательными.",
        "recommended_action_en": "Check load signs and input convention.",
        "recommended_action_ru": "Проверьте знаки нагрузок и принятую конвенцию ввода.",
        "related_command": "python -m sp63_core input-preflight --input-json input.json --json",
    },
    {
        "code": "mser_greater_than_m",
        "category": "loads",
        "severity": "warning",
        "title_en": "Service moment exceeds design moment",
        "title_ru": "Сервисный момент больше расчетного",
        "message_en": "Mser greater than M requires engineering review.",
        "message_ru": "Mser больше M требует инженерной проверки.",
        "recommended_action_en": "Confirm load combinations and service/design values.",
        "recommended_action_ru": "Проверьте сочетания нагрузок и расчетные/сервисные значения.",
        "related_command": "python -m sp63_core input-preflight --input-json input.json --json",
    },
    {
        "code": "archive_validation_fail",
        "category": "archive",
        "severity": "error",
        "title_en": "Archive validation failed",
        "title_ru": "Проверка архива не пройдена",
        "message_en": "Report archive manifest or checksum validation failed.",
        "message_ru": "Проверка manifest или checksum архива отчета не пройдена.",
        "recommended_action_en": "Regenerate the report bundle and rerun archive validation.",
        "recommended_action_ru": "Пересоберите пакет отчета и повторите проверку архива.",
        "related_command": "python -m sp63_core report-archive-validate --path reports/case --json",
    },
    {
        "code": "zip_missing",
        "category": "zip",
        "severity": "warning",
        "title_en": "ZIP package missing",
        "title_ru": "ZIP-пакет отсутствует",
        "message_en": "The expected report ZIP package was not created or was removed.",
        "message_ru": "Ожидаемый ZIP-пакет отчета не создан или удален.",
        "recommended_action_en": "Run the workflow without --no-zip or export the archive ZIP.",
        "recommended_action_ru": "Запустите workflow без --no-zip или экспортируйте ZIP архива.",
        "related_command": (
            "python -m sp63_core report-archive-zip --path reports/case "
            "--output reports/case.zip --json"
        ),
    },
    {
        "code": "manifest_missing",
        "category": "archive",
        "severity": "error",
        "title_en": "Manifest missing",
        "title_ru": "Manifest отсутствует",
        "message_en": "A report bundle is missing manifest.json.",
        "message_ru": "В пакете отчета отсутствует manifest.json.",
        "recommended_action_en": "Regenerate the deterministic report bundle.",
        "recommended_action_ru": "Пересоберите deterministic report bundle.",
        "related_command": (
            "python -m sp63_core design-report --input-json input.json "
            "--bundle-output reports/case"
        ),
    },
    {
        "code": "checksum_mismatch",
        "category": "archive",
        "severity": "error",
        "title_en": "Checksum mismatch",
        "title_ru": "Несовпадение checksum",
        "message_en": "A file checksum does not match the manifest metadata.",
        "message_ru": "Checksum файла не совпадает с данными manifest.",
        "recommended_action_en": "Treat the bundle as modified and regenerate or review manually.",
        "recommended_action_ru": "Считайте пакет измененным; пересоберите или проверьте вручную.",
        "related_command": "python -m sp63_core report-archive-validate --path reports/case --json",
    },
    {
        "code": "ml_readiness_incomplete",
        "category": "ml_readiness",
        "severity": "warning",
        "title_en": "ML readiness incomplete",
        "title_ru": "ML-readiness не завершен",
        "message_en": "ML evidence is incomplete and cannot approve project use.",
        "message_ru": "ML-доказательства неполны и не дают разрешения на проектное применение.",
        "recommended_action_en": (
            "Provide dataset, external validation, and material verification evidence."
        ),
        "recommended_action_ru": (
            "Предоставьте dataset, external validation и material verification."
        ),
        "related_command": "python -m sp63_core engineering-ml-readiness-bundle --help",
    },
    {
        "code": "ml_project_use_forbidden",
        "category": "ml_readiness",
        "severity": "error",
        "title_en": "ML project use forbidden",
        "title_ru": "Проектное использование ML запрещено",
        "message_en": "ml_ready_for_project_use must remain false.",
        "message_ru": "ml_ready_for_project_use должен оставаться false.",
        "recommended_action_en": "Use deterministic SP63 verification for every design decision.",
        "recommended_action_ru": "Используйте deterministic SP63 verification для каждого решения.",
        "related_command": "python -m sp63_core ml-proposal-verify --json",
    },
    {
        "code": "generated_report_missing",
        "category": "workflow",
        "severity": "error",
        "title_en": "Generated report missing",
        "title_ru": "Сформированный отчет отсутствует",
        "message_en": "Expected deterministic report files are missing.",
        "message_ru": "Ожидаемые файлы deterministic report отсутствуют.",
        "recommended_action_en": "Rerun engineering-workflow and review errors.",
        "recommended_action_ru": "Повторите engineering-workflow и проверьте ошибки.",
        "related_command": (
            "python -m sp63_core engineering-workflow --input-json input.json "
            "--output-dir reports/workflow --json"
        ),
    },
    {
        "code": "protected_file_changed",
        "category": "protected_files",
        "severity": "error",
        "title_en": "Protected file changed",
        "title_ru": "Изменен protected file",
        "message_en": "A protected formula, material, or external-validation file changed.",
        "message_ru": "Изменен protected-файл формул, материалов или external validation.",
        "recommended_action_en": "Stop release flow and review the protected file change.",
        "recommended_action_ru": "Остановите release flow и проверьте изменение protected-файла.",
        "related_command": "python -m sp63_core protected-files-check --json",
    },
    {
        "code": "preflight_fail",
        "category": "input_preflight",
        "severity": "error",
        "title_en": "Preflight failed",
        "title_ru": "Preflight завершился ошибкой",
        "message_en": "Input preflight found blocking errors.",
        "message_ru": "Input preflight нашел блокирующие ошибки.",
        "recommended_action_en": "Fix preflight errors before running deterministic workflow.",
        "recommended_action_ru": "Исправьте ошибки preflight перед deterministic workflow.",
        "related_command": (
            "python -m sp63_core engineering-workflow --input-json input.json "
            "--output-dir reports/workflow --with-preflight --json"
        ),
    },
    {
        "code": "deterministic_report_fail",
        "category": "workflow",
        "severity": "error",
        "title_en": "Deterministic report failed",
        "title_ru": "Deterministic report завершился ошибкой",
        "message_en": "The deterministic report workflow failed or produced fail status.",
        "message_ru": "Deterministic report workflow завершился ошибкой или статусом fail.",
        "recommended_action_en": "Review workflow_summary.json and deterministic report warnings.",
        "recommended_action_ru": "Проверьте workflow_summary.json и предупреждения отчета.",
        "related_command": (
            "python -m sp63_core engineering-workflow --input-json input.json "
            "--output-dir reports/workflow --json"
        ),
    },
    {
        "code": "engineer_review_required",
        "category": "release_candidate",
        "severity": "info",
        "title_en": "Engineer review required",
        "title_ru": "Требуется инженерная проверка",
        "message_en": "The software output is draft-MVP evidence and needs engineer review.",
        "message_ru": "Вывод программы является draft-MVP evidence и требует проверки инженером.",
        "recommended_action_en": (
            "Review deterministic reports, materials, external validation, and warnings."
        ),
        "recommended_action_ru": "Проверьте отчеты, материалы, external validation и warnings.",
        "related_command": (
            "python -m sp63_core release-candidate-report --output-dir reports/rc --json"
        ),
    },
)


@dataclass(frozen=True)
class DiagnosticsCatalogResult:
    """Diagnostics catalog export result."""

    status: str
    catalog_status: str
    diagnostics_count: int
    categories: tuple[str, ...]
    json_data: dict[str, Any]
    markdown: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_diagnostics_catalog(
    *,
    output_dir: Path | None = None,
) -> DiagnosticsCatalogResult:
    """Build a static diagnostics catalog for workflow-facing messages."""
    diagnostics = tuple(dict(item) for item in _DIAGNOSTICS)
    categories = tuple(sorted({item["category"] for item in diagnostics}))
    errors = _validate_diagnostics(diagnostics)
    status = "fail" if errors else "pass"
    json_data = {
        "report_type": "diagnostics_catalog",
        "status": status,
        "catalog_status": status,
        "diagnostics_count": len(diagnostics),
        "categories": list(categories),
        "diagnostics": list(diagnostics),
        "warnings": [DIAGNOSTICS_WARNING],
        "errors": list(errors),
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "ml_ready_for_project_use": False,
    }
    markdown = _render_diagnostics_catalog_markdown(json_data)
    result = DiagnosticsCatalogResult(
        status=status,
        catalog_status=status,
        diagnostics_count=len(diagnostics),
        categories=categories,
        json_data=json_data,
        markdown=markdown,
        warnings=(DIAGNOSTICS_WARNING,),
        errors=errors,
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    if output_dir is not None:
        _write_catalog_files(Path(output_dir), result)
    return result


def _validate_diagnostics(diagnostics: tuple[dict[str, str], ...]) -> tuple[str, ...]:
    errors: list[str] = []
    required_keys = (
        "code",
        "category",
        "severity",
        "title_en",
        "title_ru",
        "message_en",
        "message_ru",
        "recommended_action_en",
        "recommended_action_ru",
        "related_command",
    )
    valid_severities = {"info", "warning", "error"}
    codes: set[str] = set()
    for item in diagnostics:
        missing_keys = [key for key in required_keys if not item.get(key)]
        if missing_keys:
            errors.append(f"diagnostic {item.get('code', '<unknown>')} missing {missing_keys}")
        severity = item.get("severity")
        if severity not in valid_severities:
            errors.append(f"diagnostic {item.get('code', '<unknown>')} has invalid severity")
        code = item.get("code", "")
        if code in codes:
            errors.append(f"duplicate diagnostic code: {code}")
        codes.add(code)
    return tuple(errors)


def _render_diagnostics_catalog_markdown(json_data: dict[str, Any]) -> str:
    lines = [
        "# Diagnostics Catalog",
        "",
        DIAGNOSTICS_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Summary",
        "",
        f"- status: `{json_data['status']}`",
        f"- diagnostics_count: `{json_data['diagnostics_count']}`",
        f"- categories: `{', '.join(json_data['categories'])}`",
        "",
        "## Diagnostics",
        "",
        "| code | category | severity | title_en | title_ru | related_command |",
        "|---|---|---|---|---|---|",
    ]
    for item in json_data["diagnostics"]:
        lines.append(
            "| {code} | {category} | {severity} | {title_en} | {title_ru} | `{command}` |".format(
                code=item["code"],
                category=item["category"],
                severity=item["severity"],
                title_en=item["title_en"],
                title_ru=item["title_ru"],
                command=item["related_command"],
            )
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Messages are guidance for users and reviewers.",
            "- The catalog does not perform calculations.",
            "- Deterministic SP63 checks remain mandatory.",
            "- Engineer review remains mandatory.",
            "- ML remains advisory-only and cannot approve project use.",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_catalog_files(output_dir: Path, result: DiagnosticsCatalogResult) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "diagnostics_catalog.json").write_text(
        json.dumps(result.json_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "diagnostics_catalog.md").write_text(result.markdown, encoding="utf-8")
