import json

from sp63_core.cli import main
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


def test_cli_bending_command_text_output(capsys):
    exit_code = main(
        [
            "bending",
            *section_args(),
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


def test_cli_select_longitudinal_command_text_output(capsys):
    exit_code = main(
        [
            "select-longitudinal",
            *section_args(),
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
            "--load-duration",
            "short",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Rectangular design" in captured.out
    assert "status: pass" in captured.out
    assert "constructive" in captured.out
    assert "max_spacing" in captured.out
    assert "reinforcement ratio" in captured.out


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
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert output_path.exists()
    assert "rows: 2" in captured.out


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


def test_cli_validate_golden(capsys):
    exit_code = main(["validate", "--golden"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Validation" in captured.out
    assert "status: pass" in captured.out
    assert "golden:" in captured.out


def test_cli_validate_generated_dataset_json(capsys):
    exit_code = main(["validate", "--generate-dataset-limit", "10", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "validate"
    assert data["status"] == "pass"
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


def _filled_external_row(scad_As: float | None = 101.0) -> ExternalComparisonRow:
    return ExternalComparisonRow(
        case_id="case_000001",
        b=300,
        h=500,
        concrete_class="B25",
        rebar_class="A500",
        M=150_000_000,
        Q=80_000,
        program_As=100.0,
        program_stirrups="D8/200, 2 legs",
        program_Mult=100.0,
        program_Qult=100.0,
        scad_As=scad_As,
        scad_Mult=102.0,
        scad_Qult=103.0,
        accepted=True,
    )
