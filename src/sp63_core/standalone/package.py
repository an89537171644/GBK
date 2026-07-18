"""Build a review-only Windows package for the standalone beam wrapper.

The builder deliberately produces command scripts and text assets, not an
executable or an installer.  A pure-Python project wheel may be copied into the
package when it is supplied by the release workflow.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

PACKAGE_FORMAT_VERSION = "1.1"
PACKAGE_WARNING = (
    "Исследовательский пакет для прямоугольной балки. Все схемы и числовые "
    "результаты имеют статус diagnostic_only; их выдача или трактовка как "
    "утверждённой несущей способности либо проектного решения запрещена."
)
FORBIDDEN_BINARY_SUFFIXES = (".bin", ".dll", ".dylib", ".exe", ".pyd", ".so")
RUNTIME_LOCK_RELATIVE_PATH = "requirements/runtime-py311.lock"
RUNTIME_PY311_LOCK = """# Фиксированные зависимости автономного маршрута для Python 3.11.
# Первая установка требует доступа к сети: пакеты не включены в ZIP.
# Версии сняты с нейтрального тестового профиля проекта 2026-07-18;
# обязательна отдельная чистая проверка Windows Actions на Python 3.11.
annotated-types==0.7.0
joblib==1.5.3
numpy==2.3.5
pandas==2.2.3
pydantic==2.13.4
pydantic-core==2.46.4
python-dateutil==2.9.0.post0
pytz==2026.2
scikit-learn==1.8.0
scipy==1.17.0
six==1.17.0
threadpoolctl==3.6.0
typing-extensions==4.15.0
typing-inspection==0.4.2
tzdata==2026.2
"""
BUILD_ID_FILENAME = ".gbk_build_id"
VERIFY_PACKAGE_POWERSHELL = r"""param(
    [string]$PackageRoot = $PSScriptRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

try {
    $root = [IO.Path]::GetFullPath($PackageRoot)
    $rootPrefix = $root.TrimEnd(
        [char[]]@([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
    ) + [IO.Path]::DirectorySeparatorChar
    $manifestPath = Join-Path $root "standalone_manifest.json"
    $sidecarPath = Join-Path $root "standalone_manifest.sha256"

    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        throw "standalone_manifest.json is missing"
    }
    if (-not (Test-Path -LiteralPath $sidecarPath -PathType Leaf)) {
        throw "standalone_manifest.sha256 is missing"
    }

    $sidecar = (Get-Content -LiteralPath $sidecarPath -Raw -Encoding UTF8).Trim()
    if ($sidecar -notmatch '^([0-9A-Fa-f]{64})\s{2}standalone_manifest\.json$') {
        throw "standalone_manifest.sha256 has an invalid format"
    }
    $expectedManifestHash = $Matches[1].ToLowerInvariant()
    $actualManifestHash = (
        Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256
    ).Hash.ToLowerInvariant()
    if ($actualManifestHash -ne $expectedManifestHash) {
        throw "standalone_manifest.json SHA-256 mismatch"
    }

    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 |
        ConvertFrom-Json
    $records = @($manifest.files)
    if ([int64]$manifest.file_count -ne $records.Count) {
        throw "manifest file_count does not match files records"
    }

    $seen = @{}
    foreach ($record in $records) {
        $relative = [string]$record.relative_path
        if ([string]::IsNullOrWhiteSpace($relative)) {
            throw "manifest contains an empty relative_path"
        }
        if (
            [IO.Path]::IsPathRooted($relative) -or
            $relative.Contains("\") -or
            $relative.Contains(":")
        ) {
            throw "manifest path is not a safe POSIX relative path: $relative"
        }
        $parts = @($relative.Split('/'))
        if ($parts.Count -eq 0 -or $parts -contains "" -or $parts -contains "." -or
            $parts -contains "..") {
            throw "manifest path contains an unsafe component: $relative"
        }
        if ($seen.ContainsKey($relative)) {
            throw "manifest contains a duplicate path: $relative"
        }
        $seen[$relative] = $true

        $nativeRelative = $relative.Replace('/', [IO.Path]::DirectorySeparatorChar)
        $candidate = [IO.Path]::GetFullPath((Join-Path $root $nativeRelative))
        if (-not $candidate.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw "manifest path escapes the package root: $relative"
        }
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            throw "manifest payload is missing: $relative"
        }
        $file = Get-Item -LiteralPath $candidate -Force
        if (($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "manifest payload must not be a reparse point: $relative"
        }

        if ($null -eq $record.size_bytes) {
            throw "manifest size is missing: $relative"
        }
        $expectedSize = [int64]$record.size_bytes
        if ($expectedSize -lt 0 -or $file.Length -ne $expectedSize) {
            throw "manifest size mismatch: $relative"
        }
        $expectedHash = [string]$record.sha256
        if ($expectedHash -notmatch '^[0-9A-Fa-f]{64}$') {
            throw "manifest SHA-256 is invalid: $relative"
        }
        $actualHash = (
            Get-FileHash -LiteralPath $candidate -Algorithm SHA256
        ).Hash.ToLowerInvariant()
        if ($actualHash -ne $expectedHash.ToLowerInvariant()) {
            throw "manifest SHA-256 mismatch: $relative"
        }
    }

    Write-Host "Package integrity check passed for $($records.Count) payload files."
    exit 0
}
catch {
    [Console]::Error.WriteLine("Package integrity check failed: $($_.Exception.Message)")
    exit 2
}
"""
VERIFY_ONE_CLICK_RESULT_POWERSHELL = r"""Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-Sha256Hex([byte[]]$Bytes) {
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        return (($algorithm.ComputeHash($Bytes) | ForEach-Object {
            $_.ToString("x2")
        }) -join "")
    }
    finally {
        $algorithm.Dispose()
    }
}

function Read-ZipEntryBytes($Entry) {
    $stream = $Entry.Open()
    $memory = [IO.MemoryStream]::new()
    try {
        $stream.CopyTo($memory)
        return ,$memory.ToArray()
    }
    finally {
        $stream.Dispose()
        $memory.Dispose()
    }
}

try {
    $root = [IO.Path]::GetFullPath($PSScriptRoot)
    $output = Join-Path $root "output\beam_example"
    $statusPath = Join-Path $output "standalone_latest_status.json"
    $landingPath = Join-Path $output "standalone_index.html"
    $bundlePath = Join-Path $output "standalone_review_bundle.zip"
    $metadataPath = Join-Path $output "standalone_review_metadata.json"
    $manifestPath = Join-Path $root "standalone_manifest.json"

    foreach ($required in @(
        $statusPath, $landingPath, $bundlePath, $metadataPath, $manifestPath
    )) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "required one-click result file is missing: $required"
        }
    }

    $status = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 |
        ConvertFrom-Json
    if ($status.status -ne "review_required") {
        throw "standalone status is not review_required: $($status.status)"
    }
    if ($status.preflight_status -ne "pass") {
        throw "standalone preflight did not pass"
    }
    if ($status.project_use -ne $false -or
        $status.project_use_status -ne "prohibited") {
        throw "standalone project-use guard is invalid"
    }
    if ($status.requires_engineer_review -ne $true) {
        throw "standalone engineer-review guard is invalid"
    }
    if ($status.reinforcement_selection_status -ne "diagnostic_only") {
        throw "reinforcement selection is not diagnostic_only"
    }
    if ($status.calculation_status -ne "outside_applicability") {
        throw "control-example calculation status is unexpected"
    }
    if ($status.evidence_status -ne "needs_engineer_review") {
        throw "control-example evidence status is unexpected"
    }
    if ($status.ml_included -ne $false) {
        throw "ML must not be included in the standalone route"
    }

    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 |
        ConvertFrom-Json
    $metadata = Get-Content -LiteralPath $metadataPath -Raw -Encoding UTF8 |
        ConvertFrom-Json
    $expectedBuildId = "wheel-sha256:$($manifest.wheel_sha256)"
    if (
        $metadata.code_identity.code_identity_status -ne
        "recorded_from_launcher_requires_manifest_match"
    ) {
        throw "standalone build identity status is not acceptable"
    }
    if ($metadata.code_identity.build_id -ne $expectedBuildId) {
        throw "standalone build identity does not match the package manifest"
    }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $expectedPayloadNames = @(
        "standalone_input.json",
        "canonical_input.json",
        "standalone_bundle_status.json",
        "standalone_review_metadata.json",
        "workflow_summary.json",
        "index.html",
        "README_REVIEW_BUNDLE.md",
        "deterministic_report/input.json",
        "deterministic_report/report.json",
        "deterministic_report/report.md",
        "deterministic_report/report.html"
    )
    $reviewManifestName = "standalone_review_manifest.json"
    $reviewSidecarName = "standalone_review_manifest.sha256"
    $expectedNames = @(
        $expectedPayloadNames + @($reviewManifestName, $reviewSidecarName)
    )
    $archive = [IO.Compression.ZipFile]::OpenRead($bundlePath)
    try {
        $names = @($archive.Entries | ForEach-Object { $_.FullName })
        if (@($names | Sort-Object -Unique).Count -ne $names.Count) {
            throw "review bundle contains duplicate members"
        }
        if (@(Compare-Object $expectedNames $names).Count -ne 0) {
            throw "review bundle members do not match the required contract"
        }

        $reviewManifestEntry = $archive.GetEntry($reviewManifestName)
        $reviewSidecarEntry = $archive.GetEntry($reviewSidecarName)
        [byte[]]$reviewManifestBytes = Read-ZipEntryBytes $reviewManifestEntry
        [byte[]]$reviewSidecarBytes = Read-ZipEntryBytes $reviewSidecarEntry
        $reviewManifestHash = Get-Sha256Hex $reviewManifestBytes
        $reviewSidecar = [Text.Encoding]::ASCII.GetString(
            $reviewSidecarBytes
        ).Trim()
        $expectedSidecar = "$reviewManifestHash  $reviewManifestName"
        if ($reviewSidecar -ne $expectedSidecar) {
            throw "review bundle manifest sidecar mismatch"
        }
        $reviewManifest = (
            [Text.Encoding]::UTF8.GetString($reviewManifestBytes) |
            ConvertFrom-Json
        )
        if ($reviewManifest.report_type -ne "standalone_review_bundle_manifest" -or
            $reviewManifest.path_scope -ne "bundle_relative") {
            throw "review bundle manifest identity is invalid"
        }
        if ($reviewManifest.project_use -ne $false -or
            $reviewManifest.requires_engineer_review -ne $true -or
            $reviewManifest.reinforcement_selection_status -ne "diagnostic_only") {
            throw "review bundle manifest safety guards are invalid"
        }

        $records = @($reviewManifest.files)
        $recordNames = @($records | ForEach-Object { [string]$_.path })
        if (@(Compare-Object $expectedPayloadNames $recordNames).Count -ne 0 -or
            @($recordNames | Sort-Object -Unique).Count -ne $recordNames.Count) {
            throw "review bundle manifest file records are incomplete"
        }
        foreach ($record in $records) {
            $relative = [string]$record.path
            if ([string]::IsNullOrWhiteSpace($relative) -or
                [IO.Path]::IsPathRooted($relative) -or
                $relative.Contains("\") -or $relative.Contains(":") -or
                @($relative.Split('/')) -contains "..") {
                throw "review bundle manifest contains an unsafe path"
            }
            $entry = $archive.GetEntry($relative)
            if ($null -eq $entry) {
                throw "review bundle payload is missing: $relative"
            }
            [byte[]]$entryBytes = Read-ZipEntryBytes $entry
            if ([int64]$record.size_bytes -ne $entryBytes.LongLength) {
                throw "review bundle payload size mismatch: $relative"
            }
            if ([string]$record.sha256 -ne (Get-Sha256Hex $entryBytes)) {
                throw "review bundle payload hash mismatch: $relative"
            }
        }

        [byte[]]$zipMetadataBytes = Read-ZipEntryBytes (
            $archive.GetEntry("standalone_review_metadata.json")
        )
        $zipMetadata = (
            [Text.Encoding]::UTF8.GetString($zipMetadataBytes) |
            ConvertFrom-Json
        )
        if ($zipMetadata.code_identity.code_identity_status -ne
            "recorded_from_launcher_requires_manifest_match" -or
            $zipMetadata.code_identity.build_id -ne $expectedBuildId) {
            throw "review bundle code identity does not match the package"
        }
    }
    finally {
        $archive.Dispose()
    }

    Write-Host "one_click_verification=pass"
    Write-Host "status=$($status.status)"
    Write-Host "calculation_status=$($status.calculation_status)"
    Write-Host "evidence_status=$($status.evidence_status)"
    Write-Host "project_use=false"
    Write-Host "requires_engineer_review=true"
    Write-Host "reinforcement_selection_status=diagnostic_only"
    Write-Host "build_id=$expectedBuildId"
    exit 0
}
catch {
    [Console]::Error.WriteLine(
        "One-click result verification failed: $($_.Exception.Message)"
    )
    exit 2
}
"""

ONE_CLICK_GUARD_POWERSHELL = r"""param(
    [ValidateSet("0", "1")]
    [string]$CiMode = "0"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$mutex = $null
$acquired = $false

try {
    $root = [IO.Path]::GetFullPath($PSScriptRoot)
    $worker = Join-Path $root "ONE_CLICK_WORKER.cmd"
    if (-not (Test-Path -LiteralPath $worker -PathType Leaf)) {
        throw "ONE_CLICK_WORKER.cmd is missing"
    }
    $rootBytes = [Text.Encoding]::UTF8.GetBytes($root.ToUpperInvariant())
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        $digest = (($algorithm.ComputeHash($rootBytes) | ForEach-Object {
            $_.ToString("x2")
        }) -join "")
    }
    finally {
        $algorithm.Dispose()
    }
    $mutex = [Threading.Mutex]::new(
        $false,
        "Local\GBK_Standalone_$digest"
    )
    try {
        $acquired = $mutex.WaitOne(0, $false)
    }
    catch [Threading.AbandonedMutexException] {
        $acquired = $true
    }
    if (-not $acquired) {
        [Console]::Error.WriteLine(
            "ОШИБКА: установка уже запущена в другом окне."
        )
        exit 3
    }

    $workerArgument = if ($CiMode -eq "1") { "--ci" } else { "" }
    $command = "call `"$worker`" $workerArgument"
    $process = Start-Process -FilePath $env:ComSpec -ArgumentList @(
        "/d", "/c", $command
    ) -Wait -PassThru -NoNewWindow
    exit $process.ExitCode
}
catch {
    [Console]::Error.WriteLine(
        "Ошибка защищённого запуска: $($_.Exception.Message)"
    )
    exit 2
}
finally {
    if ($acquired -and $null -ne $mutex) {
        $mutex.ReleaseMutex()
    }
    if ($null -ne $mutex) {
        $mutex.Dispose()
    }
}
"""

BEAM_EXAMPLE: dict[str, str | float] = {
    "case_id": "beam-demo-001",
    "b_mm": 300.0,
    "h_mm": 500.0,
    "cover_mm": 32.0,
    "stirrup_diameter_mm": 8.0,
    "concrete_class": "B25",
    "longitudinal_rebar_class": "A500",
    "stirrup_rebar_class": "A240",
    "moment_kNm": 150.0,
    "shear_kN": 80.0,
    "tension_face": "local_y_min",
}


@dataclass(frozen=True, slots=True)
class StandaloneWindowsPackageResult:
    """Result of generating a source- or wheel-oriented Windows package."""

    status: str
    package_status: str
    output_dir: str
    distribution_mode: str
    wheel_included: bool
    wheel_filename: str | None
    wheel_sha256: str | None
    manifest_path: str
    manifest_sha256_path: str
    readme_path: str
    generated_files: tuple[str, ...]
    file_count: int
    script_count: int
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    element_type: str = "rectangular_beam"
    load_duration: str = "short"
    project_use: bool = False
    project_use_status: str = "prohibited"
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    ml_included: bool = False
    external_solver_required: bool = False


def build_standalone_windows_package(
    output_dir: Path,
    wheel_path: Path | None = None,
) -> StandaloneWindowsPackageResult:
    """Create a Windows package skeleton for the standalone beam command.

    ``wheel_path`` is optional so developers can generate a source-install
    skeleton before a wheel has been built.  A supplied wheel is accepted only
    when it is a safe, pure-Python wheel without native binary members.
    """
    output_path = Path(output_dir)
    _require_empty_output_directory(output_path)
    input_dir = output_path / "input"
    docs_dir = output_path / "docs"
    requirements_dir = output_path / "requirements"
    wheel_dir = output_path / "wheel"
    for directory in (output_path, input_dir, docs_dir, requirements_dir, wheel_dir):
        directory.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    warnings = [PACKAGE_WARNING]
    payload_files: list[Path] = []
    bundled_wheel: Path | None = None
    wheel_sha256: str | None = None

    if wheel_path is None:
        distribution_mode = "source"
        warnings.append(
            "Wheel не включён. INSTALL_FROM_SOURCE.cmd требует явно указать "
            "каталог исходного проекта."
        )
    else:
        distribution_mode = "wheel"
        wheel_errors = _validate_pure_python_wheel(Path(wheel_path))
        errors.extend(wheel_errors)
        if not wheel_errors:
            bundled_wheel = wheel_dir / Path(wheel_path).name
            shutil.copyfile(wheel_path, bundled_wheel)
            payload_files.append(bundled_wheel)
            wheel_sha256 = _sha256(bundled_wheel)

    runtime_lock_path = output_path / RUNTIME_LOCK_RELATIVE_PATH
    runtime_lock_path.write_text(RUNTIME_PY311_LOCK, encoding="utf-8")
    payload_files.append(runtime_lock_path)

    scripts = _script_specs(bundled_wheel, wheel_sha256)
    for filename, content in scripts.items():
        path = output_path / filename
        encoding = "utf-8-sig" if path.suffix.casefold() == ".ps1" else "utf-8"
        path.write_text(content, encoding=encoding, newline="\r\n")
        payload_files.append(path)

    example_path = input_dir / "beam_example.json"
    example_path.write_text(
        json.dumps(BEAM_EXAMPLE, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    payload_files.append(example_path)

    readme_path = output_path / "README_STANDALONE_WINDOWS.md"
    scope_path = docs_dir / "SCOPE.md"
    install_path = docs_dir / "WINDOWS_INSTALL.md"
    checklist_path = docs_dir / "USER_ACCEPTANCE_CHECKLIST.md"
    readme_path.write_text(_render_package_readme(distribution_mode), encoding="utf-8")
    scope_path.write_text(_render_scope(), encoding="utf-8")
    install_path.write_text(
        _render_windows_install(distribution_mode),
        encoding="utf-8",
    )
    checklist_path.write_text(
        _render_acceptance_checklist(distribution_mode),
        encoding="utf-8",
    )
    payload_files.extend((readme_path, scope_path, install_path, checklist_path))

    _assert_complete_payload_set(output_path, payload_files)
    status = "fail" if errors else "pass"
    manifest_path = output_path / "standalone_manifest.json"
    manifest_sha256_path = output_path / "standalone_manifest.sha256"
    manifest = _build_manifest(
        output_dir=output_path,
        payload_files=tuple(payload_files),
        status=status,
        distribution_mode=distribution_mode,
        wheel_filename=bundled_wheel.name if bundled_wheel else None,
        wheel_sha256=wheel_sha256,
        warnings=tuple(warnings),
        errors=tuple(errors),
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest_sha256_path.write_text(
        f"{_sha256(manifest_path)}  {manifest_path.name}\n",
        encoding="utf-8",
    )

    generated_files = (*payload_files, manifest_path, manifest_sha256_path)
    return StandaloneWindowsPackageResult(
        status=status,
        package_status=status,
        output_dir=str(output_path),
        distribution_mode=distribution_mode,
        wheel_included=bundled_wheel is not None,
        wheel_filename=bundled_wheel.name if bundled_wheel else None,
        wheel_sha256=wheel_sha256,
        manifest_path=str(manifest_path),
        manifest_sha256_path=str(manifest_sha256_path),
        readme_path=str(readme_path),
        generated_files=tuple(str(path) for path in generated_files),
        file_count=len(payload_files),
        script_count=len(scripts),
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def _require_empty_output_directory(output_path: Path) -> None:
    """Refuse to overwrite any existing package content."""
    if output_path.is_symlink():
        raise FileExistsError(f"output_dir must not be a symbolic link: {output_path}")
    if not output_path.exists():
        return
    if not output_path.is_dir():
        raise FileExistsError(f"output_dir exists and is not a directory: {output_path}")
    if next(output_path.iterdir(), None) is not None:
        raise FileExistsError(f"output_dir must be empty: {output_path}")


def _assert_complete_payload_set(output_path: Path, payload_files: list[Path]) -> None:
    """Require every generated pre-manifest file to be integrity-recorded."""
    expected = {path.relative_to(output_path).as_posix() for path in payload_files}
    actual = {
        path.relative_to(output_path).as_posix()
        for path in output_path.rglob("*")
        if path.is_file()
    }
    if actual != expected:
        missing = sorted(actual - expected)
        absent = sorted(expected - actual)
        raise RuntimeError(
            "standalone payload inventory mismatch: "
            f"unrecorded={missing}; absent={absent}"
        )


def _script_specs(
    bundled_wheel: Path | None,
    wheel_sha256: str | None,
) -> dict[str, str]:
    wheel_name = bundled_wheel.name if bundled_wheel else "WHEEL_FILE_REQUIRED.whl"
    return {
        "01_START_HERE.cmd": _start_here_script(
            wheel_available=bundled_wheel is not None,
        ),
        "ONE_CLICK_GUARD.ps1": ONE_CLICK_GUARD_POWERSHELL,
        "ONE_CLICK_WORKER.cmd": _one_click_worker_script(),
        "VERIFY_PACKAGE.ps1": VERIFY_PACKAGE_POWERSHELL,
        "VERIFY_PACKAGE.cmd": _verify_package_cmd_script(),
        "VERIFY_ONE_CLICK_RESULT.ps1": VERIFY_ONE_CLICK_RESULT_POWERSHELL,
        "INSTALL_FROM_WHEEL.cmd": _install_from_wheel_script(
            wheel_name,
            wheel_sha256,
        ),
        "INSTALL_FROM_SOURCE.cmd": _install_from_source_script(),
        "RUN_INTERACTIVE.cmd": _run_interactive_script(),
        "RUN_JSON.cmd": _run_json_script(),
        "RUN_JSON_USER.cmd": _run_json_user_script(),
        "OPEN_RESULTS.cmd": _open_results_script(),
    }


def _cmd_preamble() -> list[str]:
    return [
        "@echo off",
        "setlocal",
        "chcp 65001 >nul",
        'set "PYTHONUTF8=1"',
        'set "ROOT=%~dp0"',
        'cd /d "%ROOT%" || exit /b 1',
    ]


def _start_here_script(*, wheel_available: bool) -> str:
    if not wheel_available:
        return "\n".join(
            [
                *_cmd_preamble(),
                "echo ОШИБКА: это исходный пакет разработчика без готового wheel.",
                "echo Однокнопочная установка доступна только в пользовательском ZIP.",
                'if /I not "%~1"=="--ci" pause',
                "exit /b 2",
                "",
            ]
        )
    return "\n".join(
        [
            *_cmd_preamble(),
            'set "CI_MODE=0"',
            'if /I "%~1"=="--ci" set "CI_MODE=1"',
            "powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass "
            '-File "%ROOT%ONE_CLICK_GUARD.ps1" -CiMode "%CI_MODE%"',
            'set "FINAL_RC=%ERRORLEVEL%"',
            'if "%CI_MODE%"=="0" pause',
            'exit /b %FINAL_RC%',
            "",
        ]
    )


def _one_click_worker_script() -> str:
    return "\n".join(
        [
            *_cmd_preamble(),
            'set "CI_MODE=0"',
            'if /I "%~1"=="--ci" set "CI_MODE=1"',
            'set "FINAL_RC=1"',
            'set "INSTALL_LOG=%ROOT%INSTALLATION_LOG.txt"',
            'set "RUN_LOG=%ROOT%EXAMPLE_RUN_LOG.txt"',
            'set "RESULT_PATH=%ROOT%output\\beam_example\\standalone_index.html"',
            "echo ============================================================",
            "echo GBK: автоматическая установка и запуск контрольного примера",
            "echo Не закрывайте окно. Первая установка может занять несколько минут.",
            "echo ============================================================",
            "echo.",
            "echo Шаг 1 из 2: проверка и установка...",
            '> "%INSTALL_LOG%" echo GBK installation log',
            "if errorlevel 1 goto :install_log_failed",
            '>> "%INSTALL_LOG%" echo Started: %DATE% %TIME%',
            'call "%ROOT%INSTALL_FROM_WHEEL.cmd" >> "%INSTALL_LOG%" 2>&1',
            'set "INSTALL_RC=%ERRORLEVEL%"',
            'type "%INSTALL_LOG%"',
            'if not "%INSTALL_RC%"=="0" goto :install_failed',
            "echo.",
            "echo Шаг 2 из 2: запуск контрольного примера...",
            '> "%RUN_LOG%" echo GBK example run log',
            "if errorlevel 1 goto :run_log_failed",
            '>> "%RUN_LOG%" echo Started: %DATE% %TIME%',
            'call "%ROOT%RUN_JSON.cmd" >> "%RUN_LOG%" 2>&1',
            'set "RUN_RC=%ERRORLEVEL%"',
            'if not "%RUN_RC%"=="0" goto :run_failed',
            "powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass "
            '-File "%ROOT%VERIFY_ONE_CLICK_RESULT.ps1" >> "%RUN_LOG%" 2>&1',
            'set "VERIFY_RC=%ERRORLEVEL%"',
            'type "%RUN_LOG%"',
            'if not "%VERIFY_RC%"=="0" goto :result_verification_failed',
            'if "%CI_MODE%"=="0" start "" "%RESULT_PATH%"',
            'if errorlevel 1 set "BROWSER_WARNING=1"',
            "echo.",
            "echo ============================================================",
            "echo ГОТОВО: установка и контрольный запуск завершены.",
            "echo Результат: %RESULT_PATH%",
            "echo project_use=false; требуется инженерная проверка.",
            "echo ============================================================",
            'if defined BROWSER_WARNING echo Отчёт готов, но браузер не открылся.',
            'if defined BROWSER_WARNING echo Откройте вручную: %RESULT_PATH%',
            'set "FINAL_RC=0"',
            "goto :finish",
            "",
            ":install_log_failed",
            "echo ОШИБКА: не удаётся создать журнал установки в папке программы.",
            'set "FINAL_RC=2"',
            "goto :finish",
            "",
            ":install_failed",
            "echo.",
            "echo ОШИБКА: установка не завершена. Код: %INSTALL_RC%",
            "echo Журнал: %INSTALL_LOG%",
            "echo Пришлите скриншот последних строк этого окна.",
            'set "FINAL_RC=%INSTALL_RC%"',
            "goto :finish",
            "",
            ":run_log_failed",
            "echo ОШИБКА: не удаётся создать журнал контрольного запуска.",
            'set "FINAL_RC=2"',
            "goto :finish",
            "",
            ":run_failed",
            'type "%RUN_LOG%"',
            "echo.",
            "echo ОШИБКА: контрольный пример не завершён. Код: %RUN_RC%",
            "echo Журнал: %RUN_LOG%",
            "echo Пришлите скриншот последних строк этого окна.",
            'set "FINAL_RC=%RUN_RC%"',
            "goto :finish",
            "",
            ":result_verification_failed",
            "echo.",
            "echo ОШИБКА: итоговые защитные проверки не пройдены.",
            "echo Журнал: %RUN_LOG%",
            "echo Отчёт автоматически не открывается.",
            'set "FINAL_RC=%VERIFY_RC%"',
            "goto :finish",
            "",
            ":finish",
            'exit /b %FINAL_RC%',
            "",
        ]
    )


def _verify_package_cmd_script() -> str:
    return "\n".join(
        [
            *_cmd_preamble(),
            "powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass "
            '-File "%ROOT%VERIFY_PACKAGE.ps1"',
            'set "RC=%ERRORLEVEL%"',
            'exit /b %RC%',
            "",
        ]
    )


def _install_from_wheel_script(wheel_name: str, wheel_sha256: str | None) -> str:
    expected_hash = wheel_sha256 or "WHEEL_SHA256_NOT_AVAILABLE"
    return "\n".join(
        [
            *_cmd_preamble(),
            'call "%ROOT%VERIFY_PACKAGE.cmd" || exit /b 2',
            f'set "WHEEL_PATH=%ROOT%wheel\\{wheel_name}"',
            f'set "EXPECTED_WHEEL_SHA256={expected_hash}"',
            f'set "EXPECTED_BUILD_ID=wheel-sha256:{expected_hash}"',
            'if not "%~1"=="" set "WHEEL_PATH=%~f1"',
            'if not exist "%WHEEL_PATH%" (',
            "  echo ОШИБКА: файл wheel не найден: %WHEEL_PATH%",
            "  exit /b 2",
            ")",
            'if "%EXPECTED_WHEEL_SHA256%"=="WHEEL_SHA256_NOT_AVAILABLE" (',
            "  echo ОШИБКА: ожидаемый SHA-256 wheel не включён в этот пакет.",
            "  echo Сформируйте пакет заново с проверенным wheel.",
            "  exit /b 2",
            ")",
            'set "GBK_WHEEL_PATH=%WHEEL_PATH%"',
            'set "ACTUAL_WHEEL_SHA256="',
            "for /f \"usebackq delims=\" %%H in (`powershell -NoProfile "
            '-NonInteractive -Command "$p=$env:GBK_WHEEL_PATH; '
            "(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()\"`) "
            'do set "ACTUAL_WHEEL_SHA256=%%H"',
            'set "GBK_WHEEL_PATH="',
            'if not defined ACTUAL_WHEEL_SHA256 (',
            "  echo ОШИБКА: не удалось вычислить SHA-256 wheel.",
            "  exit /b 2",
            ")",
            'if /I not "%ACTUAL_WHEEL_SHA256%"=="%EXPECTED_WHEEL_SHA256%" (',
            "  echo ОШИБКА: SHA-256 wheel не совпадает с ожидаемым.",
            "  echo Ожидается: %EXPECTED_WHEEL_SHA256%",
            "  echo Получено:  %ACTUAL_WHEEL_SHA256%",
            "  exit /b 2",
            ")",
            'set "NEW_VENV=%ROOT%.venv.new"',
            'set "PREVIOUS_VENV=%ROOT%.venv.previous"',
            'if not exist "%ROOT%.venv" if exist "%PREVIOUS_VENV%" (',
            '  move "%PREVIOUS_VENV%" "%ROOT%.venv" >nul',
            "  if errorlevel 1 (",
            "    echo ОШИБКА: не удалось восстановить предыдущую рабочую среду.",
            "    exit /b 2",
            "  )",
            ")",
            "where py >nul 2>nul || (",
            "  echo ОШИБКА: Python Launcher не найден. Установите Python 3.11.",
            "  exit /b 2",
            ")",
            'py -3.11 -c "import struct,sys; '
            "sys.exit(0 if struct.calcsize('P') * 8 == 64 else 1)\" || (",
            "  echo ОШИБКА: требуется 64-разрядный Python 3.11.",
            "  exit /b 2",
            ")",
            'if exist "%NEW_VENV%" rmdir /s /q "%NEW_VENV%"',
            'if exist "%NEW_VENV%" (',
            "  echo ОШИБКА: не удалось очистить временное окружение.",
            "  exit /b 2",
            ")",
            'if exist "%PREVIOUS_VENV%" rmdir /s /q "%PREVIOUS_VENV%"',
            'if exist "%PREVIOUS_VENV%" (',
            "  echo ОШИБКА: не удалось очистить резервное окружение.",
            "  exit /b 2",
            ")",
            'py -3.11 -m venv "%NEW_VENV%" || exit /b 1',
            '"%NEW_VENV%\\Scripts\\python.exe" -m pip install --no-deps '
            '-r "%ROOT%requirements\\runtime-py311.lock" || exit /b 1',
            '"%NEW_VENV%\\Scripts\\python.exe" -m pip install --no-deps '
            '"%WHEEL_PATH%" || exit /b 1',
            '"%NEW_VENV%\\Scripts\\python.exe" -m pip check || exit /b 1',
            '"%NEW_VENV%\\Scripts\\python.exe" -c "import sp63_core.standalone" '
            "|| exit /b 1",
            f'> "%NEW_VENV%\\{BUILD_ID_FILENAME}.tmp" echo %EXPECTED_BUILD_ID%',
            f'move /y "%NEW_VENV%\\{BUILD_ID_FILENAME}.tmp" '
            f'"%NEW_VENV%\\{BUILD_ID_FILENAME}" >nul || exit /b 1',
            'set "HAS_PREVIOUS_VENV=0"',
            'if exist "%ROOT%.venv" (',
            '  move "%ROOT%.venv" "%PREVIOUS_VENV%" >nul',
            "  if errorlevel 1 (",
            "    echo ОШИБКА: не удалось сохранить предыдущую рабочую среду.",
            "    exit /b 1",
            "  )",
            '  set "HAS_PREVIOUS_VENV=1"',
            ")",
            'move "%NEW_VENV%" "%ROOT%.venv" >nul',
            "if errorlevel 1 goto :activation_failed",
            'if exist "%PREVIOUS_VENV%" rmdir /s /q "%PREVIOUS_VENV%"',
            'if exist "%PREVIOUS_VENV%" echo ПРЕДУПРЕЖДЕНИЕ: резервная среда не удалена.',
            "echo Автономный пакет для балки установлен.",
            "exit /b 0",
            "",
            ":activation_failed",
            'if "%HAS_PREVIOUS_VENV%"=="1" move '
            '"%PREVIOUS_VENV%" "%ROOT%.venv" >nul',
            'if "%HAS_PREVIOUS_VENV%"=="1" if errorlevel 1 goto :restore_failed',
            "echo ОШИБКА: не удалось активировать новую среду; предыдущая сохранена.",
            "exit /b 1",
            "",
            ":restore_failed",
            "echo ОШИБКА: автоматическое восстановление не завершено.",
            "echo Предыдущая среда сохранена в .venv.previous; передайте этот экран.",
            "exit /b 1",
            "",
        ]
    )


