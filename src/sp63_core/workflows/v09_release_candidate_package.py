"""Final v0.9 release candidate package for engineering review."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sp63_core.workflows.clean_demo_verify import verify_clean_demo_artifacts
from sp63_core.workflows.clean_demo_workflow import run_clean_demo_workflow
from sp63_core.workflows.engineer_review_packet import build_engineer_review_packet
from sp63_core.workflows.release_acceptance_checklist import (
    build_release_acceptance_checklist,
)
from sp63_core.workflows.release_bundle import build_release_bundle
from sp63_core.workflows.release_notes import build_release_notes_package
from sp63_core.workflows.review_signoff_templates import build_review_signoff_templates
from sp63_core.workflows.v09_final_audit import build_v09_final_audit
from sp63_core.workflows.v09_freeze_report import build_v09_freeze_report
from sp63_core.workflows.v09_review_build import build_v09_review_build
from sp63_core.workflows.v09_review_closure import build_v09_review_closure
from sp63_core.workflows.windows_smoke_plan import build_windows_smoke_plan

V09_RELEASE_CANDIDATE_PACKAGE_WARNING = (
    "v0.9 release candidate package is engineering review evidence only. It does "
    "not publish a release, certify designs, approve project use, or make ML "
    "project-ready."
)

FORBIDDEN_PACKAGE_NAME_TOKENS: tuple[str, ...] = (
    "passport",
    "snils",
    "grant",
    "private",
    "personal",
    "confidential",
)
FORBIDDEN_PACKAGE_SUFFIXES: tuple[str, ...] = (
    ".pdf",
    ".doc",
    ".docx",
    ".dwg",
    ".ifc",
    ".spf",
    ".spr",
)


@dataclass(frozen=True)
class V09ReleaseCandidatePackageResult:
    """v0.9 release candidate package result."""

    status: str
    package_status: str
    output_dir: str
    version: str
    package_root: str
    generated_files: tuple[str, ...]
    included_artifacts: tuple[dict[str, Any], ...]
    manifest_path: str
    readme_path: str
    start_here_path: str
    zip_path: str
    critical_failures: tuple[str, ...]
    review_required_gates: tuple[dict[str, Any], ...]
    ready_for_engineering_review: bool
    ready_for_project_use: bool
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_v09_release_candidate_package(
    *,
    output_dir: Path,
    version: str = "0.9.0-rc1",
) -> V09ReleaseCandidatePackageResult:
    """Build the final v0.9 release candidate package."""
    output_path = Path(output_dir)
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    artifacts_path = output_path / "artifacts"
    artifacts_path.mkdir(parents=True, exist_ok=True)

    warnings = [V09_RELEASE_CANDIDATE_PACKAGE_WARNING]
    errors: list[str] = []
    included_artifacts: list[dict[str, Any]] = []
    review_required_gates: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="sp63_k108_") as temp_name:
        temp_path = Path(temp_name)

        review_closure = build_v09_review_closure(
            output_dir=temp_path / "review_closure",
            version=version,
        )
        _collect_summary_artifact(
            name="review_closure",
            result=review_closure,
            target_dir=artifacts_path / "review_closure",
            critical=True,
            included_artifacts=included_artifacts,
            review_required_gates=review_required_gates,
        )
        _extend_review_gates_from_closure(review_closure, review_required_gates)

        review_build = build_v09_review_build(
            output_dir=temp_path / "review_build",
            version=version,
        )
        _collect_summary_artifact(
            name="review_build",
            result=review_build,
            target_dir=artifacts_path / "review_build",
            critical=True,
            included_artifacts=included_artifacts,
            review_required_gates=review_required_gates,
        )

        freeze = build_v09_freeze_report(output_dir=temp_path / "freeze_report", version=version)
        _collect_summary_artifact(
            name="freeze_report",
            result=freeze,
            target_dir=artifacts_path / "freeze_report",
            critical=False,
            included_artifacts=included_artifacts,
            review_required_gates=review_required_gates,
        )

        final_audit = build_v09_final_audit(output_dir=temp_path / "final_audit", version=version)
        _collect_summary_artifact(
            name="final_audit",
            result=final_audit,
            target_dir=artifacts_path / "final_audit",
            critical=False,
            included_artifacts=included_artifacts,
            review_required_gates=review_required_gates,
        )

        engineer_packet = build_engineer_review_packet(
            output_dir=temp_path / "engineer_review_packet"
        )
        _collect_summary_artifact(
            name="engineer_review_packet",
            result=engineer_packet,
            target_dir=artifacts_path / "engineer_review_packet",
            critical=False,
            included_artifacts=included_artifacts,
            review_required_gates=review_required_gates,
        )

    clean_demo = run_clean_demo_workflow(output_dir=artifacts_path / "clean_demo")
    clean_verify = verify_clean_demo_artifacts(workflow_dir=Path(clean_demo.output_dir))
    _record_artifact(
        name="clean_demo",
        status=clean_demo.status,
        critical=True,
        path=str(artifacts_path / "clean_demo"),
        included_artifacts=included_artifacts,
        review_required_gates=review_required_gates,
    )
    _record_artifact(
        name="clean_demo_verify",
        status=clean_verify.status,
        critical=True,
        path=clean_verify.summary_markdown_path,
        included_artifacts=included_artifacts,
        review_required_gates=review_required_gates,
    )

    acceptance = build_release_acceptance_checklist(
        output_dir=artifacts_path / "release_acceptance_checklist"
    )
    _record_artifact_result(
        name="release_acceptance_checklist",
        result=acceptance,
        critical=False,
        included_artifacts=included_artifacts,
        review_required_gates=review_required_gates,
    )

    signoff = build_review_signoff_templates(output_dir=artifacts_path / "signoff_templates")
    _record_artifact_result(
        name="signoff_templates",
        result=signoff,
        critical=False,
        included_artifacts=included_artifacts,
        review_required_gates=review_required_gates,
    )

    windows_smoke = build_windows_smoke_plan(output_dir=artifacts_path / "windows_smoke_plan")
    _record_artifact_result(
        name="windows_smoke_plan",
        result=windows_smoke,
        critical=False,
        included_artifacts=included_artifacts,
        review_required_gates=review_required_gates,
    )

    release_notes = build_release_notes_package(
        output_dir=artifacts_path / "release_notes",
        version=version,
    )
    _record_artifact_result(
        name="release_notes",
        result=release_notes,
        critical=False,
        included_artifacts=included_artifacts,
        review_required_gates=review_required_gates,
    )

    _copy_known_limitations(artifacts_path / "known_limitations", errors)
    _record_artifact(
        name="known_limitations",
        status="review_required",
        critical=False,
        path=str(artifacts_path / "known_limitations" / "known_limitations_v0_9.md"),
        included_artifacts=included_artifacts,
        review_required_gates=review_required_gates,
    )

    release_bundle = build_release_bundle(
        output_dir=artifacts_path / "release_bundle",
        version=version,
    )
    _record_artifact_result(
        name="release_bundle",
        result=release_bundle,
        critical=True,
        included_artifacts=included_artifacts,
        review_required_gates=review_required_gates,
    )

    critical_failures = tuple(
        f"critical release candidate artifact failed: {item['name']}"
        for item in included_artifacts
        if item["critical"] and item["status"] == "fail"
    )
    forbidden_errors = _scan_for_forbidden_package_paths(output_path)
    errors.extend(forbidden_errors)
    critical_failures = tuple([*critical_failures, *forbidden_errors])
    review_required_gates_tuple = _dedupe_review_gates(tuple(review_required_gates))

    package_status = _package_status(
        critical_failures=critical_failures,
        review_required_gates=review_required_gates_tuple,
    )
    start_here_path = output_path / "README_START_HERE.md"
    readme_path = output_path / "README_RELEASE_CANDIDATE.md"
    summary_json_path = output_path / "v09_release_candidate_package.json"
    summary_markdown_path = output_path / "v09_release_candidate_package.md"
    manifest_path = output_path / "v09_release_candidate_manifest.json"
    zip_path = output_path / "v09_release_candidate_package.zip"

    start_here_path.write_text(_render_start_here(package_status, version), encoding="utf-8")
    result = V09ReleaseCandidatePackageResult(
        status=package_status,
        package_status=package_status,
        output_dir=str(output_path),
        version=version,
        package_root=str(output_path),
        generated_files=(),
        included_artifacts=tuple(included_artifacts),
        manifest_path=str(manifest_path),
        readme_path=str(readme_path),
        start_here_path=str(start_here_path),
        zip_path=str(zip_path),
        critical_failures=critical_failures,
        review_required_gates=review_required_gates_tuple,
        ready_for_engineering_review=not critical_failures,
        ready_for_project_use=False,
        warnings=tuple(warnings),
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    readme_path.write_text(_render_readme(result), encoding="utf-8")
    summary_markdown_path.write_text(
        render_v09_release_candidate_package_markdown(result),
        encoding="utf-8",
    )
    summary_json_path.write_text(
        json.dumps(
            {"report_type": "v09_release_candidate_package", **asdict(result)},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_manifest(output_path=output_path, manifest_path=manifest_path, result=result)
    _write_zip(package_root=output_path, zip_path=zip_path)

    final_files = tuple(str(path) for path in _iter_package_files(output_path))
    final_result = V09ReleaseCandidatePackageResult(
        **{**asdict(result), "generated_files": final_files}
    )
    summary_json_path.write_text(
        json.dumps(
            {"report_type": "v09_release_candidate_package", **asdict(final_result)},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    summary_markdown_path.write_text(
        render_v09_release_candidate_package_markdown(final_result),
        encoding="utf-8",
    )
    _write_manifest(output_path=output_path, manifest_path=manifest_path, result=final_result)
    _write_zip(package_root=output_path, zip_path=zip_path)
    return final_result


def render_v09_release_candidate_package_markdown(
    result: V09ReleaseCandidatePackageResult,
) -> str:
    """Render v0.9 release candidate package as Markdown."""
    lines = [
        "# v0.9 Release Candidate Package",
        "",
        V09_RELEASE_CANDIDATE_PACKAGE_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "ready_for_project_use = false",
        "",
        "## Summary",
        "",
        f"- version: `{result.version}`",
        f"- package_status: `{result.package_status}`",
        f"- ready_for_engineering_review: `{result.ready_for_engineering_review}`",
        f"- ready_for_project_use: `{result.ready_for_project_use}`",
        f"- critical_failures: `{len(result.critical_failures)}`",
        f"- review_required_gates: `{len(result.review_required_gates)}`",
        f"- zip_path: `{result.zip_path}`",
        "",
        "## Included Artifacts",
        "",
        "| name | status | critical | path |",
        "|---|---|---:|---|",
    ]
    for item in result.included_artifacts:
        lines.append(
            f"| {item['name']} | `{item['status']}` | "
            f"`{item['critical']}` | `{item['path']}` |"
        )
    lines.extend(
        [
            "",
            "## Review Required Gates",
            "",
            *_gate_lines(result.review_required_gates),
            "",
            "## Critical Failures",
            "",
            *_bullet_lines(result.critical_failures),
        ]
    )
    return "\n".join(lines) + "\n"


def _collect_summary_artifact(
    *,
    name: str,
    result: Any,
    target_dir: Path,
    critical: bool,
    included_artifacts: list[dict[str, Any]],
    review_required_gates: list[dict[str, Any]],
) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    copied_files: list[str] = []
    for source_name in getattr(result, "generated_files", ()):
        source = Path(source_name)
        if source.is_file():
            target = target_dir / source.name
            shutil.copyfile(source, target)
            copied_files.append(str(target))
    collected_path = target_dir / "collected_artifact.json"
    collected_path.write_text(
        json.dumps(
            {
                "artifact_name": name,
                "status": result.status,
                "copied_files": copied_files,
                "requires_engineer_review": True,
                "ml_is_advisory_only": True,
                "deterministic_checks_required": True,
                "ml_ready_for_project_use": False,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    _record_artifact(
        name=name,
        status=result.status,
        critical=critical,
        path=str(target_dir),
        included_artifacts=included_artifacts,
        review_required_gates=review_required_gates,
    )


def _record_artifact_result(
    *,
    name: str,
    result: Any,
    critical: bool,
    included_artifacts: list[dict[str, Any]],
    review_required_gates: list[dict[str, Any]],
) -> None:
    generated_files = getattr(result, "generated_files", ())
    path = generated_files[0] if generated_files else getattr(result, "output_dir", "")
    _record_artifact(
        name=name,
        status=result.status,
        critical=critical,
        path=path,
        included_artifacts=included_artifacts,
        review_required_gates=review_required_gates,
    )


def _record_artifact(
    *,
    name: str,
    status: str,
    critical: bool,
    path: str,
    included_artifacts: list[dict[str, Any]],
    review_required_gates: list[dict[str, Any]],
) -> None:
    included_artifacts.append(
        {
            "name": name,
            "status": status,
            "critical": critical,
            "path": path,
        }
    )
    if status == "review_required":
        review_required_gates.append(
            {
                "gate_id": name,
                "status": "review_required",
                "reason": f"{name} requires manual engineering review",
            }
        )


def _extend_review_gates_from_closure(
    closure: Any,
    review_required_gates: list[dict[str, Any]],
) -> None:
    for gate in closure.acceptable_review_gates:
        review_required_gates.append(
            {
                "gate_id": gate["gate_id"],
                "status": gate["status"],
                "reason": gate["reason"],
            }
        )


def _copy_known_limitations(target_dir: Path, errors: list[str]) -> None:
    source = Path("docs/known_limitations_v0_9.md")
    target_dir.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        errors.append("known limitations document missing: docs/known_limitations_v0_9.md")
        return
    shutil.copyfile(source, target_dir / "known_limitations_v0_9.md")


def _package_status(
    *,
    critical_failures: tuple[str, ...],
    review_required_gates: tuple[dict[str, Any], ...],
) -> str:
    if critical_failures:
        return "fail"
    if review_required_gates:
        return "review_required"
    return "pass"


def _render_start_here(package_status: str, version: str) -> str:
    return "\n".join(
        [
            "# Start Here: v0.9 Release Candidate Package",
            "",
            "This folder is a v0.9 release candidate package for engineering review.",
            "",
            "Start with:",
            "",
            "1. `README_RELEASE_CANDIDATE.md`",
            "2. `v09_release_candidate_package.md`",
            "3. `v09_release_candidate_manifest.json`",
            "4. `artifacts/clean_demo/index.html`",
            "",
            "How to check the package:",
            "",
            "- open `artifacts/clean_demo/index.html` in a browser;",
            "- review `artifacts/clean_demo/deterministic_report/report.html`;",
            "- review `v09_release_candidate_package.json` for machine-readable status;",
            "- review `v09_release_candidate_manifest.json` for SHA256 checksums;",
            "- keep the ZIP archive with the package evidence.",
            "",
            "`review_required` means manual engineer review is still required. It is not a "
            "failure by itself.",
            "",
            f"- version: `{version}`",
            f"- package_status: `{package_status}`",
            "- project use is not approved;",
            "- engineer review is mandatory;",
            "- ML is advisory-only;",
            "- deterministic SP63 checks are mandatory.",
        ]
    ) + "\n"


def _render_readme(result: V09ReleaseCandidatePackageResult) -> str:
    return "\n".join(
        [
            "# README Release Candidate",
            "",
            V09_RELEASE_CANDIDATE_PACKAGE_WARNING,
            "",
            f"version: `{result.version}`",
            f"package_status: `{result.package_status}`",
            f"ready_for_engineering_review: `{result.ready_for_engineering_review}`",
            "ready_for_project_use: `false`",
            "ml_ready_for_project_use: `false`",
            "",
            "Review `README_START_HERE.md` first. This package is not project approval.",
        ]
    ) + "\n"


def _write_manifest(
    *,
    output_path: Path,
    manifest_path: Path,
    result: V09ReleaseCandidatePackageResult,
) -> None:
    files = [
        {
            "relative_path": path.relative_to(output_path).as_posix(),
            "sha256": _sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for path in _iter_package_files(output_path)
        if path != manifest_path and path.suffix.lower() != ".zip"
    ]
    manifest = {
        "report_type": "v09_release_candidate_manifest",
        "status": result.status,
        "package_status": result.package_status,
        "version": result.version,
        "file_count": len(files),
        "files": files,
        "included_artifacts": list(result.included_artifacts),
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "ml_ready_for_project_use": False,
        "ready_for_project_use": False,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_zip(*, package_root: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in _iter_package_files(package_root):
            if path == zip_path:
                continue
            archive.write(path, arcname=path.relative_to(package_root).as_posix())


def _scan_for_forbidden_package_paths(package_root: Path) -> tuple[str, ...]:
    errors: list[str] = []
    for path in _iter_package_files(package_root):
        relative = path.relative_to(package_root).as_posix().lower()
        if any(part.endswith("_smoke") for part in Path(relative).parts):
            errors.append(f"generated smoke artifact path included: {relative}")
        if any(token in relative for token in FORBIDDEN_PACKAGE_NAME_TOKENS):
            errors.append(f"forbidden private/personal path token included: {relative}")
        if any(relative.endswith(suffix) for suffix in FORBIDDEN_PACKAGE_SUFFIXES):
            errors.append(f"forbidden binary/document path included: {relative}")
        if "sp63_full" in relative or "full_sp63" in relative:
            errors.append(f"forbidden full SP63 path included: {relative}")
    return tuple(errors)


def _iter_package_files(package_root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in package_root.rglob("*") if path.is_file()))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dedupe_review_gates(gates: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    unique: dict[str, dict[str, Any]] = {}
    for gate in gates:
        unique.setdefault(gate["gate_id"], gate)
    return tuple(unique.values())


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]


def _gate_lines(values: tuple[dict[str, Any], ...]) -> list[str]:
    if not values:
        return ["- none"]
    return [
        f"- `{gate['gate_id']}`: `{gate['status']}` - {gate['reason']}" for gate in values
    ]
