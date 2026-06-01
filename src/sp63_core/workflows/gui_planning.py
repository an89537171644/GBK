"""Planning-only GUI technology decision for engineering workflow wrappers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RECOMMENDED_OPTION = "cli_first_with_static_html_reports"
RECOMMENDED_NEXT_STEP = "K65 - static workflow launcher and HTML report index"
PLANNING_WARNING = (
    "This document is planning only. It does not implement GUI and does not "
    "approve ML for project use."
)

CONSIDERED_OPTIONS = (
    "cli_first_no_gui",
    "static_html_report_viewer",
    "desktop_tkinter",
    "desktop_pyside_or_pyqt",
    "streamlit_local_app",
    "gradio_local_app",
    "fastapi_web_backend",
    "electron_wrapper",
)

REJECTED_OPTIONS = (
    "desktop_tkinter",
    "desktop_pyside_or_pyqt",
    "streamlit_local_app",
    "gradio_local_app",
    "fastapi_web_backend",
    "electron_wrapper",
)

REQUIRED_BACKEND_COMMANDS = (
    "python -m sp63_core validate --golden",
    "python -m sp63_core manual-cases --json",
    "python -m sp63_core engineering-workflow-self-check "
    "--output-dir reports/workflow_self_check --json",
    "python -m sp63_core engineering-workflow "
    "--input-json <input.json> --output-dir <output_dir> --json",
    "python -m sp63_core engineering-ml-readiness "
    "--dataset <dataset.jsonl> --external-validation-csv <external.csv> "
    "--material-verification-csv <materials.csv> --json",
    "python -m sp63_core engineering-interface-contract --output-dir <output_dir> --json",
)

REQUIRED_SCREENS_OR_PANELS = (
    "Safety notice panel",
    "Input selection panel",
    "Run deterministic workflow panel",
    "Output files panel",
    "Archive/ZIP validation panel",
    "ML readiness panel",
    "Engineer checklist panel",
    "Logs/errors panel",
)

REQUIRED_SAFETY_WARNINGS = (
    "ML output must never be displayed as final design decision.",
    "Deterministic SP63 status must be visually primary.",
    "Engineer review warning must always be visible.",
    "ml_ready_for_project_use must remain false.",
    "Failed/review_required statuses must not be hidden.",
    "Archive validation and manifest status must be visible.",
    "Material verification must not update catalog automatically.",
    "External validation must be shown separately from synthetic benchmark results.",
)

OPTION_DETAILS: tuple[dict[str, Any], ...] = (
    {
        "option": "cli_first_no_gui",
        "advantages": (
            "uses existing tested commands",
            "no UI dependencies",
            "lowest risk of hiding deterministic statuses",
        ),
        "disadvantages": (
            "less convenient for non-CLI users",
            "manual file navigation remains necessary",
        ),
        "dependency_impact": "none",
        "safety_risks": ("operator may skip generated review files",),
        "recommended_stage": "current safe baseline",
    },
    {
        "option": "static_html_report_viewer",
        "advantages": (
            "uses existing report.html outputs",
            "portable file-based review",
            "keeps deterministic reports visible",
        ),
        "disadvantages": (
            "cannot launch workflows by itself",
            "needs an index file to organize generated outputs",
        ),
        "dependency_impact": "none",
        "safety_risks": ("viewer must not hide review_required or fail statuses",),
        "recommended_stage": "recommended K65 direction",
    },
    {
        "option": "desktop_tkinter",
        "advantages": ("ships with many Python installations", "can launch CLI commands"),
        "disadvantages": ("adds UI state and event-loop complexity", "limited modern UI polish"),
        "dependency_impact": "stdlib on some platforms, but still a GUI layer",
        "safety_risks": ("UI could obscure workflow warnings",),
        "recommended_stage": "postpone until CLI/report workflow is stable",
    },
    {
        "option": "desktop_pyside_or_pyqt",
        "advantages": ("strong desktop UI toolkit", "good native packaging options"),
        "disadvantages": ("large dependency footprint", "packaging complexity"),
        "dependency_impact": "heavy GUI dependency",
        "safety_risks": ("large UI surface could make ML outputs look authoritative",),
        "recommended_stage": "not recommended before external validation maturity",
    },
    {
        "option": "streamlit_local_app",
        "advantages": ("fast prototype", "simple local dashboards"),
        "disadvantages": ("web-app mental model", "new runtime dependency"),
        "dependency_impact": "adds Streamlit dependency",
        "safety_risks": ("dashboard layout may make advisory ML look like a checker",),
        "recommended_stage": "not in K64/K65",
    },
    {
        "option": "gradio_local_app",
        "advantages": ("fast ML demo workflows", "simple local app primitives"),
        "disadvantages": ("ML-demo framing is a poor fit for engineering review",),
        "dependency_impact": "adds Gradio dependency",
        "safety_risks": ("can frame ML as the primary interface",),
        "recommended_stage": "not recommended for engineering safety workflow",
    },
    {
        "option": "fastapi_web_backend",
        "advantages": ("clean API boundary", "can serve multiple clients later"),
        "disadvantages": ("backend service lifecycle and security concerns",),
        "dependency_impact": "adds FastAPI/server dependencies",
        "safety_risks": ("remote/API use can bypass local review package habits",),
        "recommended_stage": "future integration only after stable CLI contract",
    },
    {
        "option": "electron_wrapper",
        "advantages": ("cross-platform desktop shell", "HTML-based interface"),
        "disadvantages": ("large runtime", "packaging and update complexity"),
        "dependency_impact": "adds Node/Electron stack",
        "safety_risks": ("heavy wrapper can hide that CLI is the authority",),
        "recommended_stage": "not recommended for current draft-MVP",
    },
)


@dataclass(frozen=True)
class EngineeringGUIPlanningResult:
    """Planning-only technology decision for future GUI wrappers."""

    status: str
    decision_status: str
    recommended_option: str
    considered_options: tuple[str, ...]
    rejected_options: tuple[str, ...]
    required_backend_commands: tuple[str, ...]
    required_safety_warnings: tuple[str, ...]
    recommended_next_step: str
    json_data: dict[str, Any]
    markdown: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_engineering_gui_planning_decision(
    *,
    output_dir: Path | None = None,
) -> EngineeringGUIPlanningResult:
    """Build the planning-only GUI technology decision."""
    json_data: dict[str, Any] = {
        "decision_type": "engineering_gui_planning_decision",
        "status": "pass",
        "decision_status": "pass",
        "recommended_option": RECOMMENDED_OPTION,
        "considered_options": list(CONSIDERED_OPTIONS),
        "rejected_options": list(REJECTED_OPTIONS),
        "option_details": list(OPTION_DETAILS),
        "required_backend_commands": list(REQUIRED_BACKEND_COMMANDS),
        "required_screens_or_panels": list(REQUIRED_SCREENS_OR_PANELS),
        "required_safety_warnings": list(REQUIRED_SAFETY_WARNINGS),
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "ml_ready_for_project_use": False,
    }
    markdown = render_engineering_gui_planning_markdown(json_data)
    result = EngineeringGUIPlanningResult(
        status="pass",
        decision_status="pass",
        recommended_option=RECOMMENDED_OPTION,
        considered_options=CONSIDERED_OPTIONS,
        rejected_options=REJECTED_OPTIONS,
        required_backend_commands=REQUIRED_BACKEND_COMMANDS,
        required_safety_warnings=REQUIRED_SAFETY_WARNINGS,
        recommended_next_step=RECOMMENDED_NEXT_STEP,
        json_data=json_data,
        markdown=markdown,
        warnings=(PLANNING_WARNING,),
        errors=(),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    if output_dir is not None:
        _write_planning_files(Path(output_dir), result)
    return result


def render_engineering_gui_planning_markdown(json_data: dict[str, Any]) -> str:
    """Render GUI planning decision as Markdown."""
    option_rows = []
    for option in json_data["option_details"]:
        option_rows.append(
            (
                "| {option} | {advantages} | {disadvantages} | "
                "{dependency} | {risks} | {stage} |"
            ).format(
                option=option["option"],
                advantages="; ".join(option["advantages"]),
                disadvantages="; ".join(option["disadvantages"]),
                dependency=option["dependency_impact"],
                risks="; ".join(option["safety_risks"]),
                stage=option["recommended_stage"],
            )
        )

    lines = [
        "# Engineering GUI Planning Decision",
        "",
        PLANNING_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Current Project State",
        "",
        "- The deterministic workflow already produces HTML, Markdown, JSON, "
        "manifests, and ZIP packages.",
        "- K63 provides a future GUI/desktop wrapper interface contract.",
        "- A working GUI is intentionally postponed.",
        "",
        "## Considered Interface Options",
        "",
        "| Option | Pros | Cons | Dependencies | Safety risk | Recommended stage |",
        "| --- | --- | --- | --- | --- | --- |",
        *option_rows,
        "",
        "## Recommended Option",
        "",
        f"`{json_data['recommended_option']}`",
        "",
        "This keeps the CLI/workflow layer as the authority, uses existing "
        "static report outputs, avoids heavy UI dependencies, and lowers the "
        "risk that advisory ML will be read as a design checker.",
        "",
        "## Why Heavy GUI Dependencies Are Postponed",
        "",
        "- The deterministic report package is already reviewable without a GUI.",
        "- Streamlit, Gradio, PyQt/PySide, FastAPI, Flask, and Electron add "
        "runtime or packaging complexity.",
        "- More UI surface increases the risk of hiding engineer-review warnings.",
        "- Project approval still requires deterministic checks and engineer review.",
        "",
        "## Required Backend Commands",
        "",
        *_bullet_lines(tuple(json_data["required_backend_commands"])),
        "",
        "## Required Screens/Panels",
        "",
        *_bullet_lines(tuple(json_data["required_screens_or_panels"])),
        "",
        "## Safety Constraints",
        "",
        *_bullet_lines(tuple(json_data["required_safety_warnings"])),
        "",
        "## Recommended Next Step",
        "",
        f"`{json_data['recommended_next_step']}`",
        "",
        "## Limitations",
        "",
        "- K64 does not implement UI.",
        "- K64 does not add UI dependencies.",
        "- K64 does not change formulas, materials, or reinforcement selection.",
        "- K64 does not approve ML for project use.",
    ]
    return "\n".join(lines) + "\n"


def _write_planning_files(output_dir: Path, result: EngineeringGUIPlanningResult) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "engineering_gui_planning_decision.json").write_text(
        json.dumps(result.json_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "engineering_gui_planning_decision.md").write_text(
        result.markdown,
        encoding="utf-8",
    )


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]
