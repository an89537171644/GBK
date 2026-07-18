import hashlib
import json
import re
import zipfile
from pathlib import Path

from sp63_core.report.ed01_contract import public_report_contract_errors
from sp63_core.standalone import StandaloneBeamInput, run_standalone_beam_case
from sp63_core.standalone import controller as standalone_controller


def beam_input() -> StandaloneBeamInput:
    return StandaloneBeamInput(
        case_id="public-contract-001",
        b_mm=300,
        h_mm=500,
        cover_mm=32,
        stirrup_diameter_mm=8,
        concrete_class="B25",
        longitudinal_rebar_class="A500",
        stirrup_rebar_class="A240",
        moment_kNm=150,
        shear_kN=80,
        tension_face="local_y_min",
    )


def _diagnostic_paths(value, path="report"):
    paths = []
    if isinstance(value, dict):
        for key, nested in value.items():
            child = f"{path}.{key}"
            if isinstance(key, str) and key.startswith("diagnostic_"):
                paths.append(child)
            paths.extend(_diagnostic_paths(nested, child))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(_diagnostic_paths(nested, f"{path}[{index}]"))
    return paths


def test_standalone_report_obeys_public_ed01_contract(tmp_path):
    result = run_standalone_beam_case(beam_input(), tmp_path)

    assert result.report_dir is not None
    payload = json.loads(
        (Path(result.report_dir) / "report.json").read_text(encoding="utf-8")
    )
    assert public_report_contract_errors(payload) == ()
    assert _diagnostic_paths(payload) == []
    assert payload["project_use"] is False
    assert payload["status_scope"] == "public"
    bending = payload["checks"]["bending"]
    assert bending["status"] == "outside_applicability"
    assert bending["Mult"] is None
    assert bending["utilization"] is None
    assert bending["capacity_publication_allowed"] is False


def test_review_bundle_contains_traceable_inputs_status_and_verified_hashes(
    tmp_path,
    monkeypatch,
):
    wheel_digest = "a" * 64
    monkeypatch.setenv("GBK_BUILD_ID", f"wheel-sha256:{wheel_digest.upper()}")
    result = run_standalone_beam_case(beam_input(), tmp_path)

    assert result.report_zip_path is not None
    with zipfile.ZipFile(result.report_zip_path, "r") as archive:
        required_payloads = {
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
            "deterministic_report/report.html",
        }
        assert required_payloads <= set(archive.namelist())
        assert "standalone_latest_status.json" not in archive.namelist()
        assert not any(name.endswith(".zip") for name in archive.namelist())
        bundle_index = archive.read("index.html").decode("utf-8")
        bundle_hrefs = re.findall(r'href="([^"]+)"', bundle_index)
        assert bundle_hrefs
        assert all(href in archive.namelist() for href in bundle_hrefs)
        assert "standalone_review_bundle.zip" not in bundle_index
        assert "workflow/index.html" not in bundle_index
        manifest_bytes = archive.read("standalone_review_manifest.json")
        manifest = json.loads(manifest_bytes)
        assert manifest["path_scope"] == "bundle_relative"
        records = {record["path"]: record for record in manifest["files"]}
        assert set(records) == required_payloads
        for path, record in records.items():
            data = archive.read(path)
            assert record["sha256"] == hashlib.sha256(data).hexdigest()
            assert record["size_bytes"] == len(data)

        sidecar = archive.read("standalone_review_manifest.sha256").decode("utf-8")
        assert sidecar == (
            f"{hashlib.sha256(manifest_bytes).hexdigest()}  "
            "standalone_review_manifest.json\n"
        )
        metadata = json.loads(archive.read("standalone_review_metadata.json"))
        assert metadata["path_scope"] == "bundle_relative"
        assert metadata["code_identity"] == {
            "package_name": "sp63_core",
            "package_version": "0.1.0",
            "build_id": f"wheel-sha256:{wheel_digest}",
            "code_identity_status": (
                "recorded_from_launcher_requires_manifest_match"
            ),
            "requires_engineer_review": True,
        }
        assert metadata["scope"]["reinforcement_selection_status"] == "diagnostic_only"
        assert metadata["units_layer"]["classification"] == (
            "programmatic_input_unit_conversion"
        )
        assert metadata["units_layer"]["normative_formula_asserted"] is False
        conversions = {
            (item["source_unit"], item["target_unit"], item["implementation"])
            for item in metadata["units_layer"]["conversions"]
        }
        assert conversions == {
            ("kN*m", "N*mm", "sp63_core.units.kNm_to_Nmm"),
            ("kN", "N", "sp63_core.units.kN_to_N"),
        }
        assert metadata["input_semantics"] == {
            "cover_reference": "concrete_face_to_outer_stirrup_surface",
            "moment_value_semantics": "non_negative_magnitude",
            "shear_value_semantics": "non_negative_magnitude",
            "tension_face_allowed": ["local_y_min", "local_y_max"],
            "physical_axis_mapping_status": "requires_engineer_review/open_question",
        }
        bundle_status = json.loads(archive.read("standalone_bundle_status.json"))
        assert bundle_status["path_scope"] == "bundle_relative"
        assert bundle_status["project_use"] is False
        assert bundle_status["requires_engineer_review"] is True
        assert all(not Path(path).is_absolute() for path in bundle_status["paths"].values())

        forbidden_fragments = (
            str(tmp_path).encode(),
            str(Path.cwd()).encode(),
            b"/tmp/",
            b"/workspace/",
            b"C:\\Users\\",
        )
        for name in archive.namelist():
            payload = archive.read(name)
            assert all(fragment not in payload for fragment in forbidden_fragments), name