def _install_from_source_script() -> str:
    return "\n".join(
        [
            *_cmd_preamble(),
            'call "%ROOT%VERIFY_PACKAGE.cmd" || exit /b 2',
            'set "SOURCE_DIR=%~1"',
            'if "%SOURCE_DIR%"=="" (',
            "  echo Использование: INSTALL_FROM_SOURCE.cmd ^<каталог-исходного-проекта^>",
            "  exit /b 2",
            ")",
            'for %%I in ("%SOURCE_DIR%") do set "SOURCE_DIR=%%~fI"',
            'if not exist "%SOURCE_DIR%\\pyproject.toml" (',
            "  echo ОШИБКА: pyproject.toml не найден в %SOURCE_DIR%",
            "  exit /b 2",
            ")",
            'set "NEW_VENV=%ROOT%.venv.new"',
            'set "PREVIOUS_VENV=%ROOT%.venv.previous"',
            'if not exist "%ROOT%.venv" if exist "%PREVIOUS_VENV%" (',
            '  move "%PREVIOUS_VENV%" "%ROOT%.venv" >nul',
            "  if errorlevel 1 (",
            "    echo ОШИБКА: не удалось восстановить предыдущую рабочую среду.",
            "    exit /b 2",
            "  )",
            ")",
            "where py >nul 2>nul || (",
            "  echo ОШИБКА: Python Launcher не найден. Установите Python 3.11.",
            "  exit /b 2",
            ")",
            'py -3.11 -c "import struct,sys; '
            "sys.exit(0 if struct.calcsize('P') * 8 == 64 else 1)\" || (",
            "  echo ОШИБКА: требуется 64-разрядный Python 3.11.",
            "  exit /b 2",
            ")",
            'if exist "%NEW_VENV%" rmdir /s /q "%NEW_VENV%"',
            'if exist "%NEW_VENV%" (',
            "  echo ОШИБКА: не удалось очистить временное окружение.",
            "  exit /b 2",
            ")",
            'if exist "%PREVIOUS_VENV%" rmdir /s /q "%PREVIOUS_VENV%"',
            'if exist "%PREVIOUS_VENV%" (',
            "  echo ОШИБКА: не удалось очистить резервное окружение.",
            "  exit /b 2",
            ")",
            'py -3.11 -m venv "%NEW_VENV%" || exit /b 1',
            '"%NEW_VENV%\\Scripts\\python.exe" -m pip install --no-deps '
            '-r "%ROOT%requirements\\runtime-py311.lock" || exit /b 1',
            '"%NEW_VENV%\\Scripts\\python.exe" -m pip install --no-deps '
            '"%SOURCE_DIR%" || exit /b 1',
            '"%NEW_VENV%\\Scripts\\python.exe" -m pip check || exit /b 1',
            '"%NEW_VENV%\\Scripts\\python.exe" -c "import sp63_core.standalone" '
            "|| exit /b 1",
            f'> "%NEW_VENV%\\{BUILD_ID_FILENAME}.tmp" echo source-unverified',
            f'move /y "%NEW_VENV%\\{BUILD_ID_FILENAME}.tmp" '
            f'"%NEW_VENV%\\{BUILD_ID_FILENAME}" >nul || exit /b 1',
            'set "HAS_PREVIOUS_VENV=0"',
            'if exist "%ROOT%.venv" (',
            '  move "%ROOT%.venv" "%PREVIOUS_VENV%" >nul',
            "  if errorlevel 1 (",
            "    echo ОШИБКА: не удалось сохранить предыдущую рабочую среду.",
            "    exit /b 1",
            "  )",
            '  set "HAS_PREVIOUS_VENV=1"',
            ")",
            'move "%NEW_VENV%" "%ROOT%.venv" >nul',
            "if errorlevel 1 goto :activation_failed",
            'if exist "%PREVIOUS_VENV%" rmdir /s /q "%PREVIOUS_VENV%"',
            'if exist "%PREVIOUS_VENV%" echo ПРЕДУПРЕЖДЕНИЕ: резервная среда не удалена.',
            "echo Автономный пакет для балки установлен из исходного проекта.",
            "exit /b 0",
            "",
            ":activation_failed",
            'if "%HAS_PREVIOUS_VENV%"=="1" move '
            '"%PREVIOUS_VENV%" "%ROOT%.venv" >nul',
            'if "%HAS_PREVIOUS_VENV%"=="1" if errorlevel 1 goto :restore_failed',
            "echo ОШИБКА: не удалось активировать новую среду; предыдущая сохранена.",
            "exit /b 1",
            "",
            ":restore_failed",
            "echo ОШИБКА: автоматическое восстановление не завершено.",
            "echo Предыдущая среда сохранена в .venv.previous; передайте этот экран.",
            "exit /b 1",
            "",
        ]
    )


