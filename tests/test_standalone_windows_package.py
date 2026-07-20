import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath

import pytest

from sp63_core.standalone.package import (
    FORBIDDEN_BINARY_SUFFIXES,
    RUNTIME_LOCK_RELATIVE_PATH,
    build_standalone_windows_package,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_pure_wheel(path: Path, *, unsafe_member: str | None = None) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("sp63_core/standalone/__init__.py", "")
        archive.writestr(
            "sp63_rc_ai-0.1.0.dist-info/WHEEL",
            "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        )
        if unsafe_member:
            archive.writestr(unsafe_member, "unsafe")
    return path


def test_source_package_generates_beam_only_windows_skeleton(tmp_path):
    result = build_standalone_windows_package(tmp_path)

    assert result.status == "pass"
    assert result.package_status == "pass"
    assert result.distribution_mode == "source"
    assert result.wheel_included is False
    assert result.element_type == "rectangular_beam"
    assert result.load_duration == "short"
    assert result.project_use is False
    assert result.requires_engineer_review is True
    assert result.ml_included is False
    assert result.external_solver_required is False
    assert result.script_count == 13
    for relative_path in (
        "01_START_HERE.cmd",
        "ONE_CLICK_GUARD.ps1",
        "ONE_CLICK_WORKER.cmd",
        "VERIFY_ONE_CLICK_RESULT.ps1",
        "VERIFY_PACKAGE.ps1",
        "VERIFY_PACKAGE.cmd",
        "INSTALL_FROM_WHEEL.cmd",
        "INSTALL_FROM_SOURCE.cmd",
        "02_OPEN_GBK.cmd",
        "RUN_INTERACTIVE.cmd",
        "RUN_JSON.cmd",
        "RUN_JSON_USER.cmd",
        "OPEN_RESULTS.cmd",
        RUNTIME_LOCK_RELATIVE_PATH,
        "input/beam_example.json",
        "README_STANDALONE_WINDOWS.md",
        "docs/SCOPE.md",
        "docs/WINDOWS_INSTALL.md",
        "docs/ENGINEER_GUI.md",
        "docs/USER_ACCEPTANCE_CHECKLIST.md",
        "standalone_manifest.json",
        "standalone_manifest.sha256",
    ):
        assert (tmp_path / relative_path).is_file()


def test_command_scripts_are_location_safe_and_use_standalone_cli(tmp_path):
    build_standalone_windows_package(tmp_path)
    scripts = tuple(tmp_path.glob("*.cmd"))
    combined = "\n".join(path.read_text(encoding="utf-8") for path in scripts)
    combined_lower = combined.lower()

    assert scripts
    assert all("%~dp0" in path.read_text(encoding="utf-8") for path in scripts)
    assert ".venv\\Scripts\\python.exe" in combined
    assert "-m sp63_core.standalone" in combined
    assert "--input-json" in combined
    assert "--output-dir" in combined
    assert "--json" in combined
    assert "scad" not in combined_lower
    assert "lira" not in combined_lower

    powershell_scripts = tuple(tmp_path.glob("*.ps1"))
    assert powershell_scripts
    assert all(path.read_bytes().startswith(b"\xef\xbb\xbf") for path in powershell_scripts)


def test_user_launchers_pause_but_automation_json_launcher_does_not(tmp_path):
    build_standalone_windows_package(tmp_path)

    interactive = (tmp_path / "RUN_INTERACTIVE.cmd").read_text(encoding="utf-8")
    user_json = (tmp_path / "RUN_JSON_USER.cmd").read_text(encoding="utf-8")
    automation_json = (tmp_path / "RUN_JSON.cmd").read_text(encoding="utf-8")
    start_here = (tmp_path / "01_START_HERE.cmd").read_text(encoding="utf-8")

    assert "pause" in interactive.casefold()
    assert "pause" in user_json.casefold()
    assert "RUN_JSON.cmd" in user_json
    assert "%*" in user_json
    assert "pause" not in automation_json.casefold()
    assert "pause" in start_here.casefold()


def test_engineer_gui_launcher_is_location_safe_verified_and_headless_testable(tmp_path):
    wheel = _write_pure_wheel(tmp_path / "sp63_rc_ai-0.1.0-py3-none-any.whl")
    output_dir = tmp_path / "package"
    result = build_standalone_windows_package(output_dir, wheel)

    launcher = (output_dir / "02_OPEN_GBK.cmd").read_text(encoding="utf-8")
    manifest = json.loads((output_dir / "standalone_manifest.json").read_text("utf-8"))
    manifest_paths = {record["relative_path"] for record in manifest["files"]}

    assert "%~dp0" in launcher
    assert "VERIFY_PACKAGE.cmd" in launcher
    assert launcher.index("VERIFY_PACKAGE.cmd") < launcher.index("APP_PYTHON=")
    assert ".gbk_build_id" in launcher
    assert 'set /p "GBK_BUILD_ID="' in launcher
    assert ".venv\\Scripts\\pythonw.exe" in launcher
    assert "-m sp63_core.standalone.gui" in launcher
    assert "--headless-smoke" in launcher
    assert "--exercise-run" in launcher
    assert launcher.index(":ci_smoke") < launcher.index("--exercise-run")
    assert "--self-check" not in launcher
    assert "GUI_LAUNCH_LOG.txt" in launcher
    assert "--output-root" in launcher
    assert f"EXPECTED_BUILD_ID=wheel-sha256:{result.wheel_sha256}" in launcher
    assert "$actual -cne $env:EXPECTED_BUILD_ID" in launcher
    assert ":build_identity_failed" in launcher
    assert launcher.index("$actual -cne $env:EXPECTED_BUILD_ID") < launcher.index(
        'start "" "%APP_PYTHONW%"'
    )
    assert 'if "%CI_MODE%"=="1" goto :ci_smoke' in launcher
    assert 'if "%CI_MODE%"=="1" (' not in launcher
    assert 'set "RC=%ERRORLEVEL%"' not in launcher
    assert 'if errorlevel 1 (set "RC=2") else (set "RC=0")' in launcher
    assert "02_OPEN_GBK.cmd" in manifest_paths

    for installer_name in ("INSTALL_FROM_WHEEL.cmd", "INSTALL_FROM_SOURCE.cmd"):
        installer = (output_dir / installer_name).read_text(encoding="utf-8")
        assert "--headless-smoke" in installer
        assert "-m sp63_core.standalone.gui" in installer
        assert "tkinter.Tcl()" not in installer
        assert "installer_gui_smoke" in installer
        assert installer.index("--headless-smoke") < installer.index(
            ".gbk_build_id.tmp"
        )


def test_one_click_launcher_installs_runs_logs_and_opens_engineer_gui(tmp_path):
    wheel = _write_pure_wheel(tmp_path / "sp63_rc_ai-0.1.0-py3-none-any.whl")
    output_dir = tmp_path / "package"
    build_standalone_windows_package(output_dir, wheel)
    launcher = (output_dir / "01_START_HERE.cmd").read_text(encoding="utf-8")
    guard = (output_dir / "ONE_CLICK_GUARD.ps1").read_text(encoding="utf-8")
    worker = (output_dir / "ONE_CLICK_WORKER.cmd").read_text(encoding="utf-8")
    result_verifier = (output_dir / "VERIFY_ONE_CLICK_RESULT.ps1").read_text(
        encoding="utf-8"
    )

    assert worker.index("INSTALL_FROM_WHEEL.cmd") < worker.index("RUN_JSON.cmd")
    assert "INSTALLATION_LOG.txt" in worker
    assert "EXAMPLE_RUN_LOG.txt" in worker
    assert "standalone_index.html" in worker
    assert 'call "%ROOT%02_OPEN_GBK.cmd" --from-install' in worker
    assert 'call "%ROOT%02_OPEN_GBK.cmd" --ci' in worker
    assert worker.index("VERIFY_ONE_CLICK_RESULT.ps1") < worker.index("02_OPEN_GBK.cmd")
    assert 'if /I "%~1"=="--ci"' in launcher
    assert 'if "%CI_MODE%"=="0" if not "%FINAL_RC%"=="0" pause' in launcher
    assert "ONE_CLICK_GUARD.ps1" in launcher
    assert "Threading.Mutex" in guard
    assert "WaitOne(0" in guard
    assert "AbandonedMutexException" in guard
    assert ".gbk_start_lock" not in launcher + guard + worker
    assert "VERIFY_ONE_CLICK_RESULT.ps1" in worker
    assert "project_use=false" in worker
    assert '$status.status -ne "review_required"' in result_verifier
    assert '$status.calculation_status -ne "outside_applicability"' in result_verifier
    assert '$status.evidence_status -ne "needs_engineer_review"' in result_verifier
    assert "standalone_review_manifest.sha256" in result_verifier
    assert "review bundle payload hash mismatch" in result_verifier
    assert "ZipFile]::OpenRead" in result_verifier


def test_source_skeleton_refuses_one_click_without_bundled_wheel(tmp_path):
    build_standalone_windows_package(tmp_path)
    launcher = (tmp_path / "01_START_HERE.cmd").read_text(encoding="utf-8")
    readme = (tmp_path / "README_STANDALONE_WINDOWS.md").read_text(encoding="utf-8")

    assert "исходный пакет разработчика без готового wheel" in launcher
    assert "INSTALL_FROM_WHEEL.cmd" not in launcher
    assert "намеренно остановится без установки" in readme
    assert "wheel-ZIP" in readme


def test_manifest_hashes_every_payload_file_and_has_own_sha256(tmp_path):
    result = build_standalone_windows_package(tmp_path)
    manifest_path = Path(result.manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["report_type"] == "standalone_windows_package_manifest"
    assert manifest["package_format_version"] == "1.2"
    assert manifest["status"] == "pass"
    assert manifest["element_type"] == "rectangular_beam"
    assert manifest["project_use"] is False
    assert manifest["native_binaries_included"] is False
    assert manifest["file_count"] == result.file_count == len(manifest["files"])
    recorded_paths = {item["relative_path"] for item in manifest["files"]}
    actual_payload_paths = {
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*")
        if path.is_file()
    } - {"standalone_manifest.json", "standalone_manifest.sha256"}
    assert recorded_paths == actual_payload_paths
    for file_info in manifest["files"]:
        relative = PurePosixPath(file_info["relative_path"])
        assert not relative.is_absolute()
        assert ".." not in relative.parts
        path = tmp_path / relative
        assert path.is_file()
        assert file_info["sha256"] == _sha256(path)
        assert file_info["size_bytes"] == path.stat().st_size

    sidecar = Path(result.manifest_sha256_path).read_text(encoding="utf-8").split()
    assert sidecar == [_sha256(manifest_path), manifest_path.name]


def test_valid_pure_python_wheel_is_copied_and_recorded(tmp_path):
    wheel = _write_pure_wheel(tmp_path / "sp63_rc_ai-0.1.0-py3-none-any.whl")
    output_dir = tmp_path / "package"

    result = build_standalone_windows_package(output_dir, wheel)
    bundled = output_dir / "wheel" / wheel.name
    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))

    assert result.status == "pass"
    assert result.distribution_mode == "wheel"
    assert result.wheel_included is True
    assert result.wheel_filename == wheel.name
    assert result.wheel_sha256 == _sha256(wheel) == _sha256(bundled)
    assert manifest["wheel_sha256"] == result.wheel_sha256
    install_script = (output_dir / "INSTALL_FROM_WHEEL.cmd").read_text(encoding="utf-8")
    assert f"wheel\\{wheel.name}" in install_script
    assert "Get-FileHash" in install_script
    assert result.wheel_sha256 in install_script
    assert install_script.index("Get-FileHash") < install_script.index("pip install")
    assert "requirements\\runtime-py311.lock" in install_script
    assert "pip install --no-deps" in install_script
    install_doc = (output_dir / "docs" / "WINDOWS_INSTALL.md").read_text(
        encoding="utf-8"
    )
    checklist = (output_dir / "docs" / "USER_ACCEPTANCE_CHECKLIST.md").read_text(
        encoding="utf-8"
    )
    gui_guide = (output_dir / "docs" / "ENGINEER_GUI.md").read_text(encoding="utf-8")
    assert "сам выполнит установку" in install_doc
    assert "`INSTALLATION_LOG.txt`" in install_doc
    assert "ручного ввода команд" in checklist
    assert "`02_OPEN_GBK.cmd`" in gui_guide
    assert "не содержит расчётных формул" in gui_guide
    for launcher_name in ("RUN_INTERACTIVE.cmd", "RUN_JSON.cmd"):
        launcher = (output_dir / launcher_name).read_text(encoding="utf-8")
        assert ".gbk_build_id" in launcher
        assert result.wheel_sha256 not in launcher


def test_source_launchers_mark_build_identity_as_unverified(tmp_path):
    build_standalone_windows_package(tmp_path)

    source_installer = (tmp_path / "INSTALL_FROM_SOURCE.cmd").read_text(encoding="utf-8")
    wheel_installer = (tmp_path / "INSTALL_FROM_WHEEL.cmd").read_text(encoding="utf-8")
    gui_launcher = (tmp_path / "02_OPEN_GBK.cmd").read_text(encoding="utf-8")
    assert "echo source-unverified" in source_installer
    assert "EXPECTED_BUILD_ID=wheel-sha256:WHEEL_SHA256_NOT_AVAILABLE" in wheel_installer
    assert "echo %EXPECTED_BUILD_ID%" in wheel_installer
    assert "EXPECTED_BUILD_ID=source-unverified" in gui_launcher
    for launcher_name in ("RUN_INTERACTIVE.cmd", "RUN_JSON.cmd"):
        launcher = (tmp_path / launcher_name).read_text(encoding="utf-8")
        assert ".gbk_build_id" in launcher
        assert 'set /p "GBK_BUILD_ID="' in launcher
        assert "идентификатор установленной сборки отсутствует" in launcher
        assert "GBK_BUILD_ID=source-unverified" not in launcher
        assert str(tmp_path) not in launcher


def test_verifier_checks_sidecar_and_every_manifest_payload_before_install(tmp_path):
    build_standalone_windows_package(tmp_path)
    verifier = (tmp_path / "VERIFY_PACKAGE.ps1").read_text(encoding="utf-8")
    verifier_cmd = (tmp_path / "VERIFY_PACKAGE.cmd").read_text(encoding="utf-8")
    manifest = json.loads((tmp_path / "standalone_manifest.json").read_text(encoding="utf-8"))
    manifest_paths = {record["relative_path"] for record in manifest["files"]}

    assert "standalone_manifest.sha256" in verifier
    assert "Get-FileHash" in verifier
    assert "$manifest.files" in verifier
    assert "file_count" in verifier
    assert "relative_path" in verifier
    assert "size_bytes" in verifier
    assert "ReparsePoint" in verifier
    assert "unsafe component" in verifier
    assert '-File "%ROOT%VERIFY_PACKAGE.ps1"' in verifier_cmd
    assert '-PackageRoot "%ROOT%"' not in verifier_cmd
    assert "VERIFY_PACKAGE.ps1" in manifest_paths
    assert "VERIFY_PACKAGE.cmd" in manifest_paths
    assert "VERIFY_ONE_CLICK_RESULT.ps1" in manifest_paths
    assert "ONE_CLICK_GUARD.ps1" in manifest_paths
    assert "ONE_CLICK_WORKER.cmd" in manifest_paths
    assert ".gbk_build_id" not in manifest_paths
    assert "VERIFY_PACKAGE.ps1" in verifier_cmd

    for installer_name in ("INSTALL_FROM_WHEEL.cmd", "INSTALL_FROM_SOURCE.cmd"):
        installer = (tmp_path / installer_name).read_text(encoding="utf-8")
        assert installer.index("VERIFY_PACKAGE.cmd") < installer.index("py -3.11")
        assert installer.index("VERIFY_PACKAGE.cmd") < installer.index("pip install")


def test_wheel_installer_records_identity_only_after_successful_import(tmp_path):
    wheel = _write_pure_wheel(tmp_path / "sp63_rc_ai-0.1.0-py3-none-any.whl")
    output_dir = tmp_path / "package"
    result = build_standalone_windows_package(output_dir, wheel)
    installer = (output_dir / "INSTALL_FROM_WHEEL.cmd").read_text(encoding="utf-8")

    identity = f"wheel-sha256:{result.wheel_sha256}"
    assert identity in installer
    assert installer.index('import sp63_core.standalone') < installer.index(
        "echo %EXPECTED_BUILD_ID%"
    )
    assert ".gbk_build_id.tmp" in installer
    assert (
        'move /y "%NEW_VENV%\\.gbk_build_id.tmp" '
        '"%NEW_VENV%\\.gbk_build_id"' in installer
    )
    assert installer.index('"%NEW_VENV%\\.gbk_build_id"') < installer.index(
        'move "%NEW_VENV%" "%ROOT%.venv"'
    )
    run_json = (output_dir / "RUN_JSON.cmd").read_text(encoding="utf-8")
    assert 'BUILD_ID_PATH=%ROOT%.venv\\.gbk_build_id' in run_json


def test_installers_require_python_311_64_bit_and_stage_private_venv(tmp_path):
    build_standalone_windows_package(tmp_path)

    for installer_name in ("INSTALL_FROM_WHEEL.cmd", "INSTALL_FROM_SOURCE.cmd"):
        installer = (tmp_path / installer_name).read_text(encoding="utf-8")
        assert "struct.calcsize('P') * 8 == 64" in installer
        assert 'set "NEW_VENV=%ROOT%.venv.new"' in installer
        assert 'set "PREVIOUS_VENV=%ROOT%.venv.previous"' in installer
        assert 'py -3.11 -m venv "%NEW_VENV%"' in installer
        assert 'move "%NEW_VENV%" "%ROOT%.venv"' in installer
        assert installer.index('py -3.11 -m venv "%NEW_VENV%"') < installer.index(
            'move "%ROOT%.venv" "%PREVIOUS_VENV%"'
        )
        assert installer.index('move "%ROOT%.venv" "%PREVIOUS_VENV%"') < (
            installer.index('move "%NEW_VENV%" "%ROOT%.venv"')
        )


def test_installers_restore_crash_backup_before_rebuilding(tmp_path):
    wheel = _write_pure_wheel(tmp_path / "sp63_rc_ai-0.1.0-py3-none-any.whl")
    output_dir = tmp_path / "package"
    build_standalone_windows_package(output_dir, wheel)

    for installer_name in ("INSTALL_FROM_WHEEL.cmd", "INSTALL_FROM_SOURCE.cmd"):
        installer = (output_dir / installer_name).read_text(encoding="utf-8")
        restore = 'if not exist "%ROOT%.venv" if exist "%PREVIOUS_VENV%"'
        assert restore in installer
        assert installer.index(restore) < installer.index("where py")
        assert installer.index(restore) < installer.index(
            'rmdir /s /q "%PREVIOUS_VENV%"'
        )
        assert ":activation_failed" in installer
        assert ":restore_failed" in installer
        assert "if errorlevel 1 goto :restore_failed" in installer


def test_runtime_lock_is_fully_pinned_and_recorded_in_manifest(tmp_path):
    result = build_standalone_windows_package(tmp_path)
    lock_path = tmp_path / RUNTIME_LOCK_RELATIVE_PATH
    lock_lines = [
        line
        for line in lock_path.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    ]
    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
    manifest_paths = {item["relative_path"] for item in manifest["files"]}

    assert lock_lines == [
        "annotated-types==0.7.0",
        "joblib==1.5.3",
        "numpy==2.3.5",
        "pandas==2.2.3",
        "pydantic==2.13.4",
        "pydantic-core==2.46.4",
        "python-dateutil==2.9.0.post0",
        "pytz==2026.2",
        "scikit-learn==1.8.0",
        "scipy==1.17.0",
        "six==1.17.0",
        "threadpoolctl==3.6.0",
        "typing-extensions==4.15.0",
        "typing-inspection==0.4.2",
        "tzdata==2026.2",
    ]
    assert all(line.count("==") == 1 for line in lock_lines)
    assert RUNTIME_LOCK_RELATIVE_PATH in manifest_paths
    assert "requirements\\runtime-py311.lock" in (
        tmp_path / "INSTALL_FROM_SOURCE.cmd"
    ).read_text(encoding="utf-8")
    for installer_name in ("INSTALL_FROM_WHEEL.cmd", "INSTALL_FROM_SOURCE.cmd"):
        installer = (tmp_path / installer_name).read_text(encoding="utf-8")
        assert "pip install --no-deps -r" in installer
        assert "pip check" in installer


def test_builder_refuses_nonempty_output_without_touching_existing_files(tmp_path):
    output_dir = tmp_path / "existing"
    output_dir.mkdir()
    sentinel = output_dir / "do-not-overwrite.txt"
    sentinel.write_text("user data", encoding="utf-8")

    with pytest.raises(FileExistsError, match="must be empty"):
        build_standalone_windows_package(output_dir)

    assert sentinel.read_text(encoding="utf-8") == "user data"
    assert not (output_dir / "standalone_manifest.json").exists()


def test_unsafe_or_native_wheel_is_rejected_fail_closed(tmp_path):
    wheel = _write_pure_wheel(
        tmp_path / "sp63_rc_ai-0.1.0-py3-none-any.whl",
        unsafe_member="../escape.dll",
    )
    output_dir = tmp_path / "rejected"

    result = build_standalone_windows_package(output_dir, wheel)

    assert result.status == "fail"
    assert result.wheel_included is False
    assert any("unsafe wheel archive member" in error for error in result.errors)
    assert any("wheel member is forbidden" in error for error in result.errors)
    assert not (output_dir / "wheel" / wheel.name).exists()


def test_generated_package_contains_no_native_or_executable_artifacts(tmp_path):
    result = build_standalone_windows_package(tmp_path)

    forbidden = [
        path
        for path in map(Path, result.generated_files)
        if path.suffix.lower() in FORBIDDEN_BINARY_SUFFIXES
    ]
    assert forbidden == []


def test_bundled_example_uses_standalone_beam_input_contract(tmp_path):
    build_standalone_windows_package(tmp_path)
    payload = json.loads((tmp_path / "input" / "beam_example.json").read_text(encoding="utf-8"))

    assert set(payload) == {
        "case_id",
        "b_mm",
        "h_mm",
        "cover_mm",
        "stirrup_diameter_mm",
        "concrete_class",
        "longitudinal_rebar_class",
        "stirrup_rebar_class",
        "moment_kNm",
        "shear_kN",
        "tension_face",
    }
    assert payload["case_id"] == "beam-demo-001"
    assert "span" not in payload
    assert "element_type" not in payload


def test_generated_docs_define_cover_as_program_input_without_normative_approval(tmp_path):
    build_standalone_windows_package(tmp_path)
    scope = (tmp_path / "docs" / "SCOPE.md").read_text(encoding="utf-8")

    assert "расстояние от грани бетона до наружной поверхности" in scope
    assert "нормативная интерпретация остаётся на инженерной проверке" in scope
    assert "`moment_kNm` — неотрицательный модуль" in scope
    assert "его знак не выбирает грань" in scope
    assert "`shear_kN` — программный неотрицательный модуль |Q|" in scope
    assert "не утверждает нормативную знаковую конвенцию" in scope
    assert "`tension_face` явно задаётся как `local_y_min` или `local_y_max`" in scope
    assert "сопоставление локальных осей и граней пока не утверждено" in scope


def test_generated_install_docs_define_complete_json_contract_and_online_scope(tmp_path):
    build_standalone_windows_package(tmp_path)
    readme = (tmp_path / "README_STANDALONE_WINDOWS.md").read_text(encoding="utf-8")
    install = (tmp_path / "docs" / "WINDOWS_INSTALL.md").read_text(encoding="utf-8")
    gui_guide = (tmp_path / "docs" / "ENGINEER_GUI.md").read_text(encoding="utf-8")

    assert "не офлайн- или самодостаточный" in readme
    assert "обязательно подключение к интернету" in install
    assert "`01_START_HERE.cmd`" in readme
    assert "`01_START_HERE.cmd`" in install
    assert "`02_OPEN_GBK.cmd`" in readme
    assert "`02_OPEN_GBK.cmd`" in install
    assert "local_y_min" in gui_guide
    assert "local_y_max" in gui_guide
    assert "намеренно остановится" in readme
    assert "wheel отсутствует" in install
    checklist = (tmp_path / "docs" / "USER_ACCEPTANCE_CHECKLIST.md").read_text(
        encoding="utf-8"
    )
    assert "не предназначен" in checklist
    for field in (
        "case_id",
        "b_mm",
        "h_mm",
        "cover_mm",
        "stirrup_diameter_mm",
        "concrete_class",
        "longitudinal_rebar_class",
        "stirrup_rebar_class",
        "moment_kNm",
        "shear_kN",
        "tension_face",
        "element_type",
        "load_duration",
    ):
        assert f"`{field}`" in install
    assert "`6`, `8`, `10`, `12`" in install
    assert "только демонстрационные исходные данные" in install
    assert "не коэффициенты" in install
    assert "автоматически создаёт отдельный каталог `run-*`" in install
    assert "не помещайте" in install
    assert "`pass` отдельной технической проверки" in install
    assert "standalone_review_metadata.json" in install
    assert ".code_identity.code_identity_status" in install
    assert ".code_identity.build_id" in install
    assert "recorded_from_launcher_requires_manifest_match" in install
    assert "standalone_index.html" in install
    assert "standalone_review_bundle.zip" in install
    assert "GUI_LAUNCH_LOG.txt" in install
    assert "GUI_LAUNCH_LOG.txt" in checklist
    assert "только диагностическими/CI-маршрутами" in checklist
    assert "после повторной" in checklist
    assert "защитной проверки" in checklist


def test_repository_windows_workflow_is_pr_gated_and_checks_review_bundle():
    workflow = Path(".github/workflows/standalone-windows.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "pull_request:" in workflow
    assert "  push:" not in workflow
    assert "VERIFY_PACKAGE.cmd" in workflow
    assert "standalone_review_bundle.zip" in workflow
    assert "standalone_review_metadata.json" in workflow
    assert "recorded_from_launcher_requires_manifest_match" in workflow
    assert "wheel_sha256" in workflow
    assert "USERPROFILE" in workflow
    assert "tampered lock wheel and documentation" in workflow
    assert '01_START_HERE.cmd" --ci' in workflow
    assert "INSTALLATION_LOG.txt" in workflow
    assert "EXAMPLE_RUN_LOG.txt" in workflow
    assert "standalone-windows-python311-engineer-gui-draft" in workflow
    assert '02_OPEN_GBK.cmd" --ci' in workflow
    assert "Reject stale installed build identity" in workflow
    assert "GUI launcher accepted a stale installed build identity" in workflow
    assert "WriteAllBytes($buildIdPath, $originalBytes)" in workflow
    assert "проверка ЖБК" in workflow
    assert "STANDALONE_USER_PACKAGE" in workflow
    assert 'src/sp63_core/**' in workflow
    assert "timeout-minutes: 45" in workflow
    assert "valid ZIP with tampered payload" in workflow
    assert "PIP_NO_INDEX" in workflow
    assert "Failed staged reinstall damaged the active environment" in workflow
    assert workflow.count('01_START_HERE.cmd" --ci') == 2


def test_generated_user_documents_are_russian(tmp_path):
    build_standalone_windows_package(tmp_path)
    readme = (tmp_path / "README_STANDALONE_WINDOWS.md").read_text(encoding="utf-8")
    install = (tmp_path / "docs" / "WINDOWS_INSTALL.md").read_text(encoding="utf-8")
    gui_guide = (tmp_path / "docs" / "ENGINEER_GUI.md").read_text(encoding="utf-8")
    checklist = (tmp_path / "docs" / "USER_ACCEPTANCE_CHECKLIST.md").read_text(
        encoding="utf-8"
    )

    assert "Автономная исследовательская версия" in readme
    assert "Установка в Windows" in install
    assert "Инженерный интерфейс автономной версии" in gui_guide
    assert "Контрольный лист пользовательской приёмки" in checklist