def test_controller_fails_closed_when_public_contract_checker_reports_error(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        standalone_controller,
        "public_report_contract_errors",
        lambda _payload: ("forced public-contract violation",),
    )

    result = run_standalone_beam_case(beam_input(), tmp_path)

    assert result.status == "fail"
    assert result.project_use is False
    assert result.report_dir is None
    assert result.report_index_path is None
    assert result.report_zip_path is None
    assert result.deterministic_report_zip_path is None
    assert any("forced public-contract violation" in error for error in result.errors)
    assert not (tmp_path / "workflow").exists()
    assert not (tmp_path / "standalone_review_bundle.zip").exists()
    latest_status = json.loads(
        (tmp_path / "standalone_latest_status.json").read_text(encoding="utf-8")
    )
    assert latest_status["status"] == "fail"
    assert latest_status["report_dir"] is None
    assert latest_status["report_index_path"] is None
    assert latest_status["report_zip_path"] is None


def test_review_metadata_marks_missing_build_identity_as_open_question(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("GBK_BUILD_ID", raising=False)

    result = run_standalone_beam_case(beam_input(), tmp_path)

    assert result.report_zip_path is not None
    with zipfile.ZipFile(result.report_zip_path) as archive:
        metadata = json.loads(archive.read("standalone_review_metadata.json"))
    assert metadata["code_identity"]["build_id"] is None
    assert metadata["code_identity"]["code_identity_status"] == (
        "unavailable_open_question"
    )
    assert metadata["code_identity"]["requires_engineer_review"] is True


def test_review_metadata_ignores_invalid_build_identity_without_copying_it(
    tmp_path,
    monkeypatch,
):
    unsafe_identity = r"C:\Users\producer\private-wheel"
    monkeypatch.setenv("GBK_BUILD_ID", unsafe_identity)

    result = run_standalone_beam_case(beam_input(), tmp_path)

    assert result.report_zip_path is not None
    with zipfile.ZipFile(result.report_zip_path) as archive:
        metadata_bytes = archive.read("standalone_review_metadata.json")
        metadata = json.loads(metadata_bytes)
    assert metadata["code_identity"]["build_id"] is None
    assert metadata["code_identity"]["code_identity_status"] == "invalid_ignored"
    assert unsafe_identity.encode() not in metadata_bytes


def test_review_bundle_privacy_guard_fails_closed_on_producer_path(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        standalone_controller,
        "_bundle_readme",
        lambda _result: r"producer path C:\Users\private\GBK",
    )

    result = run_standalone_beam_case(beam_input(), tmp_path)

    assert result.status == "fail"
    assert result.report_dir is None
    assert result.report_index_path is None
    assert result.report_zip_path is None
    assert result.deterministic_report_zip_path is None
    assert any("privacy guard" in error for error in result.errors)
    assert not (tmp_path / "standalone_review_bundle.zip").exists()
    assert not (tmp_path / "workflow").exists()