def _run_interactive_script() -> str:
    return "\n".join(
        [
            *_cmd_preamble(),
            f'set "BUILD_ID_PATH=%ROOT%.venv\\{BUILD_ID_FILENAME}"',
            'if not exist "%BUILD_ID_PATH%" (',
            "  echo ОШИБКА: идентификатор установленной сборки отсутствует.",
            '  set "RC=2"',
            "  goto :finish",
            ")",
            'set "GBK_BUILD_ID="',
            'set /p "GBK_BUILD_ID="<"%BUILD_ID_PATH%"',
            'if not defined GBK_BUILD_ID (',
            "  echo ОШИБКА: идентификатор установленной сборки пуст.",
            '  set "RC=2"',
            "  goto :finish",
            ")",
            'set "APP_PYTHON=%ROOT%.venv\\Scripts\\python.exe"',
            'if not exist "%APP_PYTHON%" (',
            "  echo ОШИБКА: пакет не установлен. Сначала запустите INSTALL-скрипт.",
            '  set "RC=2"',
            "  goto :finish",
            ")",
            '"%APP_PYTHON%" -m sp63_core.standalone',
            'set "RC=%ERRORLEVEL%"',
            ":finish",
            "pause",
            'exit /b %RC%',
            "",
        ]
    )


def _run_json_script() -> str:
    return "\n".join(
        [
            *_cmd_preamble(),
            f'set "BUILD_ID_PATH=%ROOT%.venv\\{BUILD_ID_FILENAME}"',
            'if not exist "%BUILD_ID_PATH%" (',
            "  echo ОШИБКА: идентификатор установленной сборки отсутствует.",
            "  exit /b 2",
            ")",
            'set "GBK_BUILD_ID="',
            'set /p "GBK_BUILD_ID="<"%BUILD_ID_PATH%"',
            'if not defined GBK_BUILD_ID (',
            "  echo ОШИБКА: идентификатор установленной сборки пуст.",
            "  exit /b 2",
            ")",
            'set "APP_PYTHON=%ROOT%.venv\\Scripts\\python.exe"',
            'set "INPUT_PATH=%ROOT%input\\beam_example.json"',
            'set "OUTPUT_PATH=%ROOT%output\\beam_example"',
            'if not "%~1"=="" set "INPUT_PATH=%~f1"',
            'if not "%~2"=="" set "OUTPUT_PATH=%~f2"',
            'if not exist "%APP_PYTHON%" (',
            "  echo ОШИБКА: пакет не установлен. Сначала запустите INSTALL-скрипт.",
            "  exit /b 2",
            ")",
            'if not exist "%INPUT_PATH%" (',
            "  echo ОШИБКА: входной JSON не найден: %INPUT_PATH%",
            "  exit /b 2",
            ")",
            '"%APP_PYTHON%" -m sp63_core.standalone --input-json "%INPUT_PATH%" '
            '--output-dir "%OUTPUT_PATH%" --json',
            'set "RC=%ERRORLEVEL%"',
            'exit /b %RC%',
            "",
        ]
    )


