import csv
import json

import pytest

from sp63_core.cli import main
from sp63_core.materials import build_material_verification_rows
from sp63_core.validation import ExternalComparisonRow, export_external_comparison_csv


def section_args() -> list[str]:
    return [
        "--b",
        "300",
        "--h",
        "500",
        "--cover",
        "32",
        "--stirrup-diameter",
        "8",
        "--main-bar-diameter",
        "20",
    ]


def orientation_args() -> list[str]:
    return [
        "--local-axes-id",
        "cli-test-local-axes",
        "--moment-axis",
        "local_z",
        "--tension-face",
        "local_y_min",
    ]


def test_cli_bending_command_text_output(capsys):
    exit_code = main(
        [
            "bending",
            *section_args(),
            *orientation_args(),
            "--concrete",
            "B25",
            "--rebar",
            "A500",
            "--as-area",
            "942.48",
            "--moment",
            "150000000",
            "--load-duration",
            "short",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Bending check" in captured.out
    assert "status: pass" in captured.out
    assert "completeness_status: incomplete" in captured.out
    assert "evidence_status: needs_engineer_review" in captured.out
    assert "project_use_status: prohibited" in captured.out
    assert "project_use: false" in captured.out
    assert "requires_engineer_review: true" in captured.out
    assert "material_source_clauses:" in captured.out
    assert "layout_applicability_status: not_checked_area_only" in captured.out
    assert "manual_applicability_confirmation_required: true" in captured.out


def test_cli_bmr_03_json_exposes_resolved_long_term_context(capsys):
    exit_code = main(
        [
            "bending",
            *section_args(),
            *orientation_args(),
            "--concrete",
            "B25",
            "--rebar",
            "A500",
            "--as-area",
            "942.4777960769379",
            "--moment",
            "164000000",
            "--load-duration",
            "long",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["status"] == "fail"
    assert payload["result"]["Rb_base"] == 14.5
    assert payload["result"]["gamma_b1"] == 0.9
    assert payload["result"]["Rb_effective"] == 13.05
    assert payload["result"]["Mult"] == pytest.approx(163_023_639.01)
    assert payload["result"]["project_use"] is False
    assert payload["result"]["requires_engineer_review"] is True


def test_cli_bmr_05_omits_capacity_outside_applicability(capsys):
    exit_code = main(
        [
            "bending",
            "--b",
            "300",
            "--h",
            "500",
            "--cover",
            "29.5",
            "--stirrup-diameter",
            "8",
            "--main-bar-diameter",
            "25",
            *orientation_args(),
            "--concrete",
            "B25",
            "--rebar",
            "A500",
            "--as-area",
            "2454.369260617026",
            "--moment",
            "250000000",
            "--load-duration",
            "short",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["status"] == "outside_applicability"
    assert payload["result"]["capacity_applicable"] is False
    assert "Mult" not in payload["result"]
    assert "utilization" not in payload["result"]


def test_cli_bending_never_emits_infinity_for_large_finite_input(capsys):
    exit_code = main(
        [
            "bending",
            *section_args(),
            *orientation_args(),
            "--concrete",
            "B25",
            "--rebar",
            "A500",
            "--as-area",
            "1e308",
            "--moment",
            "150000000",
            "--load-duration",
            "short",
            "--json",
        ]
    )

    output = capsys.readouterr().out
    payload = json.loads(output, parse_constant=lambda value: pytest.fail(value))
    assert exit_code == 0
    assert payload["status"] == "outside_applicability"
    assert payload["result"]["x"] is None
    assert "Mult" not in payload["result"]


def test_cli_bending_unsupported_material_profile_is_fail_closed(capsys):
    exit_code = main(
        [
            "bending",
            *section_args(),
            *orientation_args(),
            "--concrete",
            "B25",
            "--rebar",
            "A240",
            "--as-area",
            "942.48",
            "--moment",
            "150000000",
            "--load-duration",
            "short",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["status"] == "outside_applicability"
    assert payload["result"]["xi_R"] is None
    assert payload["result"]["normative_profile_id"] is None
    assert payload["result"]["layout_applicability_status"] == "not_checked_area_only"
    assert payload["result"]["manual_applicability_confirmation_required"] is True
    assert payload["result"]["project_use_status"] == "prohibited"
    assert payload["result"]["project_use"] is False
    assert "Mult" not in payload["result"]


def test_cli_bending_text_handles_unavailable_unsupported_profile_values(capsys):
    exit_code = main(
        [
            "bending",
            *section_args(),
            *orientation_args(),
            "--concrete",
            "B25",
            "--rebar",
            "A240",
            "--as-area",
            "942.48",
            "--moment",
            "150000000",
            "--load-duration",
            "short",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "status: outside_applicability" in output
    assert "x: not available" in output
    assert "xi: not available" in output
    assert "xi_R: not available" in output
    assert "M_ult not available: outside applicability" in output
    assert "project_use_status: prohibited" in output
    assert "project_use: false" in output
    assert "requires_engineer_review: true" in output


def test_cli_shear_command_text_output(capsys):
    exit_code = main(
        [
            "shear",
            *section_args(),
            "--concrete",
            "B25",
            "--stirrup-rebar",
            "A240",
            "--Q",
            "80000",
            "--Asw",
            "100.53",
            "--sw",
            "200",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Shear check" in captured.out
    assert "status: pass" in captured.out


def test_cli_crack_formation_text_output(capsys):
    exit_code = main(
        [
            "crack-formation",
            *section_args(),
            "--concrete",
            "B25",
            "--moment-ser",
            "30000000",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Crack formation" in captured.out
    assert "Mcrc" in captured.out


def test_cli_crack_formation_json_output(capsys):
    exit_code = main(
        [
            "crack-formation",
            *section_args(),
            "--concrete",
            "B25",
            "--moment-ser",
            "30000000",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "crack-formation"
    assert data["status"] == "crack"
    assert "Mcrc" in data["result"]


def test_cli_crack_width_text_output(capsys):
    exit_code = main(
        [
            "crack-width",
            *section_args(),
            "--concrete",
            "B25",
            "--rebar",
            "A500",
            "--moment-ser",
            "30000000",
            "--as-area",
            "942.48",
            "--acrc-limit",
            "0.3",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Crack width" in captured.out
    assert "acrc" in captured.out


def test_cli_crack_width_json_output(capsys):
    exit_code = main(
        [
            "crack-width",
            *section_args(),
            "--concrete",
            "B25",
            "--rebar",
            "A500",
            "--moment-ser",
            "30000000",
            "--as-area",
            "942.48",
            "--acrc-limit",
            "0.3",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "crack-width"
    assert "acrc" in data["result"]
    assert "status" in data["result"]


def test_cli_deflection_text_output(capsys):
    exit_code = main(
        [
            "deflection",
            *section_args(),
            "--concrete",
            "B25",
            "--rebar",
            "A500",
            "--moment-ser",
            "30000000",
            "--as-area",
            "942.48",
            "--span",
            "6000",
            "--deflection-limit-ratio",
            "250",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Deflection" in captured.out
    assert "curvature" in captured.out
    assert "I_eff" in captured.out


def test_cli_deflection_json_output(capsys):
    exit_code = main(
        [
            "deflection",
            *section_args(),
            "--concrete",
            "B25",
            "--rebar",
            "A500",
            "--moment-ser",
            "30000000",
            "--as-area",
            "942.48",
            "--span",
            "6000",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "deflection"
    assert "deflection" in data["result"]
    assert "I_eff" in data["result"]


def test_cli_select_longitudinal_command_text_output(capsys):
    exit_code = main(
        [
            "select-longitudinal",
            *section_args(),
            *orientation_args(),
            "--concrete",
            "B25",
            "--rebar",
            "A500",
            "--moment",
            "150000000",
            "--load-duration",
            "short",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Longitudinal reinforcement options" in captured.out
    assert "status: pass" in captured.out
    assert "constructive" in captured.out
    assert "reinforcement ratio" in captured.out
    assert "evidence_status: needs_engineer_review" in captured.out
    assert "project_use_status: prohibited" in captured.out
    assert "project_use: false" in captured.out


def test_cli_select_longitudinal_json_exposes_top_level_and_option_safety(capsys):
    exit_code = main(
        [
            "select-longitudinal",
            *section_args(),
            *orientation_args(),
            "--concrete",
            "B25",
            "--rebar",
            "A500",
            "--moment",
            "150000000",
            "--load-duration",
            "short",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["project_use_status"] == "prohibited"
    assert payload["project_use"] is False
    assert payload["requires_engineer_review"] is True
    assert payload["result"]
    assert all(option["project_use_status"] == "prohibited" for option in payload["result"])
    assert all(option["project_use"] is False for option in payload["result"])


def test_cli_select_longitudinal_marks_unsupported_profile_outside_applicability(capsys):
    exit_code = main(
        [
            "select-longitudinal",
            *section_args(),
            *orientation_args(),
            "--concrete",
            "B25",
            "--rebar",
            "A240",
            "--moment",
            "150000000",
            "--load-duration",
            "short",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["status"] == "outside_applicability"
    assert payload["result"] == []
    assert payload["project_use"] is False
    assert any("unsupported ULS longitudinal rebar" in item for item in payload["warnings"])


def test_cli_select_transverse_command_text_output(capsys):
    exit_code = main(
        [
            "select-transverse",
            *section_args(),
            "--concrete",
            "B25",
            "--stirrup-rebar",
            "A240",
            "--Q",
            "80000",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Transverse reinforcement options" in captured.out
    assert "status: pass" in captured.out
    assert "constructive" in captured.out
    assert "max_spacing" in captured.out
    assert "project_use_status: prohibited" in captured.out
    assert "project_use: false" in captured.out


def test_cli_select_transverse_json_preserves_candidate_geometry_and_safety(capsys):
    exit_code = main(
        [
            "select-transverse",
            *section_args(),
            "--concrete",
            "B25",
            "--stirrup-rebar",
            "A240",
            "--Q",
            "80000",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["project_use"] is False
    assert payload["project_use_status"] == "prohibited"
    assert payload["result"]
    assert all(
        float(option["geometry_stirrup_diameter"])
        == float(option["scheme"].split("/")[0][1:])
        for option in payload["result"]
    )
    assert all(option["project_use"] is False for option in payload["result"])


def test_cli_design_rectangular_command_text_output(capsys):
    exit_code = main(
        [
            "design-rectangular",
            "--b",
            "300",
            "--h",
            "500",
            "--cover",
            "32",
            "--stirrup-diameter",
            "8",
            "--concrete",
            "B25",
            "--rebar",
            "A500",
            "--stirrup-rebar",
            "A240",
            "--moment",
            "150000000",
            "--shear",
            "80000",
            *orientation_args(),
            "--load-duration",
            "short",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Rectangular design" in captured.out
    assert "status: pass" in captured.out
    assert "strength_status: pass" in captured.out
    assert "serviceability_status: not_checked" in captured.out
    assert "overall_status: pass" in captured.out
    assert "evidence_status: needs_engineer_review" in captured.out
    assert "project_use_status: prohibited" in captured.out
    assert "project_use: false" in captured.out
    assert "requires_engineer_review: true" in captured.out
    assert "constructive" in captured.out
    assert "max_spacing" in captured.out
    assert "reinforcement ratio" in captured.out


def test_cli_design_rectangular_with_cracks(capsys):
    exit_code = main(
        [
            "design-rectangular",
            "--b",
            "300",
            "--h",
            "500",
            "--cover",
            "32",
            "--stirrup-diameter",
            "8",
            "--concrete",
            "B25",
            "--rebar",
            "A500",
            "--stirrup-rebar",
            "A240",
            "--moment",
            "150000000",
            "--shear",
            "80000",
            *orientation_args(),
            "--load-duration",
            "short",
            "--check-cracks",
            "--moment-ser",
            "30000000",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Rectangular design" in captured.out
    assert "crack_formation" in captured.out


def test_cli_design_rectangular_with_crack_width(capsys):
    exit_code = main(
        [
            "design-rectangular",
            "--b",
            "300",
            "--h",
            "500",
            "--cover",
            "32",
            "--stirrup-diameter",
            "8",
            "--concrete",
            "B25",
            "--rebar",
            "A500",
            "--stirrup-rebar",
            "A240",
            "--moment",
            "150000000",
            "--shear",
            "80000",
            *orientation_args(),
            "--load-duration",
            "short",
            "--check-crack-width",
            "--moment-ser",
            "30000000",
            "--acrc-limit",
            "0.3",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Rectangular design" in captured.out
    assert "crack_width" in captured.out


def test_cli_design_rectangular_with_deflection(capsys):
    exit_code = main(
        [
            "design-rectangular",
            "--b",
            "300",
            "--h",
            "500",
            "--cover",
            "32",
            "--stirrup-diameter",
            "8",
            "--concrete",
            "B25",
            "--rebar",
            "A500",
            "--stirrup-rebar",
            "A240",
            "--moment",
            "150000000",
            "--shear",
            "80000",
            *orientation_args(),
            "--load-duration",
            "short",
            "--check-deflection",
            "--moment-ser",
            "30000000",
            "--span",
            "6000",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Rectangular design" in captured.out
    assert "deflection" in captured.out


def test_cli_design_rectangular_json_output(capsys):
    exit_code = main(
        [
            "design-rectangular",
            "--b",
            "300",
            "--h",
            "500",
            "--cover",
            "32",
            "--stirrup-diameter",
            "8",
            "--concrete",
            "B25",
            "--rebar",
            "A500",
            "--stirrup-rebar",
            "A240",
            "--moment",
            "150000000",
            "--shear",
            "80000",
            *orientation_args(),
            "--load-duration",
            "short",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "design-rectangular"
    assert data["status"] == "pass"
    assert data["result"]["status"] == "pass"
    assert data["result"]["strength_status"] == "pass"
    assert data["result"]["serviceability_status"] == "not_checked"
    assert data["result"]["overall_status"] == "pass"
    assert data["result"]["evidence_status"] == "needs_engineer_review"
    assert data["result"]["project_use_status"] == "prohibited"
    assert data["result"]["project_use"] is False
    assert data["result"]["requires_engineer_review"] is True
    assert data["result"]["protocol_strength_status"] == "pass"
    assert data["result"]["protocol_serviceability_status"] == "not_checked"
    assert data["result"]["protocol_overall_status"] == "pass"
    assert "constructive_status" in data["result"]["selected_transverse"]
    assert "constructive_max_spacing" in data["result"]["selected_transverse"]
    assert "sw_max_by_shear_rule" in data["result"]["selected_transverse"]
    assert "qsw_rule_status" in data["result"]["selected_transverse"]
    assert "transverse_reinforcement_countable" in data["result"]["selected_transverse"]


def test_cli_generate_dataset_command(tmp_path, capsys):
    output_path = tmp_path / "dataset_v001.csv"

    exit_code = main(
        [
            "generate-dataset",
            "--limit",
            "2",
            "--output",
            str(output_path),
            "--load-duration",
            "short",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert output_path.exists()
    assert "rows: 2" in captured.out
    assert "dataset_version: 0.3" in captured.out
    assert "completeness_status: incomplete" in captured.out
    assert "evidence_status: needs_engineer_review" in captured.out
    assert "project_use_status: prohibited" in captured.out
    assert "project_use: false" in captured.out


def test_cli_generate_dataset_split_command(tmp_path, capsys):
    report_path = tmp_path / "report.json"

    exit_code = main(
        [
            "generate-dataset",
            "--limit",
            "10",
            "--split",
            "--output-dir",
            str(tmp_path),
            "--prefix",
            "dataset_test",
            "--report",
            str(report_path),
            "--load-duration",
            "short",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert (tmp_path / "dataset_test_train.csv").exists()
    assert (tmp_path / "dataset_test_validation.csv").exists()
    assert (tmp_path / "dataset_test_test.csv").exists()
    assert report_path.exists()
    assert "train_rows" in captured.out


def test_cli_generate_dataset_split_group_command(tmp_path, capsys):
    report_path = tmp_path / "report.json"

    exit_code = main(
        [
            "generate-dataset",
            "--limit",
            "20",
            "--split",
            "--group-split",
            "--seed",
            "42",
            "--output-dir",
            str(tmp_path),
            "--prefix",
            "dataset_group",
            "--report",
            str(report_path),
            "--load-duration",
            "short",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert (tmp_path / "dataset_group_train.csv").exists()
    assert (tmp_path / "dataset_group_validation.csv").exists()
    assert (tmp_path / "dataset_group_test.csv").exists()
    assert report_path.exists()
    assert "unique_group_count" in captured.out
    assert "unsafe_rows_count" in captured.out


def test_cli_generate_dataset_json_exposes_v03_provenance(tmp_path, capsys):
    output_path = tmp_path / "dataset_v003.csv"

    exit_code = main(
        [
            "generate-dataset",
            "--limit",
            "2",
            "--output",
            str(output_path),
            "--load-duration",
            "short",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["dataset_version"] == "0.3"
    assert payload["load_duration"] == "short"
    assert payload["local_axes_id"] == "synthetic-dataset-local-axes"
    assert payload["moment_axis"] == "local_z"
    assert payload["tension_face"] == "local_y_min"
    assert payload["completeness_status"] == "incomplete"
    assert payload["evidence_status"] == "needs_engineer_review"
    assert payload["project_use_status"] == "prohibited"
    assert payload["project_use"] is False


def test_cli_generate_dataset_rejects_long_until_shear_context(tmp_path):
    with pytest.raises(SystemExit):
        main(
            [
                "generate-dataset",
                "--limit",
                "1",
                "--output",
                str(tmp_path / "long.csv"),
                "--load-duration",
                "long",
            ]
        )


def test_cli_dataset_loader_rejects_legacy_dataset_version(tmp_path):
    path = tmp_path / "legacy.csv"
    assert (
        main(
            [
                "generate-dataset",
                "--limit",
                "1",
                "--output",
                str(path),
                "--load-duration",
                "short",
            ]
        )
        == 0
    )
    with path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = list(reader.fieldnames or ())
        rows = list(reader)
    rows[0]["dataset_version"] = "0.2"
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match="unsupported dataset_version"):
        main(["validate", "--dataset", str(path), "--json"])


def test_cli_dataset_loader_rejects_long_duration_row(tmp_path):
    path = tmp_path / "long.csv"
    assert (
        main(
            [
                "generate-dataset",
                "--limit",
                "1",
                "--output",
                str(path),
                "--load-duration",
                "short",
            ]
        )
        == 0
    )
    with path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = list(reader.fieldnames or ())
        rows = list(reader)
    rows[0]["load_duration"] = "long"
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match="rows must use load_duration='short'"):
        main(["validate", "--dataset", str(path), "--json"])


def test_cli_dataset_loader_rejects_missing_orientation_column(tmp_path):
    path = tmp_path / "missing_orientation.csv"
    assert (
        main(
            [
                "generate-dataset",
                "--limit",
                "1",
                "--output",
                str(path),
                "--load-duration",
                "short",
            ]
        )
        == 0
    )
    with path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = [
            field for field in (reader.fieldnames or ()) if field != "local_axes_id"
        ]
        rows = list(reader)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match="local_axes_id"):
        main(["validate", "--dataset", str(path), "--json"])


def test_cli_validate_golden(capsys):
    exit_code = main(["validate", "--golden"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Validation" in captured.out
    assert "status: pass" in captured.out
    assert "completeness_status: incomplete" in captured.out
    assert "evidence_status: needs_engineer_review" in captured.out
    assert "project_use_status: prohibited" in captured.out
    assert "project_use: false" in captured.out
    assert "requires_engineer_review: true" in captured.out
    assert "golden: 12/12 passed" in captured.out
    assert "BMR-01: regression_match=pass" in captured.out
    assert "expected_calculation_status=pass" in captured.out
    assert "BMR-02: regression_match=pass; expected_calculation_status=fail" in captured.out
    assert (
        "BMR-05: regression_match=pass; "
        "expected_calculation_status=outside_applicability"
    ) in captured.out


def test_cli_validate_generated_dataset_json(capsys):
    exit_code = main(["validate", "--generate-dataset-limit", "10", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "validate"
    assert data["status"] == "pass"
    assert data["completeness_status"] == "incomplete"
    assert data["evidence_status"] == "needs_engineer_review"
    assert data["project_use_status"] == "prohibited"
    assert data["project_use"] is False
    assert data["requires_engineer_review"] is True
    assert data["dataset"]["total_rows"] == 10
    assert data["dataset"]["group_leakage_count"] == 0


def test_cli_validate_external_template_and_acceptance_report(tmp_path, capsys):
    external_template = tmp_path / "scad_lira_template.csv"
    acceptance_report = tmp_path / "acceptance_report.json"

    exit_code = main(
        [
            "validate",
            "--golden",
            "--generate-dataset-limit",
            "10",
            "--external-template",
            str(external_template),
            "--acceptance-report",
            str(acceptance_report),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert external_template.exists()
    assert acceptance_report.exists()
    assert data["acceptance"]["status"] == "warning"
    assert data["acceptance"]["golden_case_count"] == 12
    assert data["acceptance"]["golden_passed_count"] == 12
    assert data["acceptance_report"] == str(acceptance_report)


def test_cli_validate_external_input_acceptance_pass(tmp_path, capsys):
    external_input = tmp_path / "filled.csv"
    acceptance_report = tmp_path / "acceptance_report.json"
    export_external_comparison_csv((_filled_external_row(),), external_input)

    exit_code = main(
        [
            "validate",
            "--golden",
            "--generate-dataset-limit",
            "10",
            "--external-input",
            str(external_input),
            "--acceptance-report",
            str(acceptance_report),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert acceptance_report.exists()
    assert data["acceptance"]["status"] == "pass"
    assert data["acceptance"]["completed_external_rows"] == 1


def test_cli_validate_external_input_incomplete_fails(tmp_path, capsys):
    external_input = tmp_path / "incomplete.csv"
    acceptance_report = tmp_path / "acceptance_report.json"
    export_external_comparison_csv((_filled_external_row(scad_As=None),), external_input)

    exit_code = main(
        [
            "validate",
            "--golden",
            "--generate-dataset-limit",
            "10",
            "--external-input",
            str(external_input),
            "--acceptance-report",
            str(acceptance_report),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["status"] == "fail"
    assert data["acceptance"]["status"] == "fail"
    assert data["acceptance"]["external_incomplete_count"] == 1


def test_cli_materials_audit_text_output(capsys):
    exit_code = main(["materials-audit"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Materials audit" in captured.out
    assert "review_required" in captured.out
    assert "B25" in captured.out
    assert "A500" in captured.out
    assert "requires_engineer_review=True" in captured.out


def test_cli_materials_audit_json_output(capsys):
    exit_code = main(["materials-audit", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "materials-audit"
    assert data["status"] == "review_required"
    assert data["rows"]
    assert any(row["class_name"] == "B25" for row in data["rows"])
    assert any(row["class_name"] == "A500" for row in data["rows"])
    assert any(
        "require engineer review" in warning
        for warning in data["warnings"]
    )


def test_cli_materials_audit_verification_template_output(capsys):
    exit_code = main(["materials-audit", "--verification-template"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Material verification template" in captured.out
    assert "material_catalog_verification_template.csv" in captured.out


def test_cli_materials_audit_verification_csv_json(tmp_path, capsys):
    csv_path = tmp_path / "material_verification.csv"
    _write_engineer_verified_material_csv(csv_path)

    exit_code = main(["materials-audit", "--verification-csv", str(csv_path), "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "materials-audit"
    assert data["mode"] == "material-verification"
    assert data["status"] == "pass"
    assert data["summary"]["engineer_verified_count"] == data["summary"]["required_rows_count"]


def test_cli_material_verification_text_output(capsys):
    exit_code = main(["material-verification"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Material verification" in captured.out
    assert "status: review_required" in captured.out
    assert "verification_status=draft" in captured.out


def test_cli_material_verification_json_output(capsys):
    exit_code = main(["material-verification", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "material-verification"
    assert data["status"] == "review_required"
    assert data["summary"]["draft_count"] == data["summary"]["required_rows_count"]
    assert any(row["class_name"] == "B25" for row in data["rows"])
    assert any(row["class_name"] == "A500" for row in data["rows"])


def test_cli_material_verification_template_output(capsys):
    exit_code = main(["material-verification", "--template"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Material verification template" in captured.out
    assert "material_catalog_verification_template.csv" in captured.out


def test_cli_material_verification_engineer_csv_json(tmp_path, capsys):
    csv_path = tmp_path / "material_verification.csv"
    _write_engineer_verified_material_csv(csv_path)

    exit_code = main(["material-verification", "--csv", str(csv_path), "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "material-verification"
    assert data["status"] == "pass"
    assert data["summary"]["engineer_verified_count"] == data["summary"]["required_rows_count"]
    assert data["summary"]["requires_engineer_review"] is False


def test_cli_material_verification_incomplete_engineer_metadata_json(tmp_path, capsys):
    csv_path = tmp_path / "material_verification.csv"
    _write_engineer_verified_material_csv(csv_path, engineer_name="")

    exit_code = main(["material-verification", "--csv", str(csv_path), "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["status"] == "review_required"
    assert data["summary"]["needs_review_count"] >= 1


def test_cli_material_verification_report_json_output(tmp_path, capsys):
    csv_path = tmp_path / "material_verification.csv"
    _write_engineer_verified_material_csv(csv_path)

    exit_code = main(["material-verification-report", "--csv", str(csv_path), "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "material-verification-report"
    assert data["status"] == "pass"
    assert data["summary"]["total_rows"] == 51
    assert data["summary"]["engineer_verified_count"] == 51
    assert data["summary"]["missing_required_fields_count"] == 0
    assert data["needs_review_rows"] == []


def test_cli_material_verification_report_markdown_output(tmp_path, capsys):
    csv_path = tmp_path / "material_verification.csv"
    report_path = tmp_path / "material_verification_report.md"
    _write_engineer_verified_material_csv(csv_path, engineer_name="")

    exit_code = main(
        [
            "material-verification-report",
            "--csv",
            str(csv_path),
            "--output",
            str(report_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert report_path.exists()
    assert "Material Verification Report" in captured.out
    assert "missing_required_fields_count" in captured.out
    assert "Needs Review Rows" in report_path.read_text(encoding="utf-8")


def test_cli_manual_cases_text_output(capsys):
    exit_code = main(["manual-cases"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Manual SP63 verification cases" in captured.out
    assert "status: pass" in captured.out
    assert "case_count: 6" in captured.out
    assert "manual_case_01" in captured.out


def test_cli_manual_cases_json_output(capsys):
    exit_code = main(["manual-cases", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "manual-cases"
    assert data["status"] == "pass"
    assert data["case_count"] == 6
    assert data["passed_count"] == 6
    assert all(case["passed"] for case in data["cases"])
    assert data["requires_engineer_review"] is True


def test_cli_ml_readiness_json_output(capsys):
    exit_code = main(["ml-readiness", "--generate-dataset-limit", "20", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "ml-readiness"
    assert data["status"] == "review_required"
    assert data["total_rows"] == 20
    assert data["missing_required_columns"] == []
    assert data["unsafe_rows_count"] == 0
    assert data["status_counts"]["overall_status"] == {"pass": 20}
    assert "overall_status" in data["constant_target_columns"]
    assert any(
        "dataset contains only passing overall_status rows" in warning
        for warning in data["warnings"]
    )


def test_cli_ml_baseline_json_output(capsys):
    exit_code = main(
        [
            "ml-baseline",
            "--safe-limit",
            "30",
            "--diagnostic-limit",
            "1000",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "ml-baseline"
    assert data["ml_is_advisory_only"] is True
    assert data["neural_network_used"] is False
    assert data["deterministic_checks_required"] is True
    assert "longitudinal_as_mm2" in data["regression_metrics"]
    assert "bending_utilization" in data["regression_metrics"]
    assert data["classification_metrics"]["target"] == "overall_status"
    assert data["diagnostic_rows"] == 1000
    expanded = data["expanded_diagnostic_classification"]
    assert expanded["target"] == "overall_status"
    assert expanded["target_constant"] is False
    assert expanded["class_distribution"]["pass"] >= 1
    assert expanded["class_distribution"]["fail"] >= 1
    assert expanded["class_distribution"]["review_or_fail"] >= 1
    assert expanded["split"]["group_key_present"] is True
    assert expanded["split"]["unique_group_count"] >= 50
    assert expanded["split"]["group_leakage_checked"] is True
    assert expanded["split"]["group_leakage_count"] == 0
    assert "input_only_features" in expanded["feature_modes"]
    assert "deterministic_derived_features" in expanded["feature_modes"]
    assert expanded["feature_modes"]["input_only_features"]["logistic"]["accuracy"] >= 0
    assert not any("fewer than 1000 rows" in warning for warning in data["warnings"])
    assert any("deterministic output values" in warning for warning in data["warnings"])


def test_cli_neural_surrogate_json_output(capsys):
    exit_code = main(["neural-surrogate", "--diagnostic-limit", "100", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "neural-surrogate"
    assert data["neural_network_used"] is True
    assert data["ml_is_advisory_only"] is True
    assert data["deterministic_checks_required"] is True
    assert data["requires_engineer_review"] is True
    assert data["classification_target"] == "overall_status"
    assert "accuracy" in data["classification_metrics"]
    assert "macro_f1" in data["classification_metrics"]
    assert "longitudinal_as_mm2" in data["regression_metrics"]
    assert any("must not be used as a design checker" in warning for warning in data["warnings"])


def test_cli_ml_proposal_verify_json_output(capsys):
    exit_code = main(["ml-proposal-verify", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "ml-proposal-verify"
    assert data["status"] == "pass"
    assert data["verified_count"] == 2
    assert data["accepted_count"] == 1
    assert data["rejected_count"] == 1
    assert data["ml_is_advisory_only"] is True
    assert data["deterministic_checks_required"] is True


def test_cli_train_baseline_command(tmp_path, capsys):
    model_path = tmp_path / "baseline_model.pkl"
    metrics_path = tmp_path / "baseline_metrics.json"

    exit_code = main(
        [
            "train-baseline",
            "--generate-dataset-limit",
            "50",
            "--model-output",
            str(model_path),
            "--metrics-output",
            str(metrics_path),
            "--seed",
            "42",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert model_path.exists()
    assert metrics_path.exists()
    assert "experimental and advisory only" in captured.out
    assert "Deterministic SP63 checks remain mandatory" in captured.out
    assert (
        "ML predictions are not accepted unless deterministic safety check passes"
        in captured.out
    )
    assert "ml_quality_status" in captured.out
    assert "completeness_status: incomplete" in captured.out
    assert "evidence_status: needs_engineer_review" in captured.out
    assert "project_use_status: prohibited" in captured.out
    assert "project_use: false" in captured.out
    assert "ml_ready_for_project_use: false" in captured.out
    assert "requires_engineer_review: true" in captured.out

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert "safety_metrics" in metrics
    assert "quality_gate" in metrics
    assert "unsafe_prediction_rate" in metrics["safety_metrics"]
    assert metrics["completeness_status"] == "incomplete"
    assert metrics["evidence_status"] == "needs_engineer_review"
    assert metrics["project_use_status"] == "prohibited"
    assert metrics["project_use"] is False
    assert metrics["ml_ready_for_project_use"] is False
    assert metrics["requires_engineer_review"] is True
    if metrics["quality_gate"]["status"] != "pass":
        assert "model remains sandbox-only" in captured.out


def _write_engineer_verified_material_csv(
    csv_path,
    *,
    engineer_name: str = "Test Engineer",
    review_date: str = "2026-05-30",
    source_note: str = "engineer checked SP 63 table reference; no full text stored",
) -> None:
    rows = []
    for row in build_material_verification_rows():
        rows.append(
            {
                "material_type": row.material_type,
                "class_name": row.class_name,
                "property_name": row.property_name,
                "catalog_value": row.catalog_value,
                "unit": row.unit,
                "verification_status": "engineer_verified",
                "engineer_value": row.catalog_value,
                "engineer_name": engineer_name,
                "review_date": review_date,
                "source_note": source_note,
                "engineer_comment": "test",
                "requires_engineer_review": "false",
            }
        )
    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _filled_external_row(scad_As: float | None = 101.0) -> ExternalComparisonRow:
    return ExternalComparisonRow(
        case_id="case_000001",
        b=300,
        h=500,
        concrete_class="B25",
        rebar_class="A500",
        local_axes_id="cli-external-case-000001-local-axes",
        moment_axis="local_z",
        tension_face="local_y_min",
        load_duration="short",
        M=150_000_000,
        Q=80_000,
        program_As=100.0,
        program_stirrups="D8/200, 2 legs",
        program_Mult=100.0,
        program_Qult=100.0,
        completeness_status="incomplete",
        evidence_status="needs_engineer_review",
        project_use_status="prohibited",
        project_use=False,
        requires_engineer_review=True,
        scad_As=scad_As,
        scad_Mult=102.0,
        scad_Qult=103.0,
        accepted=True,
    )
