"""Guard against accidental protected-file changes in release/workflow branches."""

from __future__ import annotations

import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

PROTECTED_FILES: tuple[str, ...] = (
    "src/sp63_core/checks/bending.py",
    "src/sp63_core/checks/shear.py",
    "src/sp63_core/checks/cracking.py",
    "src/sp63_core/checks/crack_width.py",
    "src/sp63_core/checks/deflection.py",
    "src/sp63_core/validation/external.py",
    "src/sp63_core/materials/concrete.py",
    "src/sp63_core/materials/rebar.py",
)

PROTECTED_FILES_GUARD_WARNING = (
    "Protected-files guard is a review aid only. It must not be used as an "
    "automatic merge approval."
)


@dataclass(frozen=True)
class ProtectedFilesGuardResult:
    """Result of checking whether protected files changed."""

    status: str
    guard_status: str
    protected_files: tuple[str, ...]
    changed_protected_files: tuple[str, ...]
    checked_git_ref: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True


def run_protected_files_guard(
    *,
    base_ref: str = "main",
    head_ref: str = "HEAD",
    changed_files: Iterable[str] | None = None,
    repo_dir: Path | None = None,
    allow_review_required: bool = False,
) -> ProtectedFilesGuardResult:
    """Check git diff for protected calculation/material/external files."""
    warnings: list[str] = [PROTECTED_FILES_GUARD_WARNING]
    errors: list[str] = []
    checked_git_ref = f"{base_ref}...{head_ref}"

    if changed_files is None:
        diff_result = _git_changed_files(
            base_ref=base_ref,
            head_ref=head_ref,
            repo_dir=repo_dir,
        )
        if diff_result[1]:
            warnings.extend(diff_result[1])
            if allow_review_required:
                warnings.append("review_required status allowed by caller")
            return ProtectedFilesGuardResult(
                status="review_required",
                guard_status="review_required",
                protected_files=PROTECTED_FILES,
                changed_protected_files=(),
                checked_git_ref=checked_git_ref,
                warnings=tuple(dict.fromkeys(warnings)),
                errors=(),
                requires_engineer_review=True,
            )
        changed_files_tuple = diff_result[0]
    else:
        changed_files_tuple = tuple(_normalize_path(path) for path in changed_files)
        checked_git_ref = "provided_changed_files"

    protected_set = set(PROTECTED_FILES)
    changed_protected = tuple(
        path for path in changed_files_tuple if _normalize_path(path) in protected_set
    )
    if changed_protected:
        errors.append("protected files changed: " + ", ".join(changed_protected))

    status = "fail" if changed_protected else "pass"
    return ProtectedFilesGuardResult(
        status=status,
        guard_status=status,
        protected_files=PROTECTED_FILES,
        changed_protected_files=changed_protected,
        checked_git_ref=checked_git_ref,
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(errors),
        requires_engineer_review=True,
    )


def _git_changed_files(
    *,
    base_ref: str,
    head_ref: str,
    repo_dir: Path | None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    cwd = Path(repo_dir) if repo_dir is not None else Path.cwd()
    refs_to_try = [f"{base_ref}...{head_ref}"]
    if base_ref == "main":
        refs_to_try.append(f"origin/main...{head_ref}")
    warnings: list[str] = []
    for ref_expr in refs_to_try:
        try:
            completed = subprocess.run(
                ["git", "diff", "--name-only", ref_expr],
                cwd=cwd,
                check=False,
                capture_output=True,
                text=True,
            )
        except (OSError, FileNotFoundError) as exc:
            return (), (f"git diff is not available: {exc}",)
        if completed.returncode == 0:
            files = tuple(
                _normalize_path(line)
                for line in completed.stdout.splitlines()
                if line.strip()
            )
            return files, ()
        warnings.append(
            "git diff failed for "
            f"{ref_expr}: {completed.stderr.strip() or completed.stdout.strip()}"
        )
    warnings.append("unable to determine changed files from git diff")
    return (), tuple(warnings)


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip()
