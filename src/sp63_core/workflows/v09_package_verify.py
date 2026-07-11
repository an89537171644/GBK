"""Verification for v0.9 release candidate review packages."""

from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sp63_core.workflows.v09_release_candidate_package import (
    build_v09_release_candidate_package,
)

V09_PACKAGE_VERIFICATION_WARNING = (
    "v0.9 package verification is engineering review evidence only. It does not "
    "publish a release, certify designs, approve project use, or make ML "
    "project-ready."
)

REQUIRED_PACKAGE_PATHS: tuple[str, ...] = (
    "README_START_HERE.md",
    "README_RELEASE_CANDIDATE.md",
    "v09_release_candidate_package.json",
    "v09_release_candidate_package.md",
    "v09_release_candidate_manifest.json",
    "v09_release_candidate_package.zip",
    "artifacts/clean_demo",
    "artifacts/engineer_review_packet",
    "artifacts/known_limitations",
    "artifacts/release_acceptance_checklist",
    "artifacts/signoff_templates",
)

REQUIRED_ZIP_FILES: tuple[str, ...] = (
    "README_START_HERE.md",
    "README_RELEASE_CANDIDATE.md",
    "v09_release_candidate_package.json",
    "v09_release_candidate_package.md",
    "v09_release_candidate_manifest.json",
    "artifacts/known_limitations/known_limitations_v0_9.md",
)

REQUIRED_ZIP_PREFIXES: tuple[str, ...] = (
    "artifacts/clean_demo/",
    "artifacts/engineer_review_packet/",
    "artifacts/release_acceptance_checklist/",
    "artifacts/signoff_templates/",
)

VERIFICATION_OUTPUT_FILES: tuple[str, ...] = (
    "README_V09_PACKAGE_VERIFICATION.md",
    "manual_acceptance_log_template.md",
    "v09_package_verification.json",
    "v09_package_verification.md",
)

FORBIDDEN_PATH_PARTS: tuple[str, ...] = (
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".ipynb_checkpoints",
)

FORBIDDEN_NAME_TOKENS: tuple[str, ...] = (
    "api_key",
    "confidential",
    "credentials",
    "full_sp63",
    "full-text-sp63",
    "grant",
    "id_rsa",
    "lira",
    "passport",
    "personal",
    "phone",
    "private",
    "scad",
    "secret",
    "signature",
    "snils",
    "sp63_full",
    "token",
)

FORBIDDEN_SUFFIXES: tuple[str, ...] = (
    ".doc",
    ".docx",
    ".dwg",
    ".dxf",
    ".env",
    ".ifc",
    ".pdf",
    ".rvt",
    ".spf",
    ".spr",
)


