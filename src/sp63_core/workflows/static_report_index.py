"""Static HTML index for generated engineering workflow report folders."""

from __future__ import annotations

import html
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

INDEX_WARNING = (
    "This static index does not certify the design. Deterministic SP63 "
    "verification and engineer review are mandatory. ML, if present, is "
    "advisory-only."
)
ML_OUTPUTS_MISSING_WARNING = (
    "ML readiness outputs were not found; deterministic-only workflow index generated."
)
CRITICAL_FILES_MISSING_WARNING = (
    "Critical workflow files are missing; static index requires engineer review."
)

EXPECTED_WORKFLOW_FILES = (
    "deterministic_report/input.json",
    "deterministic_report/report.md",
    "deterministic_report/report.json",
    "deterministic_report/report.html",
    "deterministic_report/manifest.json",
    "deterministic_report/README_REVIEW.md",
    "deterministic_report.zip",
    "workflow_summary.json",
    "workflow_summary.md",
    "README_WORKFLOW.md",
)

OPTIONAL_ML_READINESS_FILES = (
    "ml_readiness/engineering_ml_readiness.md",
    "ml_readiness/engineering_ml_readiness.json",
    "ml_readiness/engineering_ml_readiness_matrix.csv",
    "ml_readiness/README_REVIEW.md",
)

OPTIONAL_PREFLIGHT_FILES = (
    "input_preflight_report.json",
    "input_preflight_report.md",
)

ENGINEER_CHECKLIST = (
    "deterministic report reviewed",
    "archive validation pass",
    "ZIP checked",
    "manifest checked",
    "warnings reviewed",
    "ML advisory-only acknowledged",
    "engineer review completed",
)

LIMITATIONS = (
    "static index only",
    "no calculations inside HTML",
    "no project approval",
    "no material catalog update",
    "no ML project use approval",
)


@dataclass(frozen=True)
class StaticWorkflowReportIndexResult:
    """Result of building a static engineering workflow report index."""

    status: str
    index_status: str
    workflow_dir: str
    output_path: str
    detected_files: tuple[str, ...]
    missing_expected_files: tuple[str, ...]
    linked_files: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_static_workflow_report_index(
    *,
    workflow_dir: Path,
    output_path: Path | None = None,
    title: str = "Engineering Workflow Report Index",
) -> StaticWorkflowReportIndexResult:
    """Build a static HTML index for an existing engineering workflow folder."""
    workflow_path = Path(workflow_dir)
    index_path = Path(output_path) if output_path is not None else workflow_path / "index.html"
    warnings: list[str] = [INDEX_WARNING]
    errors: list[str] = []

    if not workflow_path.exists():
        errors.append(f"workflow directory does not exist: {workflow_path}")
        result = StaticWorkflowReportIndexResult(
            status="fail",
            index_status="fail",
            workflow_dir=str(workflow_path),
            output_path=str(index_path),
            detected_files=(),
            missing_expected_files=EXPECTED_WORKFLOW_FILES,
            linked_files=(),
            warnings=tuple(warnings),
            errors=tuple(errors),
            requires_engineer_review=True,
            ml_is_advisory_only=True,
            deterministic_checks_required=True,
            ml_ready_for_project_use=False,
        )
        return result

    detected_files = _detected_files(workflow_path)
    missing_expected_files = tuple(
        relative for relative in EXPECTED_WORKFLOW_FILES if not (workflow_path / relative).exists()
    )
    linked_files = tuple(
        relative
        for relative in (
            *OPTIONAL_PREFLIGHT_FILES,
            *EXPECTED_WORKFLOW_FILES,
            *OPTIONAL_ML_READINESS_FILES,
        )
        if (workflow_path / relative).exists()
    )

    optional_ml_files_present = any(
        (workflow_path / relative).exists() for relative in OPTIONAL_ML_READINESS_FILES
    )
    if not optional_ml_files_present:
        warnings.append(ML_OUTPUTS_MISSING_WARNING)
    if missing_expected_files:
        warnings.append(CRITICAL_FILES_MISSING_WARNING)

    index_status = "review_required" if missing_expected_files else "pass"
    summary = _read_workflow_summary(workflow_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        _render_static_index_html(
            title=title,
            workflow_dir=workflow_path,
            output_path=index_path,
            linked_files=linked_files,
            missing_expected_files=missing_expected_files,
            warnings=tuple(dict.fromkeys(warnings)),
            summary=summary,
        ),
        encoding="utf-8",
    )

    return StaticWorkflowReportIndexResult(
        status=index_status,
        index_status=index_status,
        workflow_dir=str(workflow_path),
        output_path=str(index_path),
        detected_files=detected_files,
        missing_expected_files=missing_expected_files,
        linked_files=linked_files,
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )


