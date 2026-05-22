"""Export calculation protocols to JSON and HTML."""

import json
from html import escape
from pathlib import Path
from typing import Any

from sp63_core.report.protocol import CalculationProtocol

DRAFT_WARNING = (
    "Расчётный протокол является MVP/draft и требует инженерной проверки."
)


def protocol_to_json(protocol: CalculationProtocol, *, indent: int = 2) -> str:
    """Return a JSON string for a calculation protocol."""
    return json.dumps(protocol.as_dict(), ensure_ascii=False, indent=indent)


def save_protocol_json(protocol: CalculationProtocol, path: str | Path) -> Path:
    """Save a calculation protocol as JSON."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(protocol_to_json(protocol), encoding="utf-8")
    return output_path


def protocol_to_html(protocol: CalculationProtocol) -> str:
    """Return a minimal standalone HTML report for a calculation protocol."""
    data = protocol.as_dict()
    sections = [
        ("Исходные данные", data["input_data"]),
        ("Материалы", data["materials"]),
        ("Геометрия", data["geometry"]),
        ("Армирование", data["reinforcement"]),
        ("Проверки", data["checks"]),
        ("Предупреждения", data["warnings"] or ["-"]),
        ("Итоговый статус", {"status": data["status"]}),
    ]
    body = "\n".join(_render_section(title, content) for title, content in sections)
    requires_review = escape(str(data["requires_engineer_review"]))

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>SP63 calculation protocol</title>
  <style>
    body {{ font-family: Arial, sans-serif; line-height: 1.45; margin: 32px; }}
    h1, h2 {{ color: #1f2933; }}
    table {{ border-collapse: collapse; margin-bottom: 20px; width: 100%; }}
    th, td {{ border: 1px solid #cbd2d9; padding: 6px 8px; text-align: left; }}
    th {{ background: #f5f7fa; }}
    pre {{ background: #f5f7fa; padding: 10px; white-space: pre-wrap; }}
    .warning {{ border-left: 4px solid #b7791f; background: #fff8e6; padding: 10px; }}
  </style>
</head>
<body>
  <h1>SP63 calculation protocol</h1>
  <p class="warning">{escape(DRAFT_WARNING)}</p>
  <p><strong>requires_engineer_review:</strong> {requires_review}</p>
{body}
</body>
</html>
"""


def save_protocol_html(protocol: CalculationProtocol, path: str | Path) -> Path:
    """Save a calculation protocol as HTML."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(protocol_to_html(protocol), encoding="utf-8")
    return output_path


def _render_section(title: str, content: Any) -> str:
    return f"  <section>\n    <h2>{escape(title)}</h2>\n{_render_content(content)}\n  </section>"


def _render_content(content: Any) -> str:
    if isinstance(content, dict):
        rows = "\n".join(
            "      <tr>"
            f"<th>{escape(str(key))}</th>"
            f"<td>{_format_value(value)}</td>"
            "</tr>"
            for key, value in content.items()
        )
        return f"    <table>\n{rows}\n    </table>"
    if isinstance(content, list | tuple):
        items = "\n".join(f"      <li>{_format_value(item)}</li>" for item in content)
        return f"    <ul>\n{items}\n    </ul>"
    return f"    <p>{_format_value(content)}</p>"


def _format_value(value: Any) -> str:
    if isinstance(value, dict):
        return f"<pre>{escape(json.dumps(value, ensure_ascii=False, indent=2))}</pre>"
    if isinstance(value, list | tuple):
        return f"<pre>{escape(json.dumps(value, ensure_ascii=False, indent=2))}</pre>"
    return escape(str(value))