def _run_json_user_script() -> str:
    return "\n".join(
        [
            *_cmd_preamble(),
            'call "%ROOT%RUN_JSON.cmd" %*',
            'set "RC=%ERRORLEVEL%"',
            "pause",
            'exit /b %RC%',
            "",
        ]
    )


def _open_results_script() -> str:
    return "\n".join(
        [
            *_cmd_preamble(),
            'set "RESULTS_PATH=%ROOT%output"',
            'if not "%~1"=="" set "RESULTS_PATH=%~f1"',
            'if not exist "%RESULTS_PATH%" (',
            "  echo ОШИБКА: каталог результатов не найден: %RESULTS_PATH%",
            "  exit /b 2",
            ")",
            'start "" explorer.exe "%RESULTS_PATH%"',
            "exit /b 0",
            "",
        ]
    )


def _validate_pure_python_wheel(wheel_path: Path) -> tuple[str, ...]:
    errors: list[str] = []
    if not wheel_path.exists() or not wheel_path.is_file():
        return (f"wheel file does not exist: {wheel_path}",)
    if wheel_path.suffix.lower() != ".whl":
        return (f"wheel_path must have .whl suffix: {wheel_path}",)
    if not re.search(r"-none-any\.whl$", wheel_path.name, flags=re.IGNORECASE):
        errors.append("only a pure-Python *-none-any.whl project wheel may be bundled")
    if not zipfile.is_zipfile(wheel_path):
        errors.append(f"wheel file is not a valid ZIP archive: {wheel_path}")
        return tuple(errors)

    with zipfile.ZipFile(wheel_path) as archive:
        names = archive.namelist()
        wheel_metadata_names = [name for name in names if name.endswith(".dist-info/WHEEL")]
        if len(wheel_metadata_names) != 1:
            errors.append("wheel archive must contain exactly one .dist-info/WHEEL file")
        for name in names:
            normalized = name.rstrip("/")
            if not normalized:
                continue
            if _unsafe_archive_member(normalized):
                errors.append(f"unsafe wheel archive member: {name}")
            if Path(normalized).suffix.lower() in FORBIDDEN_BINARY_SUFFIXES:
                errors.append(f"native or executable wheel member is forbidden: {name}")
        if len(wheel_metadata_names) == 1:
            metadata = archive.read(wheel_metadata_names[0]).decode("utf-8", errors="replace")
            if "Root-Is-Purelib: true" not in metadata:
                errors.append("wheel metadata must declare Root-Is-Purelib: true")
    return tuple(dict.fromkeys(errors))


