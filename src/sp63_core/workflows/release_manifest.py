"""Release artifact manifest and version metadata."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

RELEASE_MANIFEST_WARNING = (
    "Release artifact manifest is reproducibility metadata only. It does not "
    "publish a release, certify designs, or approve project use."
)

DEFAULT_RELEASE_ARTIFACTS: tuple[str, ...] = (
    "README.md",
    "pyproject.toml",
    "AGENTS.md",
    ".github/workflows/tests.yml",
    ".github/workflows/safety.yml",
    "docs/implementation_status.md",
    "docs/validation_report.md",
    "docs/engineering_audit.md",
    "docs/release_candidate_v0_9.md",
    "docs/docs_audit.md",
    "docs/project_template_package.md",
    "docs/engineering_workflow_runner.md",
    "docs/engineering_workflow_batch.md",
    "src/sp63_core/cli.py",
)


@dataclass(frozen=True)
class ReleaseArtifactManifestResult:
    """Release artifact manifest result."""

    status: str
    manifest_status: str
    version: str
    output_dir: str
    git_commit: str
    git_branch: str
    generated_at_utc: str
    artifact_count: int
    artifacts: tuple[dict[str, Any], ...]
    generated_files: tuple[str, ...]
    json_path: str
    markdown_path: str
    version_path: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_release_artifact_manifest(
    *,
    output_dir: Path,
    version: str = "0.9.0-rc1",
    artifact_paths: tuple[str, ...] = DEFAULT_RELEASE_ARTIFACTS,
) -> ReleaseArtifactManifestResult:
    """Build release artifact metadata without publishing a release."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / "release_artifact_manifest.json"
    markdown_path = output_path / "release_artifact_manifest.md"
    version_path = output_path / "VERSION.txt"

    warnings = (RELEASE_MANIFEST_WARNING,)
    errors: list[str] = []
    artifacts: list[dict[str, Any]] = []
    for relative_path in artifact_paths:
        path = Path(relative_path)
        if not path.exists():
            errors.append(f"release artifact missing: {relative_path}")
            continue
        artifacts.append(
            {
                "path": relative_path,
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            }
        )

    status = "fail" if errors else "pass"
    generated_at_utc = datetime.now(UTC).replace(microsecond=0).isoformat()
    result = ReleaseArtifactManifestResult(
        status=status,
        manifest_status=status,
        version=version,
        output_dir=str(output_path),
        git_commit=_git_value("rev-parse", "HEAD"),
        git_branch=_git_value("branch", "--show-current"),
        generated_at_utc=generated_at_utc,
        artifact_count=len(artifacts),
        artifacts=tuple(artifacts),
        generated_files=(str(json_path), str(markdown_path), str(version_path)),
        json_path=str(json_path),
        markdown_path=str(markdown_path),
        version_path=str(version_path),
        warnings=warnings,
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    json_path.write_text(
        json.dumps(_manifest_payload(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(_render_release_manifest_markdown(result), encoding="utf-8")
    version_path.write_text(version + "\n", encoding="utf-8")
    return result


def _manifest_payload(result: ReleaseArtifactManifestResult) -> dict[str, Any]:
    return {
        "report_type": "release_artifact_manifest",
        **result.__dict__,
    }


def _render_release_manifest_markdown(result: ReleaseArtifactManifestResult) -> str:
    lines = [
        "# Release Artifact Manifest",
        "",
        RELEASE_MANIFEST_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Version Metadata",
        "",
        f"- version: `{result.version}`",
        f"- manifest_status: `{result.manifest_status}`",
        f"- git_branch: `{result.git_branch}`",
        f"- git_commit: `{result.git_commit}`",
        f"- generated_at_utc: `{result.generated_at_utc}`",
        f"- artifact_count: `{result.artifact_count}`",
        "",
        "## Artifacts",
        "",
        "| path | size_bytes | sha256 |",
        "|---|---:|---|",
    ]
    for artifact in result.artifacts:
        lines.append(
            "| {path} | {size_bytes} | `{sha256}` |".format(
                path=artifact["path"],
                size_bytes=artifact["size_bytes"],
                sha256=artifact["sha256"],
            )
        )
    lines.extend(
        [
            "",
            "## Warnings",
            "",
            *_bullet_lines(result.warnings),
            "",
            "## Errors",
            "",
            *_bullet_lines(result.errors),
        ]
    )
    return "\n".join(lines) + "\n"


def _git_value(*args: str) -> str:
    try:
        completed = subprocess.run(
            ("git", *args),
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    value = completed.stdout.strip()
    return value or "unknown"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]