def _detected_files(workflow_dir: Path) -> tuple[str, ...]:
    return tuple(
        sorted(
            path.relative_to(workflow_dir).as_posix()
            for path in workflow_dir.rglob("*")
            if path.is_file()
        )
    )


def _read_workflow_summary(workflow_dir: Path) -> dict[str, Any]:
    summary_path = workflow_dir / "workflow_summary.json"
    if not summary_path.exists():
        return {}
    try:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _render_static_index_html(
    *,
    title: str,
    workflow_dir: Path,
    output_path: Path,
    linked_files: tuple[str, ...],
    missing_expected_files: tuple[str, ...],
    warnings: tuple[str, ...],
    summary: dict[str, Any],
) -> str:
    safe_title = html.escape(title)
    status_rows = _status_rows(summary)
    link_items = [
        _link_item(
            label=relative,
            href=_relative_href(workflow_dir / relative, output_path.parent),
        )
        for relative in linked_files
    ]
    missing_items = [
        f"<li><code>{html.escape(path)}</code></li>"
        for path in missing_expected_files
    ]
    warning_items = [f"<li>{html.escape(warning)}</li>" for warning in warnings]
    checklist_items = [f"<li>[ ] {html.escape(item)}</li>" for item in ENGINEER_CHECKLIST]
    limitation_items = [f"<li>{html.escape(item)}</li>" for item in LIMITATIONS]

    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            f"  <title>{safe_title}</title>",
            "  <style>",
            "    body { font-family: Arial, sans-serif; margin: 2rem; line-height: 1.45; }",
            "    main { max-width: 980px; margin: 0 auto; }",
            "    .warning { border: 2px solid #8a4b00; padding: 1rem; background: #fff7e6; }",
            "    .status { border-collapse: collapse; width: 100%; margin: 1rem 0; }",
            "    .status th, .status td { border: 1px solid #ccc; padding: 0.4rem; }",
            "    code { background: #f4f4f4; padding: 0.1rem 0.25rem; }",
            "    a { color: #0645ad; }",
            "  </style>",
            "</head>",
            "<body>",
            "<main>",
            f"<h1>{safe_title}</h1>",
            '<section class="warning"><strong>Warning:</strong> '
            f"{html.escape(INDEX_WARNING)}</section>",
            "<section>",
            "<h2>Summary</h2>",
            '<table class="status">',
            "<thead><tr><th>Field</th><th>Value</th></tr></thead>",
            "<tbody>",
            *status_rows,
            "</tbody>",
            "</table>",
            "</section>",
            "<section>",
            "<h2>Links</h2>",
            "<ul>",
            *(link_items or ["<li>No files linked.</li>"]),
            "</ul>",
            "</section>",
            "<section>",
            "<h2>Warnings</h2>",
            "<ul>",
            *(warning_items or ["<li>none</li>"]),
            "</ul>",
            "</section>",
            "<section>",
            "<h2>Missing Expected Files</h2>",
            "<ul>",
            *(missing_items or ["<li>none</li>"]),
            "</ul>",
            "</section>",
            "<section>",
            "<h2>Engineer Checklist</h2>",
            "<ul>",
            *checklist_items,
            "</ul>",
            "</section>",
            "<section>",
            "<h2>Limitations</h2>",
            "<ul>",
            *limitation_items,
            "</ul>",
            "</section>",
            "</main>",
            "</body>",
            "</html>",
            "",
        ]
    )


def _status_rows(summary: dict[str, Any]) -> list[str]:
    fields = (
        "workflow_status",
        "preflight_status",
        "preflight_errors_count",
        "preflight_warnings_count",
        "deterministic_report_status",
        "archive_validation_status",
        "zip_status",
        "ml_readiness_status",
        "ml_ready_for_project_use",
    )
    rows = []
    for field in fields:
        value = summary.get(field, "not_available")
        escaped_field = html.escape(field)
        escaped_value = html.escape(str(value).lower() if isinstance(value, bool) else str(value))
        rows.append(
            f"<tr><td><code>{escaped_field}</code></td>"
            f"<td><code>{escaped_value}</code></td></tr>"
        )
    return rows


def _link_item(*, label: str, href: str) -> str:
    return (
        f'<li><a href="{html.escape(href, quote=True)}">'
        f"{html.escape(label)}</a></li>"
    )


def _relative_href(path: Path, start: Path) -> str:
    return os.path.relpath(path, start=start).replace("\\", "/")
