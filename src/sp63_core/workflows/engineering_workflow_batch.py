"""Batch runner for engineering workflow input JSON folders."""

from __future__ import annotations

import html
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sp63_core.workflows.engineering_workflow import run_engineering_workflow

BATCH_WORKFLOW_WARNING = (
    "Batch engineering workflow does not certify designs. Deterministic SP63 "
    "verification and engineer review are mandatory for every case."
)


@dataclass(frozen=True)
class BatchEngineeringWorkflowResult:
    """Summary of a batch engineering workflow run."""

    status: str
    batch_status: str
    command_exit_status: str
    input_dir: str
    output_dir: str
    case_count: int
    passed_count: int
    review_required_count: int
    failed_count: int
    skipped_count: int
    passed_cases: tuple[str, ...]
    review_required_cases: tuple[str, ...]
    failed_cases: tuple[str, ...]
    skipped_cases: tuple[str, ...]
    case_results: tuple[dict[str, Any], ...]
    batch_index_path: str
    batch_summary_json_path: str
    batch_summary_markdown_path: str
    recommendations: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def run_engineering_workflow_batch(
    *,
    input_dir: Path,
    output_dir: Path,
    with_preflight: bool = True,
    with_index: bool = True,
    create_zip: bool = True,
) -> BatchEngineeringWorkflowResult:
    """Run engineering workflow for every JSON file in an input directory."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = [BATCH_WORKFLOW_WARNING]
    errors: list[str] = []
    case_results: list[dict[str, Any]] = []

    if not input_path.exists() or not input_path.is_dir():
        errors.append(f"input directory does not exist: {input_path}")
        input_files: tuple[Path, ...] = ()
    else:
        input_files = tuple(sorted(input_path.glob("*.json")))

    if not input_files and not errors:
        warnings.append("no input JSON files found for batch workflow")

    for index, input_file in enumerate(input_files, start=1):
        case_id = f"case_{index:04d}"
        case_output_dir = output_path / case_id
        try:
            workflow_result = run_engineering_workflow(
                input_json_path=input_file,
                output_dir=case_output_dir,
                create_zip=create_zip,
                with_preflight=with_preflight,
                with_index=with_index,
            )
            case_results.append(
                {
                    "case_id": case_id,
                    "input_json_path": str(input_file),
                    "output_dir": str(case_output_dir),
                    "workflow_status": workflow_result.workflow_status,
                    "preflight_status": workflow_result.preflight_status,
                    "deterministic_report_status": workflow_result.deterministic_report_status,
                    "archive_validation_status": workflow_result.archive_validation_status,
                    "zip_status": workflow_result.zip_status,
                    "index_status": workflow_result.index_status,
                    "index_path": workflow_result.index_path,
                    "warnings_count": len(workflow_result.warnings),
                    "errors_count": len(workflow_result.errors),
                    "warnings": list(workflow_result.warnings),
                    "errors": list(workflow_result.errors),
                }
            )
        except (OSError, ValueError) as exc:
            case_results.append(
                {
                    "case_id": case_id,
                    "input_json_path": str(input_file),
                    "output_dir": str(case_output_dir),
                    "workflow_status": "fail",
                    "preflight_status": None,
                    "deterministic_report_status": "not_run",
                    "archive_validation_status": "not_run",
                    "zip_status": "skipped",
                    "index_status": None,
                    "index_path": None,
                    "warnings_count": 0,
                    "errors_count": 1,
                    "warnings": [],
                    "errors": [f"batch case failed: {exc}"],
                }
            )

    passed_cases = tuple(
        case["case_id"] for case in case_results if case["workflow_status"] == "pass"
    )
    review_required_cases = tuple(
        case["case_id"] for case in case_results if case["workflow_status"] == "review_required"
    )
    failed_cases = tuple(
        case["case_id"] for case in case_results if case["workflow_status"] == "fail"
    )
    skipped_cases = tuple(
        case["case_id"] for case in case_results if case["workflow_status"] == "skipped"
    )
    passed_count = len(passed_cases)
    review_required_count = len(review_required_cases)
    failed_count = len(failed_cases)
    skipped_count = len(skipped_cases)
    batch_status = _batch_status(
        errors=errors,
        failed_count=failed_count,
        review_required_count=review_required_count,
        case_count=len(case_results),
        skipped_count=skipped_count,
    )
    command_exit_status = "completed" if not errors else "failed"
    recommendations = _batch_recommendations(
        batch_status=batch_status,
        failed_count=failed_count,
        review_required_count=review_required_count,
        skipped_count=skipped_count,
        case_count=len(case_results),
    )

    batch_summary_json_path = output_path / "batch_workflow_summary.json"
    batch_summary_markdown_path = output_path / "batch_workflow_summary.md"
    batch_index_path = output_path / "batch_index.html"
    readme_path = output_path / "README_BATCH_WORKFLOW.md"
    result = BatchEngineeringWorkflowResult(
        status=batch_status,
        batch_status=batch_status,
        command_exit_status=command_exit_status,
        input_dir=str(input_path),
        output_dir=str(output_path),
        case_count=len(case_results),
        passed_count=passed_count,
        review_required_count=review_required_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
        passed_cases=passed_cases,
        review_required_cases=review_required_cases,
        failed_cases=failed_cases,
        skipped_cases=skipped_cases,
        case_results=tuple(case_results),
        batch_index_path=str(batch_index_path),
        batch_summary_json_path=str(batch_summary_json_path),
        batch_summary_markdown_path=str(batch_summary_markdown_path),
        recommendations=recommendations,
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    batch_summary_json_path.write_text(
        json.dumps(_batch_summary_payload(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    batch_summary_markdown_path.write_text(_render_batch_summary_markdown(result), encoding="utf-8")
    batch_index_path.write_text(_render_batch_index_html(result), encoding="utf-8")
    readme_path.write_text(_render_batch_readme(result), encoding="utf-8")
    return result


def _batch_status(
    *,
    errors: list[str],
    failed_count: int,
    review_required_count: int,
    case_count: int,
    skipped_count: int,
) -> str:
    if errors or failed_count:
        return "fail"
    if case_count == 0 or skipped_count:
        return "review_required"
    if review_required_count:
        return "review_required"
    return "pass"


def _batch_recommendations(
    *,
    batch_status: str,
    failed_count: int,
    review_required_count: int,
    skipped_count: int,
    case_count: int,
) -> tuple[str, ...]:
    recommendations: list[str] = []
    if case_count == 0:
        recommendations.append("add valid input JSON files before running batch workflow")
    if failed_count:
        recommendations.append("open failed case folders and fix input/preflight errors first")
    if skipped_count:
        recommendations.append("review skipped cases before relying on the batch summary")
    if review_required_count:
        recommendations.append("perform engineer review for review_required cases")
    if batch_status == "pass":
        recommendations.append("archive batch outputs only after engineer review")
    recommendations.append("keep deterministic SP63 verification as the authority for every case")
    return tuple(dict.fromkeys(recommendations))


def _batch_summary_payload(result: BatchEngineeringWorkflowResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["report_type"] = "batch_engineering_workflow_summary"
    return payload


def _render_batch_summary_markdown(result: BatchEngineeringWorkflowResult) -> str:
    lines = [
        "# Batch Engineering Workflow Summary",
        "",
        BATCH_WORKFLOW_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Summary",
        "",
        f"- batch_status: `{result.batch_status}`",
        f"- command_exit_status: `{result.command_exit_status}`",
        f"- input_dir: `{result.input_dir}`",
        f"- output_dir: `{result.output_dir}`",
        f"- case_count: `{result.case_count}`",
        f"- passed_count: `{result.passed_count}`",
        f"- review_required_count: `{result.review_required_count}`",
        f"- failed_count: `{result.failed_count}`",
        f"- skipped_count: `{result.skipped_count}`",
        f"- passed_cases: `{', '.join(result.passed_cases) or 'none'}`",
        f"- review_required_cases: `{', '.join(result.review_required_cases) or 'none'}`",
        f"- failed_cases: `{', '.join(result.failed_cases) or 'none'}`",
        f"- batch_index_path: `{result.batch_index_path}`",
        "",
        "## Cases",
        "",
        "| case_id | workflow_status | preflight_status | deterministic_report_status | index |",
        "|---|---|---|---|---|",
    ]
    for case in result.case_results:
        lines.append(
            "| {case_id} | {workflow_status} | {preflight_status} | "
            "{deterministic_report_status} | {index_path} |".format(
                case_id=case["case_id"],
                workflow_status=case["workflow_status"],
                preflight_status=case["preflight_status"],
                deterministic_report_status=case["deterministic_report_status"],
                index_path=case["index_path"],
            )
        )
    lines.extend(
        [
            "",
            "## Recommendations",
            "",
            *_bullet_lines(result.recommendations),
            "",
            "## Warnings",
            "",
            *_bullet_lines(result.warnings),
            "",
            "## Errors",
            "",
            *_bullet_lines(result.errors),
            "",
            "## Safety",
            "",
            "- Batch workflow does not certify designs.",
            "- Each deterministic report remains draft-MVP evidence.",
            "- Engineer review remains mandatory.",
            "- ML remains advisory-only.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_batch_index_html(result: BatchEngineeringWorkflowResult) -> str:
    rows = []
    for case in result.case_results:
        link_target = case["index_path"] or str(Path(case["output_dir"]) / "workflow_summary.md")
        href = _relative_href(Path(link_target), Path(result.batch_index_path).parent)
        status = str(case["workflow_status"])
        rows.append(
            "<tr>"
            f"<td><code>{html.escape(case['case_id'])}</code></td>"
            '<td><code class="status status-{status_class}">{status}</code></td>'.format(
                status_class=html.escape(status),
                status=html.escape(status),
            )
            + f"<td><code>{html.escape(str(case['preflight_status']))}</code></td>"
            f"<td><code>{html.escape(case['deterministic_report_status'])}</code></td>"
            f'<td><a href="{html.escape(href, quote=True)}">case report</a></td>'
            "</tr>"
        )
    warning_items = [f"<li>{html.escape(warning)}</li>" for warning in result.warnings]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            "  <title>Batch Engineering Workflow</title>",
            "  <style>",
            "    body { font-family: Arial, sans-serif; margin: 2rem; line-height: 1.45; }",
            "    main { max-width: 1100px; margin: 0 auto; }",
            "    .warning { border: 2px solid #8a4b00; padding: 1rem; background: #fff7e6; }",
            "    table { border-collapse: collapse; width: 100%; margin: 1rem 0; }",
            "    th, td { border: 1px solid #ccc; padding: 0.4rem; }",
            "    code { background: #f4f4f4; padding: 0.1rem 0.25rem; }",
            "    .status-pass { color: #075d2a; font-weight: 700; }",
            "    .status-review_required { color: #8a4b00; font-weight: 700; }",
            "    .status-fail { color: #8a1f11; font-weight: 700; }",
            "  </style>",
            "</head>",
            "<body>",
            "<main>",
            "<h1>Batch Engineering Workflow</h1>",
            '<section class="warning"><strong>Warning:</strong> '
            f"{html.escape(BATCH_WORKFLOW_WARNING)}</section>",
            "<section>",
            "<h2>Summary</h2>",
            "<ul>",
            f"<li>batch_status: <code>{html.escape(result.batch_status)}</code></li>",
            f"<li>command_exit_status: <code>{html.escape(result.command_exit_status)}</code></li>",
            f"<li>case_count: <code>{result.case_count}</code></li>",
            f"<li>passed_count: <code>{result.passed_count}</code></li>",
            f"<li>review_required_count: <code>{result.review_required_count}</code></li>",
            f"<li>failed_count: <code>{result.failed_count}</code></li>",
            "<li>ml_ready_for_project_use: <code>false</code></li>",
            "</ul>",
            "</section>",
            "<section>",
            "<h2>Cases</h2>",
            "<table>",
            "<thead><tr><th>Case</th><th>Status</th><th>Preflight</th><th>Report</th><th>Link</th></tr></thead>",
            "<tbody>",
            *(rows or ["<tr><td colspan=\"5\">No cases found.</td></tr>"]),
            "</tbody>",
            "</table>",
            "</section>",
            "<section>",
            "<h2>Recommendations</h2>",
            "<ul>",
            *(
                [
                    f"<li>{html.escape(recommendation)}</li>"
                    for recommendation in result.recommendations
                ]
                or ["<li>none</li>"]
            ),
            "</ul>",
            "</section>",
            "<section>",
            "<h2>Warnings</h2>",
            "<ul>",
            *(warning_items or ["<li>none</li>"]),
            "</ul>",
            "</section>",
            "</main>",
            "</body>",
            "</html>",
            "",
        ]
    )


def _render_batch_readme(result: BatchEngineeringWorkflowResult) -> str:
    lines = [
        "# Batch Engineering Workflow",
        "",
        BATCH_WORKFLOW_WARNING,
        "",
        "## Contents",
        "",
        "- one `case_####/` folder per input JSON file;",
        "- `batch_workflow_summary.json`;",
        "- `batch_workflow_summary.md`;",
        "- `batch_index.html`;",
        "- `README_BATCH_WORKFLOW.md`.",
        "",
        "## Status",
        "",
        f"- batch_status: `{result.batch_status}`",
        f"- command_exit_status: `{result.command_exit_status}`",
        f"- case_count: `{result.case_count}`",
        f"- passed_count: `{result.passed_count}`",
        f"- failed_count: `{result.failed_count}`",
        f"- review_required_count: `{result.review_required_count}`",
        f"- failed_cases: `{', '.join(result.failed_cases) or 'none'}`",
        "",
        "## Recommendations",
        "",
        *_bullet_lines(result.recommendations),
        "",
        "## Safety",
        "",
        "- This batch does not certify designs.",
        "- Review every case folder manually.",
        "- Deterministic SP63 checks remain mandatory.",
        "- Engineer review remains mandatory.",
        "- ML remains advisory-only.",
    ]
    return "\n".join(lines) + "\n"


def _relative_href(path: Path, start: Path) -> str:
    return os.path.relpath(path, start=start).replace("\\", "/")


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]
