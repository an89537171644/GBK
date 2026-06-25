"""Static HTML preview for the engineering input form schema."""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.workflows.input_form_schema import build_input_form_schema

PREVIEW_WARNING = (
    "This static preview does not perform design calculations. Deterministic SP63 "
    "verification and engineer review are mandatory."
)


@dataclass(frozen=True)
class StaticInputFormPreviewResult:
    """Result of building the static input form preview."""

    status: str
    preview_status: str
    output_dir: str | None
    output_path: str | None
    schema_field_count: int
    generated_files: tuple[str, ...]
    json_data: dict[str, Any]
    markdown: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_static_input_form_preview(
    *,
    output_dir: Path | None = None,
    title: str = "Engineering Input Form Preview",
) -> StaticInputFormPreviewResult:
    """Build static input-form preview artifacts from the K66 schema metadata."""
    schema = build_input_form_schema()
    json_data: dict[str, Any] = {
        "preview_type": "static_input_form_preview",
        "status": "pass",
        "preview_status": "pass",
        "title": title,
        "schema_field_count": schema.field_count,
        "schema_required_fields": list(schema.required_fields),
        "schema_optional_fields": list(schema.optional_fields),
        "generated_files": [],
        "warning": PREVIEW_WARNING,
        "groups": schema.json_data["groups"],
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "ml_ready_for_project_use": False,
    }
    html_text = _render_preview_html(title=title, schema_data=schema.json_data)
    markdown = _render_preview_readme(title=title, output_path="input_form_preview.html")
    generated_files: tuple[str, ...] = ()
    output_path: str | None = None

    if output_dir is not None:
        output_path_obj = Path(output_dir) / "input_form_preview.html"
        json_path = Path(output_dir) / "input_form_preview.json"
        readme_path = Path(output_dir) / "README_INPUT_FORM_PREVIEW.md"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_path_obj.write_text(html_text, encoding="utf-8")
        json_data["generated_files"] = [
            "input_form_preview.html",
            "input_form_preview.json",
            "README_INPUT_FORM_PREVIEW.md",
        ]
        json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")
        readme_path.write_text(markdown, encoding="utf-8")
        generated_files = tuple(json_data["generated_files"])
        output_path = str(output_path_obj)

    return StaticInputFormPreviewResult(
        status="pass",
        preview_status="pass",
        output_dir=str(output_dir) if output_dir is not None else None,
        output_path=output_path,
        schema_field_count=schema.field_count,
        generated_files=generated_files,
        json_data=json_data,
        markdown=markdown,
        warnings=(PREVIEW_WARNING,),
        errors=(),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )


def _render_preview_html(*, title: str, schema_data: dict[str, Any]) -> str:
    group_sections = [
        _render_group_section(group)
        for group in schema_data["groups"]
    ]
    warnings = "\n".join(
        f"<li>{html.escape(warning)}</li>" for warning in schema_data["mandatory_warnings"]
    )
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            f"  <title>{html.escape(title)}</title>",
            "  <style>",
            "    body { font-family: Arial, sans-serif; margin: 0; color: #1f2933; }",
            "    header { background: #263238; color: #fff; padding: 24px; }",
            "    main { max-width: 1120px; margin: 0 auto; padding: 24px; }",
            "    section { border-bottom: 1px solid #d9e2ec; padding: 18px 0; }",
            "    table { border-collapse: collapse; width: 100%; margin-top: 12px; }",
            "    th, td { border: 1px solid #d9e2ec; padding: 8px; text-align: left; }",
            "    th { background: #f0f4f8; }",
            "    code { background: #f5f7fa; padding: 2px 4px; }",
            "    .warning { background: #fff7cc; border-left: 6px solid #f0b429; padding: 16px; }",
            "    .flags { display: grid; gap: 8px; "
            "grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }",
            "  </style>",
            "</head>",
            "<body>",
            "  <header>",
            f"    <h1>{html.escape(title)}</h1>",
            f"    <p>{html.escape(PREVIEW_WARNING)}</p>",
            "  </header>",
            "  <main>",
            '    <section class="warning">',
            "      <strong>Draft-MVP safety notice</strong>",
            "      <ul>",
            f"        {warnings}",
            "      </ul>",
            "    </section>",
            "    <section>",
            "      <h2>Safety Flags</h2>",
            '      <div class="flags">',
            "        <p><code>requires_engineer_review = true</code></p>",
            "        <p><code>ml_is_advisory_only = true</code></p>",
            "        <p><code>deterministic_checks_required = true</code></p>",
            "        <p><code>ml_ready_for_project_use = false</code></p>",
            "      </div>",
            "      <p>Design calculations are executed only through the deterministic "
            "workflow.</p>",
            "    </section>",
            *group_sections,
            "    <section>",
            "      <h2>Limitations</h2>",
            "      <ul>",
            "        <li>No calculations are performed inside this HTML file.</li>",
            "        <li>No JavaScript calculation logic is included.</li>",
            "        <li>No web server or GUI framework is required.</li>",
            "        <li>No project approval is implied by this preview.</li>",
            "      </ul>",
            "    </section>",
            "  </main>",
            "</body>",
            "</html>",
        ]
    )