@dataclass(frozen=True)
class V09PackageVerificationResult:
    """v0.9 release candidate package verification result."""

    status: str
    verification_status: str
    package_dir: str
    output_dir: str
    version: str
    build_ran: bool
    checked_package_paths: tuple[str, ...]
    missing_required_paths: tuple[str, ...]
    zip_path: str
    zip_entry_count: int
    missing_zip_entries: tuple[str, ...]
    forbidden_package_paths: tuple[str, ...]
    forbidden_zip_entries: tuple[str, ...]
    manifest_path: str
    manifest_file_count: int
    manifest_missing_files: tuple[str, ...]
    manifest_referenced_missing_files: tuple[str, ...]
    manifest_checksum_mismatches: tuple[str, ...]
    manual_review_gates: tuple[dict[str, Any], ...]
    ready_for_manual_review: bool
    ready_for_project_use: bool
    generated_files: tuple[str, ...]
    readme_path: str
    summary_json_path: str
    summary_markdown_path: str
    manual_acceptance_log_template_path: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def verify_v09_release_candidate_package(
    *,
    output_dir: Path,
    package_dir: Path | None = None,
    build: bool = False,
    version: str = "0.9.0-rc1",
) -> V09PackageVerificationResult:
    """Verify an existing or freshly built v0.9 release candidate package."""
    output_path = Path(output_dir)
    package_path = Path(package_dir) if package_dir is not None else output_path / "package"
    if not build and package_dir is None:
        raise ValueError("--package-dir is required unless --build is used")

    if build:
        build_v09_release_candidate_package(output_dir=package_path, version=version)

    output_path.mkdir(parents=True, exist_ok=True)

    missing_required = _missing_required_paths(package_path)
    zip_path = package_path / "v09_release_candidate_package.zip"
    zip_entries, zip_errors = _read_zip_entries(zip_path)
    missing_zip_entries = _missing_zip_entries(zip_entries)
    forbidden_package_paths = _scan_for_forbidden_package_paths(package_path)
    forbidden_zip_entries = _scan_for_forbidden_names(zip_entries)
    manifest_path = package_path / "v09_release_candidate_manifest.json"
    manifest_result = _verify_manifest(package_path=package_path, manifest_path=manifest_path)
    manual_review_gates = _manual_review_gates(package_path / "v09_release_candidate_package.json")

    errors = tuple(
        [
            *(f"required package path missing: {path}" for path in missing_required),
            *(f"required ZIP entry missing: {path}" for path in missing_zip_entries),
            *(f"forbidden package path included: {path}" for path in forbidden_package_paths),
            *(f"forbidden ZIP entry included: {path}" for path in forbidden_zip_entries),
            *(f"manifest does not cover package file: {path}" for path in manifest_result.missing),
            *(
                f"manifest references missing package file: {path}"
                for path in manifest_result.referenced_missing
            ),
            *(
                f"manifest checksum mismatch for package file: {path}"
                for path in manifest_result.checksum_mismatches
            ),
            *zip_errors,
            *manifest_result.errors,
        ]
    )
    ready_for_manual_review = not errors
    status = "fail" if errors else "review_required" if manual_review_gates else "pass"

    readme_path = output_path / "README_V09_PACKAGE_VERIFICATION.md"
    summary_json_path = output_path / "v09_package_verification.json"
    summary_markdown_path = output_path / "v09_package_verification.md"
    manual_log_path = output_path / "manual_acceptance_log_template.md"
    generated_files = (
        str(readme_path),
        str(summary_json_path),
        str(summary_markdown_path),
        str(manual_log_path),
    )
    result = V09PackageVerificationResult(
        status=status,
        verification_status=status,
        package_dir=str(package_path),
        output_dir=str(output_path),
        version=version,
        build_ran=build,
        checked_package_paths=REQUIRED_PACKAGE_PATHS,
        missing_required_paths=missing_required,
        zip_path=str(zip_path),
        zip_entry_count=len(zip_entries),
        missing_zip_entries=missing_zip_entries,
        forbidden_package_paths=forbidden_package_paths,
        forbidden_zip_entries=forbidden_zip_entries,
        manifest_path=str(manifest_path),
        manifest_file_count=manifest_result.file_count,
        manifest_missing_files=manifest_result.missing,
        manifest_referenced_missing_files=manifest_result.referenced_missing,
        manifest_checksum_mismatches=manifest_result.checksum_mismatches,
        manual_review_gates=manual_review_gates,
        ready_for_manual_review=ready_for_manual_review,
        ready_for_project_use=False,
        generated_files=generated_files,
        readme_path=str(readme_path),
        summary_json_path=str(summary_json_path),
        summary_markdown_path=str(summary_markdown_path),
        manual_acceptance_log_template_path=str(manual_log_path),
        warnings=(V09_PACKAGE_VERIFICATION_WARNING,),
        errors=errors,
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    readme_path.write_text(_render_readme(result), encoding="utf-8")
    summary_markdown_path.write_text(
        render_v09_package_verification_markdown(result),
        encoding="utf-8",
    )
    manual_log_path.write_text(_render_manual_acceptance_log_template(result), encoding="utf-8")
    summary_json_path.write_text(
        json.dumps(
            {"report_type": "v09_package_verification", **asdict(result)},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return result


def render_v09_package_verification_markdown(result: V09PackageVerificationResult) -> str:
    """Render v0.9 package verification as Markdown."""
    lines = [
        "# v0.9 Package Verification",
        "",
        V09_PACKAGE_VERIFICATION_WARNING,
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
        f"- verification_status: `{result.verification_status}`",
        f"- ready_for_manual_review: `{result.ready_for_manual_review}`",
        f"- ready_for_project_use: `{result.ready_for_project_use}`",
        f"- ml_ready_for_project_use: `{result.ml_ready_for_project_use}`",
        f"- build_ran: `{result.build_ran}`",
        f"- missing_required_paths: `{len(result.missing_required_paths)}`",
        f"- missing_zip_entries: `{len(result.missing_zip_entries)}`",
        f"- forbidden_package_paths: `{len(result.forbidden_package_paths)}`",
        f"- forbidden_zip_entries: `{len(result.forbidden_zip_entries)}`",
        f"- manifest_missing_files: `{len(result.manifest_missing_files)}`",
        f"- manifest_checksum_mismatches: `{len(result.manifest_checksum_mismatches)}`",
        f"- manual_review_gates: `{len(result.manual_review_gates)}`",
        "",
        "## Required Package Paths",
        "",
        *_bullet_lines(result.checked_package_paths),
        "",
        "## Missing Required Paths",
        "",
        *_bullet_lines(result.missing_required_paths),
        "",
        "## Missing ZIP Entries",
        "",
        *_bullet_lines(result.missing_zip_entries),
        "",
        "## Forbidden Package Paths",
        "",
        *_bullet_lines(result.forbidden_package_paths),
        "",
        "## Forbidden ZIP Entries",
        "",
        *_bullet_lines(result.forbidden_zip_entries),
        "",
        "## Manifest Issues",
        "",
        *_bullet_lines(
            (
                *result.manifest_missing_files,
                *result.manifest_referenced_missing_files,
                *result.manifest_checksum_mismatches,
            )
        ),
        "",
        "## Manual Review Gates",
        "",
        *_gate_lines(result.manual_review_gates),
        "",
        "## Errors",
        "",
        *_bullet_lines(result.errors),
    ]
    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class _ManifestVerification:
    file_count: int
    missing: tuple[str, ...]
    referenced_missing: tuple[str, ...]
    checksum_mismatches: tuple[str, ...]
    errors: tuple[str, ...]


def _missing_required_paths(package_path: Path) -> tuple[str, ...]:
    if not package_path.exists():
        return REQUIRED_PACKAGE_PATHS
    return tuple(path for path in REQUIRED_PACKAGE_PATHS if not (package_path / path).exists())


def _read_zip_entries(zip_path: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not zip_path.exists():
        return (), ()
    try:
        with zipfile.ZipFile(zip_path) as archive:
            return tuple(sorted(archive.namelist())), ()
    except zipfile.BadZipFile:
        return (), (f"ZIP is not readable: {zip_path}",)


def _missing_zip_entries(zip_entries: tuple[str, ...]) -> tuple[str, ...]:
    if not zip_entries:
        return ()
    entries = set(zip_entries)
    missing = [path for path in REQUIRED_ZIP_FILES if path not in entries]
    for prefix in REQUIRED_ZIP_PREFIXES:
        if not any(path.startswith(prefix) for path in zip_entries):
            missing.append(prefix)
    return tuple(missing)


def _scan_for_forbidden_package_paths(package_path: Path) -> tuple[str, ...]:
    if not package_path.exists():
        return ()
    relative_paths = tuple(
        path.relative_to(package_path).as_posix()
        for path in package_path.rglob("*")
        if path.is_file()
    )
    return _scan_for_forbidden_names(relative_paths)


def _scan_for_forbidden_names(paths: tuple[str, ...]) -> tuple[str, ...]:
    forbidden: list[str] = []
    for path in paths:
        lowered = path.lower().replace("\\", "/")
        parts = tuple(part for part in lowered.split("/") if part)
        if any(part.endswith("_smoke") for part in parts):
            forbidden.append(path)
            continue
        if any(part in FORBIDDEN_PATH_PARTS for part in parts):
            forbidden.append(path)
            continue
        if any(token in lowered for token in FORBIDDEN_NAME_TOKENS):
            forbidden.append(path)
            continue
        if any(lowered.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
            forbidden.append(path)
    return tuple(dict.fromkeys(forbidden))


def _verify_manifest(*, package_path: Path, manifest_path: Path) -> _ManifestVerification:
    if not manifest_path.exists():
        return _ManifestVerification(
            file_count=0,
            missing=(),
            referenced_missing=(),
            checksum_mismatches=(),
            errors=(f"manifest is missing: {manifest_path}",),
        )
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _ManifestVerification(
            file_count=0,
            missing=(),
            referenced_missing=(),
            checksum_mismatches=(),
            errors=(f"manifest is not valid JSON: {exc}",),
        )

    files = payload.get("files", ())
    if not isinstance(files, list):
        return _ManifestVerification(
            file_count=0,
            missing=(),
            referenced_missing=(),
            checksum_mismatches=(),
            errors=("manifest files field is not a list",),
        )

    manifest_items = {
        item.get("relative_path"): item
        for item in files
        if isinstance(item, dict) and isinstance(item.get("relative_path"), str)
    }
    expected_files = _manifest_expected_files(package_path, manifest_path)
    missing = tuple(path for path in expected_files if path not in manifest_items)
    referenced_missing: list[str] = []
    checksum_mismatches: list[str] = []
    for relative_path, item in manifest_items.items():
        path = package_path / relative_path
        if not path.exists():
            referenced_missing.append(relative_path)
            continue
        expected_sha = item.get("sha256")
        if isinstance(expected_sha, str) and expected_sha != _sha256(path):
            checksum_mismatches.append(relative_path)
    return _ManifestVerification(
        file_count=len(manifest_items),
        missing=missing,
        referenced_missing=tuple(referenced_missing),
        checksum_mismatches=tuple(checksum_mismatches),
        errors=(),
    )


def _manifest_expected_files(package_path: Path, manifest_path: Path) -> tuple[str, ...]:
    if not package_path.exists():
        return ()
    expected: list[str] = []
    for path in sorted(item for item in package_path.rglob("*") if item.is_file()):
        relative_path = path.relative_to(package_path).as_posix()
        if path == manifest_path:
            continue
        if path.suffix.lower() == ".zip":
            continue
        if path.name in VERIFICATION_OUTPUT_FILES:
            continue
        expected.append(relative_path)
    return tuple(expected)


def _manual_review_gates(summary_path: Path) -> tuple[dict[str, Any], ...]:
    if not summary_path.exists():
        return ()
    try:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ()
    gates = payload.get("review_required_gates", ())
    if isinstance(gates, list) and gates:
        return tuple(gate for gate in gates if isinstance(gate, dict))
    status = payload.get("package_status") or payload.get("status")
    if status == "review_required":
        return (
            {
                "gate_id": "manual_engineering_review",
                "status": "review_required",
                "reason": "release candidate package status requires manual review",
            },
        )
    return ()


def _render_readme(result: V09PackageVerificationResult) -> str:
    return "\n".join(
        [
            "# README v0.9 Package Verification",
            "",
            V09_PACKAGE_VERIFICATION_WARNING,
            "",
            f"verification_status: `{result.verification_status}`",
            f"ready_for_manual_review: `{result.ready_for_manual_review}`",
            "ready_for_project_use: `false`",
            "ml_ready_for_project_use: `false`",
            "",
            "Review `v09_package_verification.md` and "
            "`manual_acceptance_log_template.md` before release acceptance.",
        ]
    ) + "\n"


def _render_manual_acceptance_log_template(result: V09PackageVerificationResult) -> str:
    return "\n".join(
        [
            "# Manual Acceptance Log Template",
            "",
            "This template must be completed by a responsible engineer outside Codex.",
            "",
            f"- package_dir: `{result.package_dir}`",
            f"- verification_status: `{result.verification_status}`",
            f"- ready_for_manual_review: `{result.ready_for_manual_review}`",
            "- ready_for_project_use: `false`",
            "- ml_ready_for_project_use: `false`",
            "",
            "## Review Checklist",
            "",
            "- [ ] Review `README_START_HERE.md`.",
            "- [ ] Review `README_RELEASE_CANDIDATE.md`.",
            "- [ ] Review `v09_release_candidate_manifest.json` checksums.",
            "- [ ] Review clean demo deterministic report evidence.",
            "- [ ] Review engineer review packet.",
            "- [ ] Review known limitations.",
            "- [ ] Complete release acceptance checklist.",
            "- [ ] Complete signoff templates.",
            "- [ ] Confirm no project-use approval is granted by this package.",
            "- [ ] Confirm ML remains advisory-only.",
            "",
            "## Engineer Decision",
            "",
            "- reviewer:",
            "- review_date:",
            "- decision:",
            "- notes:",
        ]
    ) + "\n"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]


def _gate_lines(values: tuple[dict[str, Any], ...]) -> list[str]:
    if not values:
        return ["- none"]
    return [
        f"- `{gate.get('gate_id', 'manual_review')}`: "
        f"`{gate.get('status', 'review_required')}` - {gate.get('reason', '')}"
        for gate in values
    ]