def _unsafe_archive_member(name: str) -> bool:
    if "\\" in name or name.startswith(("/", "~")):
        return True
    if re.match(r"^[A-Za-z]:", name):
        return True
    path = PurePosixPath(name)
    return path.is_absolute() or ".." in path.parts


def _build_manifest(
    *,
    output_dir: Path,
    payload_files: tuple[Path, ...],
    status: str,
    distribution_mode: str,
    wheel_filename: str | None,
    wheel_sha256: str | None,
    warnings: tuple[str, ...],
    errors: tuple[str, ...],
) -> dict[str, Any]:
    files = [
        {
            "relative_path": path.relative_to(output_dir).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in sorted(payload_files)
        if path.is_file()
    ]
    return {
        "report_type": "standalone_windows_package_manifest",
        "package_format_version": PACKAGE_FORMAT_VERSION,
        "status": status,
        "package_status": status,
        "distribution_mode": distribution_mode,
        "wheel_included": wheel_filename is not None,
        "wheel_filename": wheel_filename,
        "wheel_sha256": wheel_sha256,
        "element_type": "rectangular_beam",
        "load_duration": "short",
        "file_count": len(files),
        "files": files,
        "warnings": list(warnings),
        "errors": list(errors),
        "project_use": False,
        "project_use_status": "prohibited",
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "ml_included": False,
        "external_solver_required": False,
        "native_binaries_included": False,
    }


def _render_package_readme(distribution_mode: str) -> str:
    if distribution_mode == "wheel":
        start_lines = [
            "1. Для простой автоматической установки дважды щёлкните",
            "   `01_START_HERE.cmd`. Команды вводить не требуется: окно останется",
            "   открытым, а при ошибке рядом будет сохранён текстовый журнал.",
        ]
    else:
        start_lines = [
            "1. Это исходный пакет для разработчика: готовый wheel не включён,",
            "   поэтому `01_START_HERE.cmd` намеренно остановится без установки.",
            "   Пользовательский однокнопочный маршрут доступен только в wheel-ZIP.",
        ]
    return "\n".join(
        [
            "# Автономная исследовательская версия для Windows",
            "",
            PACKAGE_WARNING,
            "Это сетевой пакет для рецензирования, а не офлайн- или самодостаточный",
            "дистрибутив: при первой установке обязательно подключение к интернету.",
            "",
            f"distribution_mode: `{distribution_mode}`",
            "element_type: `rectangular_beam`",
            "load_duration: `short`",
            "project_use: `false`",
            "requires_engineer_review: `true`",
            "ml_included: `false`",
            "external_solver_required: `false`",
            "",
            "## Начало работы",
            "",
            *start_lines,
            "2. Расширенная инструкция находится в `docs/WINDOWS_INSTALL.md`.",
            "3. После установки `RUN_INTERACTIVE.cmd` открывает ручной ввод, а",
            "   `RUN_JSON_USER.cmd` повторяет пример. `RUN_JSON.cmd` предназначен",
            "   только для автоматизации/CI.",
            "4. После расчёта сначала откройте верхнеуровневый `standalone_index.html`",
            "   в каталоге результата. `OPEN_RESULTS.cmd` лишь открывает папку.",
            "5. Заполните `docs/USER_ACCEPTANCE_CHECKLIST.md`.",
            "",
            "Пакет не содержит самостоятельного EXE-файла, веб-сервера, расчётных",
            "формул вне sp63_core или внешней расчётной системы.",
            "Статус `pass` отдельной технической проверки не означает общий допуск,",
            "инженерное утверждение или разрешение проектного применения.",
        ]
    ) + "\n"


def _render_scope() -> str:
    return "\n".join(
        [
            "# Область автономной версии",
            "",
            "Пакет ограничен одной непредварительно напряжённой прямоугольной балкой",
            "с ручным вводом геометрии, классов материалов, момента и поперечной силы.",
            "`cover_mm` — программное расстояние от грани бетона до наружной поверхности",
            "хомута; его нормативная интерпретация остаётся на инженерной проверке.",
            "`moment_kNm` — неотрицательный модуль; его знак не выбирает грань.",
            "`tension_face` явно задаётся как `local_y_min` или `local_y_max`.",
            "Физическое сопоставление локальных осей и граней пока не утверждено и",
            "требует инженерной проверки. Поддерживается только кратковременный маршрут.",
            "Детерминированный публичный процесс остаётся основным и может вернуть",
            "`outside_applicability`.",
            "",
            "Версия не рассчитывает здание и сочетания нагрузок, плиты или колонны,",
            "не выполняет длительные проверки и не разрешает трактовать выдаваемые числа",
            "как утверждённую изгибную несущую способность или проектное решение,",
            "не использует ML и не выполняет автоматическое утверждение или принятие",
            "проектного решения. Существующий подбор арматуры может сформировать только",
            "диагностическое непроектное предложение, обязательное к инженерной проверке.",
            "Внешняя расчётная система для запуска не требуется.",
            "Статус `pass` отдельной проверки не означает общий или инженерный допуск.",
            "",
            "project_use = false",
            "requires_engineer_review = true",
        ]
    ) + "\n"


def _render_windows_install(distribution_mode: str) -> str:
    if distribution_mode == "wheel":
        route_lines = [
            "3. Дважды щёлкните `01_START_HERE.cmd`. Он сам выполнит установку,",
            "   запустит контрольный пример, откроет итоговую страницу и оставит",
            "   окно с результатом. Вводить команды не требуется.",
            "4. При ошибке после начала установки рядом будет создан",
            "   `INSTALLATION_LOG.txt` либо `EXAMPLE_RUN_LOG.txt`.",
            "   Журнал может содержать локальные пути: не публикуйте его целиком,",
            "   если достаточно снимка последних строк ошибки.",
        ]
    else:
        route_lines = [
            "3. Этот исходный пакет не является пользовательским дистрибутивом:",
            "   wheel отсутствует, а `01_START_HERE.cmd` намеренно остановится.",
            "4. Разработчик может выполнить",
            "   `INSTALL_FROM_SOURCE.cmd C:\\path\\to\\GBK`; пользователю следует",
            "   передавать только отдельно проверенный wheel-ZIP.",
        ]
    return "\n".join(
        [
            "# Установка в Windows",
            "",
            "Пакет предназначен для сетевого рецензирования. Он не является офлайн-",
            "или самодостаточным дистрибутивом.",
            "При первой установке обязательно подключение к интернету для загрузки",
            "фиксированных зависимостей Python 3.11.",
            "",
            "1. Установите 64-разрядный Python 3.11 с Python Launcher (`py`).",
            "2. Распакуйте пакет в локальный каталог с правом записи.",
            *route_lines,
            "5. Для исходного проекта предназначен только разработческий маршрут.",
            "6. Внутренний установщик сверит SHA-256 включённого wheel и установит",
            "   зависимости из",
            "   `requirements/runtime-py311.lock`, затем wheel с `--no-deps`.",
            "7. Установка создаст `.venv` рядом с командными скриптами.",
            "8. После первого запуска пользователь может отдельно запускать",
            "   `RUN_JSON_USER.cmd` или `RUN_INTERACTIVE.cmd`.",
            "   Неблокирующий `RUN_JSON.cmd` предназначен для автоматизации и CI.",
            "",
            "`VERIFY_PACKAGE.cmd` перед установкой проверяет SHA-256 манифеста, размеры",
            "и SHA-256 всех записанных файлов. Это контроль целостности от случайного",
            "изменения или повреждения, но не криптографическое подтверждение подлинности.",
            "Доверие к источнику архива и репозиторию GitHub проверяется отдельно.",
            "Версии lock сняты 2026-07-18 с нейтрального тестового профиля проекта;",
            "их допуск для архива подтверждает только успешная блокирующая проверка",
            "`standalone-windows` в чистом Windows/Python 3.11 окружении.",
            "",
            "## Поля входного JSON",
            "",
            *_json_input_table_lines(),
            "",
            "Классы и диаметры в таблице — текущий программный каталог, а не новое",
            "нормативное утверждение; свойства материалов требуют инженерной проверки.",
            "Числа в `input/beam_example.json` — только демонстрационные исходные данные,",
            "не коэффициенты, нормативные значения или рекомендации по проектированию.",
            "Физическое сопоставление `local_y_min`/`local_y_max` с реальным элементом",
            "не утверждено и требует инженерной проверки.",
            "",
            "## Каталоги результата",
            "",
            "Для каждого отдельного расчёта задавайте отдельный каталог результата.",
            "Каталог, принятый standalone-модулем, управляется программой: не помещайте",
            "в него произвольные пользовательские файлы. Повторный запуск может удалить",
            "из него известные служебные артефакты предыдущего запуска.",
            "После расчёта главным пользовательским входом служит верхнеуровневый",
            "`standalone_index.html`; не начинайте просмотр с raw `workflow/index.html`.",
            "`OPEN_RESULTS.cmd` только открывает папку и не выбирает правильный отчёт.",
            "",
            "## Передача инженеру",
            "",
            "Передавайте только верхнеуровневый `standalone_review_bundle.zip`, который",
            "санитизирован и проверен программой. Не передавайте весь каталог `output`",
            "или внутренний `workflow/deterministic_report.zip`: они предназначены только",
            "для локальной работы и могут содержать абсолютные пути компьютера автора.",
            "Для пакетной приёмки поле `standalone_review_metadata.json`",
            "`.code_identity.code_identity_status` должно быть",
            "`recorded_from_launcher_requires_manifest_match`, а",
            "`.code_identity.build_id=wheel-sha256:<sha256>` должно совпадать с",
            "`wheel_sha256` в доверенном",
            "`standalone_manifest.json`. Маркер сам по себе не подтверждает подлинность.",
            "Для `source-unverified` статус равен `unavailable_open_question`; такой",
            "результат не передаётся как испытание собранного пакета.",
            "",
            "Статус `pass` отдельной технической проверки не означает общий результат,",
            "инженерный допуск или разрешение проектного применения.",
            "Права администратора и внешняя расчётная программа не требуются.",
            "Не добавляйте сформированный каталог `.venv` в Git.",
        ]
    ) + "\n"


def _render_acceptance_checklist(distribution_mode: str) -> str:
    if distribution_mode == "wheel":
        one_click_lines = [
            "- [ ] `01_START_HERE.cmd` выполнил установку и контрольный пример без",
            "      ручного ввода команд, сохранил окно и открыл итоговую страницу.",
            "- [ ] При ошибке после начала установки создан `INSTALLATION_LOG.txt`",
            "      либо `EXAMPLE_RUN_LOG.txt`; разработчику передаётся только снимок",
            "      необходимых последних строк.",
        ]
    else:
        one_click_lines = [
            "- [ ] Зафиксировано, что исходный пакет не предназначен для",
            "      пользовательской однокнопочной приёмки без готового wheel.",
        ]
    return "\n".join(
        [
            "# Контрольный лист пользовательской приёмки",
            "",
            *one_click_lines,
            "- [ ] Установка завершилась без ошибки.",
            "- [ ] Интерактивный режим явно указывает прямоугольную балку.",
            "- [ ] `RUN_JSON_USER.cmd` сохраняет окно после выполнения; `RUN_JSON.cmd`",
            "      остаётся неблокирующим маршрутом автоматизации.",
            "- [ ] Включённый JSON формирует отдельный управляемый каталог отчёта.",
            "- [ ] В каталог результата не помещены произвольные пользовательские файлы.",
            "- [ ] Первым открыт верхнеуровневый `standalone_index.html`, а не",
            "      `workflow/index.html`; `OPEN_RESULTS.cmd` используется лишь для папки.",
            "- [ ] В `case_id` нет ФИО, email, подписей или локальных путей.",
            "- [ ] `b_mm`, `h_mm`, `cover_mm` и `stirrup_diameter_mm` конечны и строго",
            "      больше нуля; `cover_mm < h_mm`; диаметр хомута равен 6, 8, 10 или 12 мм.",
            "- [ ] `moment_kNm` и `shear_kN` конечны и неотрицательны; ноль допустим.",
            "- [ ] `cover_mm` понимается как программное расстояние от грани бетона до",
            "      наружной поверхности хомута, ожидающее инженерного подтверждения.",
            "- [ ] `moment_kNm` — неотрицательный модуль, знак которого не выбирает грань.",
            "- [ ] `tension_face` явно задан как `local_y_min` либо `local_y_max`.",
            "- [ ] Физическое сопоставление осей и граней не считается утверждённым.",
            "- [ ] Неподдерживаемые данные отклоняются без публикации несущей способности.",
            "- [ ] Результат содержит `project_use = false`.",
            "- [ ] Результат содержит `requires_engineer_review = true`.",
            "- [ ] ML-результат отсутствует.",
            "- [ ] Внешняя расчётная система при запуске не запрашивается.",
            "- [ ] Отчёты остаются локальными и не считаются утверждением проекта.",
            "- [ ] Инженеру передаётся только `standalone_review_bundle.zip`, а не весь",
            "      каталог результата или внутренний `workflow/deterministic_report.zip`.",
            "- [ ] `standalone_review_metadata.json.code_identity.code_identity_status` равен",
            "      `recorded_from_launcher_requires_manifest_match`.",
            "- [ ] SHA-256 в `.code_identity.build_id=wheel-sha256:<sha256>` совпадает",
            "      с `wheel_sha256` из `standalone_manifest.json`.",
            "- [ ] Для `source-unverified` статус равен `unavailable_open_question`, и",
            "      результат не передаётся как пакетное испытание.",
            "- [ ] `pass` отдельной проверки не трактуется как общий или инженерный допуск.",
            "",
            "Решение: ACCEPT_FOR_RESEARCH_TRIAL / ACCEPT_WITH_COMMENTS / REJECT",
        ]
    ) + "\n"


def _json_input_table_lines() -> list[str]:
    return [
        "| Поле | Единица | Точное программное значение | Допустимое значение |",
        "|---|---:|---|---|",
        "| `case_id` | — | Технический идентификатор расчёта; не включать ФИО, email, "
        "подписи или локальные пути | Непустая после обрезки строка, не более 100 "
        "символов, без управляющих символов |",
        "| `b_mm` | мм | Ширина прямоугольного сечения | Конечное число `> 0` |",
        "| `h_mm` | мм | Высота прямоугольного сечения | Конечное число `> 0` |",
        "| `cover_mm` | мм | Расстояние от грани бетона до наружной поверхности "
        "хомута; нормативная интерпретация не утверждена | Конечное число `> 0` и `< h_mm` |",
        "| `stirrup_diameter_mm` | мм | Диаметр хомута, используемый в геометрии | "
        "Одно из: `6`, `8`, `10`, `12` |",
        "| `concrete_class` | — | Класс бетона текущего ULS-каталога | "
        "`B15`, `B20`, `B25`, `B30`, `B35`, `B40` |",
        "| `longitudinal_rebar_class` | — | Класс продольной арматуры текущего "
        "ULS-каталога | `A400`, `A500` |",
        "| `stirrup_rebar_class` | — | Класс поперечной арматуры текущего каталога | "
        "`A240`, `A400`, `A500` |",
        "| `moment_kNm` | кН·м | Неотрицательный модуль изгибающего момента; "
        "знак не выбирает грань | Конечное число `>= 0` |",
        "| `shear_kN` | кН | Неотрицательный модуль поперечной силы | "
        "Конечное число `>= 0` |",
        "| `tension_face` | — | Явно выбранная растянутая грань в локальной "
        "системе | `local_y_min` или `local_y_max` |",
        "| `element_type` (необязательное) | — | Фиксирует область элемента | Только "
        "`rectangular_beam`; при отсутствии используется оно же |",
        "| `load_duration` (необязательное) | — | Фиксирует маршрут длительности | Только "
        "`short`; при отсутствии используется оно же |",
    ]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
