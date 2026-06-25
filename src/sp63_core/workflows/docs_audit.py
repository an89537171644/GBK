"""Documentation link and CLI command audit helpers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

DOCS_AUDIT_WARNING = (
    "Documentation audit is a completeness check only. It does not certify "
    "calculations, approve project use, or make ML project-ready."
)

REQUIRED_DOCUMENTATION_FILES: tuple[str, ...] = (
    "README.md",
    "docs/engineering_audit.md",
    "docs/validation_report.md",
    "docs/implementation_status.md",
    "docs/engineering_workflow_runner.md",
    "docs/engineering_workflow_batch.md",
    "docs/engineering_workflow_batch_valid_examples.md",
    "docs/project_template_package.md",
    "docs/docs_audit.md",
    "docs/ci_safety_workflow.md",
    "docs/protected_files_guard.md",
    "docs/user_manual/README.md",
    "docs/user_manual/quickstart.md",
    "docs/user_manual/input_data.md",
    "docs/user_manual/preflight_validation.md",
    "docs/user_manual/workflow_run.md",
    "docs/user_manual/report_index.md",
    "docs/user_manual/batch_workflow.md",
    "docs/user_manual/evidence_templates.md",
    "docs/user_manual/project_template.md",
    "docs/user_manual/ml_advisory_limits.md",
    "docs/user_manual/troubleshooting.md",
    "docs/user_manual/acceptance_checklist.md",
)

REQUIRED_CLI_EXAMPLES: tuple[str, ...] = (
    "python -m sp63_core validate --golden",
    "python -m sp63_core validate --generate-dataset-limit 20 --json",
    "python -m sp63_core materials-audit --json",
    "python -m sp63_core materials-audit --verification-template",
    "python -m sp63_core manual-cases --json",
    "python -m sp63_core external-validation --sample --json",
    "python -m sp63_core ml-proposal-verify --json",
    "python -m sp63_core input-form-schema",
    "python -m sp63_core input-preflight",
    "python -m sp63_core input-form-preview",
    "python -m sp63_core engineering-workflow",
    "python -m sp63_core engineering-workflow-batch",
    "python -m sp63_core diagnostics-catalog --json",
    "python -m sp63_core docs-audit --json",
    "python -m sp63_core evidence-templates",
    "python -m sp63_core protected-files-check --json",
    "python -m sp63_core user-manual-index --json",
    "python -m sp63_core release-candidate-report",
    "python -m sp63_core project-template",
)

_MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
_IGNORED_MARKDOWN_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "build",
    "dist",
    "reports",
}


@dataclass(frozen=True)
class DocsAuditResult:
    """Documentation audit result."""

    status: str
    docs_audit_status: str
    root_dir: str
    markdown_files_count: int
    docs_checked: tuple[str, ...]
    required_files_missing: tuple[str, ...]
    local_link_count: int
    missing_local_links: tuple[str, ...]
    required_commands_present: tuple[str, ...]
    required_commands_missing: tuple[str, ...]
    output_dir: str | None
    json_path: str | None
    markdown_path: str | None
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_docs_audit_report(
    *,
    root_dir: Path = Path("."),
    output_dir: Path | None = None,
    required_files: tuple[str, ...] = REQUIRED_DOCUMENTATION_FILES,
    required_cli_examples: tuple[str, ...] = REQUIRED_CLI_EXAMPLES,
) -> DocsAuditResult:
    """Audit local documentation links and required CLI example snippets."""
    root_path = Path(root_dir)
    markdown_files = _iter_markdown_files(root_path)
    docs_text = "\n".join(
        path.read_text(encoding="utf-8") for path in markdown_files if path.is_file()
    )

    required_files_missing = tuple(
        file_name for file_name in required_files if not (root_path / file_name).exists()
    )
    local_links, missing_local_links = _scan_local_links(root_path, markdown_files)
    required_commands_present = tuple(
        command for command in required_cli_examples if command in docs_text
    )
    required_commands_missing = tuple(
        command for command in required_cli_examples if command not in docs_text
    )

    errors = tuple(
        [f"required documentation file missing: {path}" for path in required_files_missing]
        + [f"local markdown link target missing: {link}" for link in missing_local_links]
        + [f"required CLI example missing: {command}" for command in required_commands_missing]
    )
    status = "fail" if errors else "pass"
    result = DocsAuditResult(
        status=status,
        docs_audit_status=status,
        root_dir=str(root_path),
        markdown_files_count=len(markdown_files),
        docs_checked=tuple(str(path) for path in markdown_files),
        required_files_missing=required_files_missing,
        local_link_count=len(local_links),
        missing_local_links=missing_local_links,
        required_commands_present=required_commands_present,
        required_commands_missing=required_commands_missing,
        output_dir=str(output_dir) if output_dir is not None else None,
        json_path=str(Path(output_dir) / "docs_audit_report.json") if output_dir else None,
        markdown_path=str(Path(output_dir) / "docs_audit_report.md") if output_dir else None,
        warnings=(DOCS_AUDIT_WARNING,),
        errors=errors,
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    if output_dir is not None:
        _write_docs_audit_report(Path(output_dir), result)
    return result


def render_docs_audit_markdown(result: DocsAuditResult) -> str:
    """Render a Markdown summary for a documentation audit result."""
    lines = [
        "# Documentation Audit",
        "",
        DOCS_AUDIT_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Summary",
        "",
        f"- docs_audit_status: `{result.docs_audit_status}`",
        f"- markdown_files_count: `{result.markdown_files_count}`",
        f"- local_link_count: `{result.local_link_count}`",
        f"- missing_local_links: `{len(result.missing_local_links)}`",
        f"- required_commands_missing: `{len(result.required_commands_missing)}`",
        "",
        "## Missing Required Files",
        "",
        *_bullet_lines(result.required_files_missing),
        "",
        "## Missing Local Links",
        "",
        *_bullet_lines(result.missing_local_links),
        "",
        "## Missing CLI Examples",
        "",
        *_bullet_lines(result.required_commands_missing),
    ]
    return "\n".join(lines) + "\n"


def _iter_markdown_files(root_path: Path) -> tuple[Path, ...]:
    return tuple(
        sorted(
            path
            for path in root_path.rglob("*.md")
            if path.is_file()
            and not (_IGNORED_MARKDOWN_DIRS & set(path.relative_to(root_path).parts))
        )
    )


def _scan_local_links(
    root_path: Path,
    markdown_files: tuple[Path, ...],
) -> tuple[set[str], tuple[str, ...]]:
    local_links: set[str] = set()
    missing_links: list[str] = []
    for markdown_file in markdown_files:
        text = markdown_file.read_text(encoding="utf-8")
        for raw_target in _MARKDOWN_LINK_RE.findall(text):
            target = raw_target.strip()
            if _is_external_or_anchor(target):
                continue
            target_without_anchor = target.split("#", 1)[0].strip()
            if not target_without_anchor:
                continue
            target_without_anchor = unquote(target_without_anchor).strip("<>")
            target_path = (markdown_file.parent / target_without_anchor).resolve()
            local_links.add(str(target_path))
            if not target_path.exists():
                try:
                    relative_file = markdown_file.relative_to(root_path)
                except ValueError:
                    relative_file = markdown_file
                missing_links.append(f"{relative_file}: {target}")
    return local_links, tuple(sorted(dict.fromkeys(missing_links)))


def _is_external_or_anchor(target: str) -> bool:
    lowered = target.lower()
    return (
        lowered.startswith("http://")
        or lowered.startswith("https://")
        or lowered.startswith("mailto:")
        or lowered.startswith("#")
    )


def _write_docs_audit_report(output_dir: Path, result: DocsAuditResult) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "docs_audit_report.json").write_text(
        json.dumps(
            {"report_type": "docs_audit_report", **result.__dict__},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (output_dir / "docs_audit_report.md").write_text(
        render_docs_audit_markdown(result),
        encoding="utf-8",
    )


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- `{value}`" for value in values] if values else ["- none"]
