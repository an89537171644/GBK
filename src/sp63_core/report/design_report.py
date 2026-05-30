"""Engineering report export for rectangular design results."""

from dataclasses import asdict, dataclass
from html import escape
from typing import Any

REPORT_TYPE = "rectangular_design_calculation_report"
DRAFT_REPORT_WARNING = (
    "Report generated from the draft-MVP calculation core. Engineer review is "
    "required. Full SP 63 text is not stored in this repository."
)
MATERIAL_REVIEW_NOTE = (
    "Material values require engineer verification unless an engineer-filled "
    "verification CSV has been accepted separately."
)
LIMITATIONS = (
    "rectangular reinforced concrete beam only",
    "draft-MVP calculation report",
    "not a certified design conclusion",
    "external validation must be completed separately",
    "material verification must be completed separately",
    "ML is advisory-only",
    "deterministic SP63 checks are mandatory",
    "engineer review is required",
)


@dataclass(frozen=True)
class DesignCalculationReport:
    """Rendered design calculation report."""

    title: str
    report_type: str
    status: str
    strength_status: str
    serviceability_status: str
    overall_status: str
    warnings: tuple[str, ...]
    markdown: str
    html: str | None
    json_data: dict[str, Any]
    requires_engineer_review: bool = True


def build_rectangular_design_report(
    result: Any,
    *,
    include_html: bool = False,
) -> DesignCalculationReport:
    """Build Markdown, optional HTML, and JSON report data for a design result."""
    json_data = _build_json_data(result)
    markdown = render_rectangular_design_report_markdown(result)
    html = render_rectangular_design_report_html(result) if include_html else None
    warnings = tuple(json_data["warnings"])
    return DesignCalculationReport(
        title="Rectangular Design Calculation Report",
        report_type=REPORT_TYPE,
        status=result.status,
        strength_status=result.strength_status,
        serviceability_status=result.serviceability_status,
        overall_status=result.overall_status,
        warnings=warnings,
        markdown=markdown,
        html=html,
        json_data=json_data,
        requires_engineer_review=True,
    )


def render_rectangular_design_report_markdown(result: Any) -> str:
    """Render a rectangular design result as Markdown."""
    data = _build_json_data(result)
    lines: list[str] = [
        "# Rectangular Design Calculation Report",
        "",
        "requires_engineer_review = true",
        "",
        "## Draft Warning",
        "",
        DRAFT_REPORT_WARNING,
        "",
        "## Input Data",
        "",
        *_dict_table(data["input_data"]),
        "",
        "## Geometry",
        "",
        *_dict_table(data["geometry"]),
        "",
        "## Materials",
        "",
        MATERIAL_REVIEW_NOTE,
        "",
        *_dict_table(data["materials"]),
        "",
        "## Longitudinal Reinforcement",
        "",
        *_dict_table(data["reinforcement"]["longitudinal"]),
        "",
        "## Transverse Reinforcement",
        "",
        *_dict_table(data["reinforcement"]["transverse"]),
        "",
        "## Bending Check",
        "",
        *_dict_table(data["checks"].get("bending", {})),
        "",
        "## Shear Check",
        "",
        *_dict_table(data["checks"].get("shear", {})),
        "",
        "## Serviceability Checks",
        "",
    ]
    serviceability_names = ("crack_formation", "crack_width", "deflection")
    for name in serviceability_names:
        check = data["checks"].get(name)
        if check is None:
            lines.extend([f"### {name}", "", "not_checked", ""])
            continue
        lines.extend([f"### {name}", "", *_dict_table(check), ""])

    lines.extend(
        [
            "## Status Summary",
            "",
            *_dict_table(
                {
                    "status": data["status"],
                    "strength_status": data["strength_status"],
                    "serviceability_status": data["serviceability_status"],
                    "overall_status": data["overall_status"],
                }
            ),
            "",
            "## Warnings",
            "",
        ]
    )
    if data["warnings"]:
        lines.extend(f"- {warning}" for warning in data["warnings"])
    else:
        lines.append("- none")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {limitation}" for limitation in data["limitations"])
    return "\n".join(lines) + "\n"


def render_rectangular_design_report_html(result: Any) -> str:
    """Render a rectangular design result as simple static HTML."""
    markdown = render_rectangular_design_report_markdown(result)
    body = "\n".join(f"<pre>{escape(markdown)}</pre>".splitlines())
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head><meta charset=\"utf-8\"><title>Rectangular Design Report</title></head>\n"
        f"<body>{body}</body>\n"
        "</html>\n"
    )


def _build_json_data(result: Any) -> dict[str, Any]:
    protocol = None if result.protocol is None else result.protocol.as_dict()
    protocol_checks = {} if protocol is None else protocol["checks"]
    warnings = _combined_warnings(result)
    return {
        "report_type": REPORT_TYPE,
        "status": result.status,
        "strength_status": result.strength_status,
        "serviceability_status": result.serviceability_status,
        "overall_status": result.overall_status,
        "requires_engineer_review": True,
        "input_data": asdict(result.input_data),
        "materials": _materials_data(result),
        "geometry": _geometry_data(result, protocol),
        "reinforcement": _reinforcement_data(result),
        "checks": _checks_data(protocol_checks),
        "warnings": list(warnings),
        "limitations": list(LIMITATIONS),
        "protocol": protocol,
    }


