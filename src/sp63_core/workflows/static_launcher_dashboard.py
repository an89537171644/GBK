"""Static local launcher dashboard for review workflows."""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path

STATIC_LAUNCHER_WARNING = (
    "Static launcher dashboard is not a GUI application, web server, or design "
    "approval tool. It only links review commands and reports."
)

LAUNCHER_COMMANDS: tuple[str, ...] = (
    "python -m sp63_core validate --golden",
    "python -m sp63_core clean-demo-workflow --output-dir reports/clean_demo --json",
    "python -m sp63_core portable-package --output-dir reports/portable_package --json",
    "python -m sp63_core engineer-review-packet --output-dir reports/engineer_review_packet --json",
    "python -m sp63_core release-bundle --output-dir reports/release_bundle "
    "--version 0.9.0-rc1 --json",
)


@dataclass(frozen=True)
class StaticLauncherDashboardResult:
    """Static launcher dashboard result."""

    status: str
    output_dir: str
    dashboard_html_path: str
    dashboard_json_path: str
    readme_path: str
    command_count: int
    generated_files: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False
    project_use_allowed: bool = False
    web_server_required: bool = False
    javascript_calculations_present: bool = False


def build_static_launcher_dashboard(*, output_dir: Path) -> StaticLauncherDashboardResult:
    """Build static HTML launcher dashboard files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    html_path = output_path / "launcher_dashboard.html"
    json_path = output_path / "launcher_dashboard.json"
    readme_path = output_path / "README_STATIC_LAUNCHER.md"
    result = StaticLauncherDashboardResult(
        status="pass",
        output_dir=str(output_path),
        dashboard_html_path=str(html_path),
        dashboard_json_path=str(json_path),
        readme_path=str(readme_path),
        command_count=len(LAUNCHER_COMMANDS),
        generated_files=(str(html_path), str(json_path), str(readme_path)),
        warnings=(STATIC_LAUNCHER_WARNING,),
        errors=(),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
        project_use_allowed=False,
        web_server_required=False,
        javascript_calculations_present=False,
    )
    html_path.write_text(_render_html(result), encoding="utf-8")
    json_path.write_text(
        json.dumps({"report_type": "static_launcher_dashboard", **result.__dict__}, indent=2),
        encoding="utf-8",
    )
    readme_path.write_text(_render_readme(), encoding="utf-8")
    return result


def _render_html(result: StaticLauncherDashboardResult) -> str:
    command_blocks = "\n".join(
        f"<li><code>{html.escape(command)}</code></li>" for command in LAUNCHER_COMMANDS
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>SP63 Static Launcher Dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; line-height: 1.5; }}
    code {{ background: #f4f4f4; padding: 0.15rem 0.3rem; }}
    .warning {{ border: 1px solid #a66; padding: 1rem; background: #fff6f6; }}
  </style>
</head>
<body>
  <h1>SP63 Static Launcher Dashboard</h1>
  <div class="warning">{html.escape(STATIC_LAUNCHER_WARNING)}</div>
  <h2>Safety Flags</h2>
  <ul>
    <li>deterministic SP63 checks are mandatory</li>
    <li>engineer review is mandatory</li>
    <li>ML remains advisory-only</li>
    <li>ml_ready_for_project_use = false</li>
    <li>project_use_allowed = false</li>
    <li>no web server is required</li>
  </ul>
  <h2>Copyable CLI Commands</h2>
  <ul>
    {command_blocks}
  </ul>
  <h2>Useful Links</h2>
  <ul>
    <li><a href="../clean_demo/index.html">clean demo report index</a></li>
    <li><a href="../portable_package/README_PORTABLE_PACKAGE.md">portable package notes</a></li>
    <li><a href="../../docs/user_manual/quickstart.md">user manual quickstart</a></li>
    <li><a href="../engineering_workflow/index.html">engineering workflow report index</a></li>
  </ul>
</body>
</html>
"""


def _render_readme() -> str:
    return "\n".join(
        [
            "# README Static Launcher",
            "",
            STATIC_LAUNCHER_WARNING,
            "",
            "Open `launcher_dashboard.html` directly from disk.",
            "No web server is required and no JavaScript calculations are included.",
        ]
    ) + "\n"
