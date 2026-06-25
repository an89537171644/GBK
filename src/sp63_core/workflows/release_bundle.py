"""Release bundle ZIP builder for v0.9 engineering review without certification."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

from sp63_core.workflows.launcher_scripts import build_launcher_scripts_package
from sp63_core.workflows.project_template import build_project_template_package

RELEASE_BUNDLE_WARNING = (
    "Release bundle is review packaging only. It does not publish a GitHub "
    "release, certify designs, approve project use, or make ML project-ready."
)

FORBIDDEN_SUFFIXES: tuple[str, ...] = (
    ".exe",
    ".dll",
    ".bin",
)


@dataclass(frozen=True)
class ReleaseBundleResult:
    """Release bundle ZIP result."""

    status: str
    bundle_status: str
    output_dir: str
    version: str
    bundle_dir: str
    zip_path: str
    manifest_path: str
    report_markdown_path: str
    file_count: int
    zip_sha256: str | None
    generated_files: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def build_release_bundle(
    *,
    output_dir: Path,
    version: str = "0.9.0-rc1",
) -> ReleaseBundleResult:
    """Build a review-only release bundle ZIP."""
    output_path = Path(output_dir)
    bundle_dir = output_path / "bundle"
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    warnings = [RELEASE_BUNDLE_WARNING]
    errors: list[str] = []
    generated_files: list[Path] = []

    _copy_required_file(Path("README.md"), bundle_dir / "README.md", generated_files, errors)
    _copy_required_file(Path("CHANGELOG.md"), bundle_dir / "CHANGELOG.md", generated_files, errors)
    _copy_required_file(
        Path("docs/release_notes_v0_9.md"),
        bundle_dir / "release_notes_v0_9.md",
        generated_files,
        errors,
    )
    _copy_required_file(
        Path("docs/known_limitations_v0_9.md"),
        bundle_dir / "known_limitations_v0_9.md",
        generated_files,
        errors,
    )
    _copy_required_file(
        Path("docs/reports/examples/clean_demo/rectangular_clean_demo_input.json"),
        bundle_dir / "examples" / "rectangular_clean_demo_input.json",
        generated_files,
        errors,
    )

    docs_user_manual = bundle_dir / "docs" / "user_manual"
    if Path("docs/user_manual").exists():
        shutil.copytree("docs/user_manual", docs_user_manual)
        generated_files.extend(path for path in docs_user_manual.rglob("*") if path.is_file())
    else:
        errors.append("release bundle source missing: docs/user_manual")

    project_template = build_project_template_package(
        output_dir=bundle_dir / "examples" / "project_template"
    )
    launcher_scripts = build_launcher_scripts_package(output_dir=bundle_dir / "launcher_scripts")
    if project_template.status != "pass":
        errors.extend(project_template.errors)
    if launcher_scripts.status != "pass":
        errors.extend(launcher_scripts.errors)
    generated_files.extend(Path(path) for path in project_template.generated_files)
    generated_files.extend(Path(path) for path in launcher_scripts.generated_files)

    run_commands_path = bundle_dir / "RUN_COMMANDS.md"
    run_commands_path.write_text(_render_run_commands(), encoding="utf-8")
    generated_files.append(run_commands_path)

    forbidden_files = tuple(
        str(path.relative_to(bundle_dir))
        for path in bundle_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES
    )
    errors.extend(f"forbidden binary file in release bundle: {path}" for path in forbidden_files)

    zip_path = output_path / f"release_bundle_{_safe_version(version)}.zip"
    if zip_path.exists():
        zip_path.unlink()
    _write_zip(bundle_dir=bundle_dir, zip_path=zip_path)
    generated_files.append(zip_path)

    manifest_path = output_path / "release_bundle_manifest.json"
    report_markdown_path = output_path / "release_bundle_report.md"
    status = "fail" if errors else "pass"
    zip_sha256 = _sha256(zip_path) if zip_path.exists() else None
    manifest = _build_manifest(
        output_dir=output_path,
        bundle_dir=bundle_dir,
        version=version,
        zip_path=zip_path,
        zip_sha256=zip_sha256,
        status=status,
        warnings=tuple(warnings),
        errors=tuple(errors),
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    report_markdown_path.write_text(
        _render_release_bundle_report(
            version=version,
            status=status,
            zip_path=zip_path,
            file_count=len(manifest["files"]),
            errors=tuple(errors),
        ),
        encoding="utf-8",
    )
    generated_files.extend([manifest_path, report_markdown_path])

    return ReleaseBundleResult(
        status=status,
        bundle_status=status,
        output_dir=str(output_path),
        version=version,
        bundle_dir=str(bundle_dir),
        zip_path=str(zip_path),
        manifest_path=str(manifest_path),
        report_markdown_path=str(report_markdown_path),
        file_count=len(manifest["files"]),
        zip_sha256=zip_sha256,
        generated_files=tuple(str(path) for path in generated_files),
        warnings=tuple(warnings),
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )


def _copy_required_file(
    source: Path,
    target: Path,
    generated_files: list[Path],
    errors: list[str],
) -> None:
    if not source.exists():
        errors.append(f"release bundle source missing: {source}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    generated_files.append(target)


def _write_zip(*, bundle_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(bundle_dir.rglob("*")):
            if path.is_file():
                archive.write(path, arcname=path.relative_to(bundle_dir.parent).as_posix())


def _build_manifest(
    *,
    output_dir: Path,
    bundle_dir: Path,
    version: str,
    zip_path: Path,
    zip_sha256: str | None,
    status: str,
    warnings: tuple[str, ...],
    errors: tuple[str, ...],
) -> dict[str, object]:
    files = [
        {
            "path": str(path),
            "relative_path": path.relative_to(output_dir).as_posix(),
            "sha256": _sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(bundle_dir.rglob("*"))
        if path.is_file()
    ]
    return {
        "report_type": "release_bundle_manifest",
        "status": status,
        "bundle_status": status,
        "version": version,
        "bundle_dir": str(bundle_dir),
        "zip_path": str(zip_path),
        "zip_sha256": zip_sha256,
        "file_count": len(files),
        "files": files,
        "warnings": list(warnings),
        "errors": list(errors),
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "ml_ready_for_project_use": False,
    }


def _render_run_commands() -> str:
    return "\n".join(
        [
            "# Release Bundle Run Commands",
            "",
            "```bash",
            "python -m sp63_core validate --golden",
            "python -m sp63_core manual-cases --json",
            "python -m sp63_core clean-demo-workflow --output-dir reports/clean_demo --json",
            "python -m sp63_core protected-files-check --json",
            "```",
            "",
            "These commands are review aids only. Engineer review remains mandatory.",
        ]
    ) + "\n"


def _render_release_bundle_report(
    *,
    version: str,
    status: str,
    zip_path: Path,
    file_count: int,
    errors: tuple[str, ...],
) -> str:
    lines = [
        "# Release Bundle Report",
        "",
        RELEASE_BUNDLE_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        f"- version: `{version}`",
        f"- bundle_status: `{status}`",
        f"- zip_path: `{zip_path}`",
        f"- file_count: `{file_count}`",
        "",
        "## Errors",
        "",
        *_bullet_lines(errors),
    ]
    return "\n".join(lines) + "\n"


def _safe_version(version: str) -> str:
    return version.replace(".", "_").replace("-", "_")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bullet_lines(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- none"]
