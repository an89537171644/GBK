"""Batch report generation for rectangular design inputs."""

from __future__ import annotations

import json
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.report.design_report import DesignCalculationReport, build_rectangular_design_report
from sp63_core.report.design_report_input import load_rectangular_design_input_from_json

BATCH_REPORT_TYPE = "batch_design_report_index"
BATCH_REPORT_WARNING = (
    "Batch design reports are draft review artifacts; engineer review is required."
)


@dataclass(frozen=True)
class BatchDesignReportResult:
    """Result of batch design report generation."""

    status: str
    input_count: int
    report_count: int
    passed_count: int
    review_count: int
    failed_count: int
    output_dir: str
    index_markdown: str
    index_json: dict[str, Any]
    warnings: tuple[str, ...]
    requires_engineer_review: bool = True


def build_batch_design_reports(
    *,
    input_paths: Iterable[Path],
    output_dir: Path,
    include_html: bool = True,
) -> BatchDesignReportResult:
    """Build report bundles and shared indexes for several input JSON files."""
    from sp63_core.design import design_rectangular_element

    paths = tuple(Path(path) for path in input_paths)
    output_dir.mkdir(parents=True, exist_ok=True)
    cases: list[dict[str, Any]] = []
    warnings: list[str] = [BATCH_REPORT_WARNING]
    report_count = 0

    for index, input_path in enumerate(paths, start=1):
        case_id = f"case_{index:03d}"
        case_dir = output_dir / case_id
        try:
            design_input = load_rectangular_design_input_from_json(input_path)
            design_result = design_rectangular_element(design_input)
            report = build_rectangular_design_report(design_result, include_html=include_html)
            output_files = _write_case_bundle(
                report=report,
                input_path=input_path,
                case_dir=case_dir,
            )
            report_count += 1
            cases.append(
                _case_index_row(
                    case_id=case_id,
                    input_path=input_path,
                    report=report,
                    report_path=output_files["markdown"],
                )
            )
        except Exception as exc:  # noqa: BLE001 - batch must report per-input failures.
            warning = f"{case_id}: input_error: {exc}"
            warnings.append(warning)
            case_dir.mkdir(parents=True, exist_ok=True)
            if input_path.exists():
                shutil.copyfile(input_path, case_dir / "input.json")
            cases.append(
                {
                    "case_id": case_id,
                    "input_file": str(input_path),
                    "strength_status": "input_error",
                    "serviceability_status": "input_error",
                    "overall_status": "input_error",
                    "warnings_count": 1,
                    "report_path": "",
                    "requires_engineer_review": True,
                    "error": str(exc),
                }
            )

    passed_count = sum(1 for case in cases if case["overall_status"] == "pass")
    failed_count = sum(1 for case in cases if case["overall_status"] == "fail")
    review_count = len(cases) - passed_count - failed_count
    if failed_count:
        status = "fail"
    elif review_count:
        status = "review_required"
    else:
        status = "pass"

    index_json = {
        "report_type": BATCH_REPORT_TYPE,
        "status": status,
        "input_count": len(paths),
        "report_count": report_count,
        "passed_count": passed_count,
        "review_count": review_count,
        "failed_count": failed_count,
        "output_dir": str(output_dir),
        "warnings": warnings,
        "requires_engineer_review": True,
        "cases": cases,
    }
    index_markdown = _render_index_markdown(index_json)
    (output_dir / "index.md").write_text(index_markdown, encoding="utf-8")
    (output_dir / "index.json").write_text(
        json.dumps(index_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return BatchDesignReportResult(
        status=status,
        input_count=len(paths),
        report_count=report_count,
        passed_count=passed_count,
        review_count=review_count,
        failed_count=failed_count,
        output_dir=str(output_dir),
        index_markdown=index_markdown,
        index_json=index_json,
        warnings=tuple(warnings),
        requires_engineer_review=True,
    )


def _write_case_bundle(
    *,
    report: DesignCalculationReport,
    input_path: Path,
    case_dir: Path,
) -> dict[str, str]:
    case_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = case_dir / "report.md"
    json_path = case_dir / "report.json"
    html_path = case_dir / "report.html"
    input_copy_path = case_dir / "input.json"

    report_payload = _design_report_json_payload(report)
    markdown_path.write_text(report.markdown, encoding="utf-8")
    json_path.write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    html_path.write_text(report.html if report.html is not None else "", encoding="utf-8")
    shutil.copyfile(input_path, input_copy_path)
    return {
        "markdown": str(markdown_path),
        "json": str(json_path),
        "html": str(html_path),
        "input": str(input_copy_path),
    }


def _design_report_json_payload(report: DesignCalculationReport) -> dict[str, Any]:
    data = report.json_data
    return {
        "command": "design-report",
        "source": "batch_input_json",
        "report_type": report.report_type,
        "status": report.status,
        "strength_status": report.strength_status,
        "serviceability_status": report.serviceability_status,
        "overall_status": report.overall_status,
        "requires_engineer_review": report.requires_engineer_review,
        "warnings": list(report.warnings),
        "input_data": data["input_data"],
        "materials": data["materials"],
        "geometry": data["geometry"],
        "reinforcement": data["reinforcement"],
        "checks": data["checks"],
        "limitations": data["limitations"],
        "report": data,
    }


def _case_index_row(
    *,
    case_id: str,
    input_path: Path,
    report: DesignCalculationReport,
    report_path: str,
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "input_file": str(input_path),
        "strength_status": report.strength_status,
        "serviceability_status": report.serviceability_status,
        "overall_status": report.overall_status,
        "warnings_count": len(report.warnings),
        "report_path": report_path,
        "requires_engineer_review": report.requires_engineer_review,
    }


def _render_index_markdown(index_json: dict[str, Any]) -> str:
    lines = [
        "# Batch Design Report Index",
        "",
        "requires_engineer_review = true",
        "",
        "## Summary",
        "",
        "| field | value |",
        "|---|---|",
        f"| status | {index_json['status']} |",
        f"| input_count | {index_json['input_count']} |",
        f"| report_count | {index_json['report_count']} |",
        f"| passed_count | {index_json['passed_count']} |",
        f"| review_count | {index_json['review_count']} |",
        f"| failed_count | {index_json['failed_count']} |",
        "",
        "## Cases",
        "",
        "| case_id | input_file | strength_status | serviceability_status | "
        "overall_status | warnings_count | report_path | requires_engineer_review |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for case in index_json["cases"]:
        lines.append(
            "| {case_id} | {input_file} | {strength_status} | {serviceability_status} | "
            "{overall_status} | {warnings_count} | {report_path} | "
            "{requires_engineer_review} |".format(**case)
        )
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in index_json["warnings"])
    return "\n".join(lines) + "\n"