def _materials_data(result: Any) -> dict[str, Any]:
    return {
        "concrete_class": result.concrete.class_name,
        "concrete": {
            "Rb": result.concrete.Rb,
            "Rbt": result.concrete.Rbt,
            "Rbser": result.concrete.Rbser,
            "Rbtser": result.concrete.Rbtser,
            "Eb": result.concrete.Eb,
            "requires_engineer_review": result.concrete.draft_requires_engineer_review,
        },
        "longitudinal_rebar_class": result.longitudinal_rebar.class_name,
        "longitudinal_rebar": {
            "Rsn": result.longitudinal_rebar.Rsn,
            "Rs": result.longitudinal_rebar.Rs,
            "Rsser": result.longitudinal_rebar.Rsser,
            "Rsc_short": result.longitudinal_rebar.Rsc_short,
            "Rsc_long": result.longitudinal_rebar.Rsc_long,
            "Rsw": result.longitudinal_rebar.Rsw,
            "Es": result.longitudinal_rebar.Es,
            "requires_engineer_review": result.longitudinal_rebar.draft_requires_engineer_review,
        },
        "stirrup_rebar_class": result.stirrup_rebar.class_name,
        "stirrup_rebar": {
            "Rsn": result.stirrup_rebar.Rsn,
            "Rs": result.stirrup_rebar.Rs,
            "Rsser": result.stirrup_rebar.Rsser,
            "Rsc_short": result.stirrup_rebar.Rsc_short,
            "Rsc_long": result.stirrup_rebar.Rsc_long,
            "Rsw": result.stirrup_rebar.Rsw,
            "Es": result.stirrup_rebar.Es,
            "requires_engineer_review": result.stirrup_rebar.draft_requires_engineer_review,
        },
        "material_verification_note": MATERIAL_REVIEW_NOTE,
    }


def _geometry_data(
    result: Any,
    protocol: dict[str, Any] | None,
) -> dict[str, Any]:
    selected_longitudinal = result.selected_longitudinal
    selected_transverse = result.selected_transverse
    if protocol is not None:
        geometry = dict(protocol["geometry"])
        if selected_longitudinal is not None:
            geometry["selected_main_bar_diameter"] = selected_longitudinal.diameter
            geometry["selected_longitudinal_scheme"] = selected_longitudinal.scheme
        if selected_transverse is not None:
            geometry["selected_transverse_scheme"] = selected_transverse.scheme
        return geometry
    return {
        "b": result.section.b,
        "h": result.section.h,
        "cover": result.section.cover,
        "stirrup_diameter_for_geometry": result.section.stirrup_diameter,
        "h0": result.section.effective_depth(),
        "selected_main_bar_diameter": (
            None if selected_longitudinal is None else selected_longitudinal.diameter
        ),
        "selected_longitudinal_scheme": (
            None if selected_longitudinal is None else selected_longitudinal.scheme
        ),
        "selected_transverse_scheme": (
            None if selected_transverse is None else selected_transverse.scheme
        ),
    }


def _reinforcement_data(result: Any) -> dict[str, Any]:
    longitudinal = result.selected_longitudinal
    transverse = result.selected_transverse
    return {
        "longitudinal": (
            {"status": "not_selected"}
            if longitudinal is None
            else {
                "scheme": longitudinal.scheme,
                "bar_count": longitudinal.bar_count,
                "diameter": longitudinal.diameter,
                "As": longitudinal.As,
                "h0": longitudinal.section.effective_depth(),
                "reinforcement_ratio_percent": longitudinal.constructive.intermediate_values[
                    "reinforcement_ratio_percent"
                ],
                "constructive_status": longitudinal.constructive.status,
                "layout_feasible": longitudinal.layout.layout_feasible,
                "status": longitudinal.status,
            }
        ),
        "transverse": (
            {"status": "not_selected"}
            if transverse is None
            else {
                "scheme": transverse.scheme,
                "diameter": transverse.diameter,
                "Asw": transverse.Asw,
                "spacing": transverse.spacing,
                "legs": transverse.legs,
                "constructive_status": transverse.constructive.status,
                "status": transverse.status,
            }
        ),
    }


def _checks_data(checks: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, check in checks.items():
        compact = dict(check)
        if "intermediate_values" in compact:
            compact["intermediate_values"] = dict(compact["intermediate_values"])
        result[name] = compact
    return result


def _combined_warnings(result: Any) -> tuple[str, ...]:
    warnings: list[str] = [DRAFT_REPORT_WARNING, MATERIAL_REVIEW_NOTE]
    warnings.extend(result.warnings)
    if result.protocol is not None:
        warnings.extend(result.protocol.warnings)
    return tuple(dict.fromkeys(warnings))


def _dict_table(values: dict[str, Any]) -> list[str]:
    if not values:
        return ["not_available"]
    lines = ["| field | value |", "|---|---|"]
    for key, value in values.items():
        lines.append(f"| {key} | {_format_value(value)} |")
    return lines


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, dict):
        return ", ".join(f"{key}={_format_value(item)}" for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return ", ".join(_format_value(item) for item in value)
    return str(value)