def _render_group_section(group: dict[str, Any]) -> str:
    rows = "\n".join(_field_row(field) for field in group["fields"])
    return "\n".join(
        [
            "    <section>",
            f"      <h2>{html.escape(group['title'])}</h2>",
            f"      <p><code>{html.escape(group['group'])}</code></p>",
            "      <table>",
            "        <thead>",
            "          <tr>",
            "            <th>Field</th>",
            "            <th>Label</th>",
            "            <th>RU label</th>",
            "            <th>Unit</th>",
            "            <th>Required</th>",
            "            <th>Default/example</th>",
            "            <th>Min/max</th>",
            "            <th>Engineering hint</th>",
            "            <th>Validation message</th>",
            "          </tr>",
            "        </thead>",
            "        <tbody>",
            rows,
            "        </tbody>",
            "      </table>",
            "    </section>",
        ]
    )


def _field_row(field: dict[str, Any]) -> str:
    default = field.get("default")
    example = field.get("example")
    default_or_example = example if default is None and example is not None else default
    min_value = field.get("min")
    max_value = field.get("max")
    min_max = "/".join(
        "-" if value is None else str(value)
        for value in (min_value, max_value)
    )
    return (
        "          <tr>"
        f"<td><code>{html.escape(field['name'])}</code></td>"
        f"<td>{html.escape(str(field['label']))}</td>"
        f"<td>{html.escape(str(field['label_ru']))}</td>"
        f"<td>{html.escape(str(field.get('unit') or '-'))}</td>"
        f"<td>{str(field['required']).lower()}</td>"
        f"<td>{html.escape('-' if default_or_example is None else str(default_or_example))}</td>"
        f"<td>{html.escape(min_max)}</td>"
        f"<td>{html.escape(str(field['engineering_hint']))}</td>"
        f"<td>{html.escape(str(field['validation_message']))}</td>"
        "</tr>"
    )


def _render_preview_readme(*, title: str, output_path: str) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            "requires_engineer_review = true",
            "ml_is_advisory_only = true",
            "deterministic_checks_required = true",
            "ml_ready_for_project_use = false",
            "",
            PREVIEW_WARNING,
            "",
            "## Files",
            "",
            f"- `{output_path}` - static input form preview;",
            "- `input_form_preview.json` - machine-readable preview metadata;",
            "- `README_INPUT_FORM_PREVIEW.md` - this review note.",
            "",
            "## Limitations",
            "",
            "- This is not a GUI and not a web app.",
            "- This preview does not perform calculations.",
            "- Deterministic workflow commands remain authoritative.",
            "- Engineer review remains mandatory.",
        ]
    ) + "\n"
