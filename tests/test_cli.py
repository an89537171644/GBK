import json
from pathlib import Path

from sp63_core.cli import main


def test_cli_demo_runs_without_errors(capsys):
    exit_code = main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "sp63-core 0.1.0" in captured.out
    assert "MVP status" in captured.out
    assert "Bending check" in captured.out
    assert "status: pass" in captured.out


def test_cli_bending_outputs_pass_status(capsys):
    exit_code = main(
        [
            "bending",
            "--cover",
            "32",
            "--as-area",
            "942.48",
            "--moment",
            "150000000",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Bending check" in captured.out
    assert "status: pass" in captured.out


def test_cli_bending_json_outputs_json_only(capsys):
    exit_code = main(
        [
            "bending",
            "--cover",
            "32",
            "--as-area",
            "942.48",
            "--moment",
            "150000000",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "pass"
    assert payload["requires_engineer_review"] is True
    assert "Bending check" not in captured.out


def test_cli_shear_outputs_pass_status(capsys):
    exit_code = main(
        [
            "shear",
            "--cover",
            "32",
            "--q",
            "80000",
            "--asw",
            "100.53",
            "--sw",
            "200",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Shear check" in captured.out
    assert "status: pass" in captured.out


def test_cli_shear_json_outputs_json_only(capsys):
    exit_code = main(
        [
            "shear",
            "--cover",
            "32",
            "--q",
            "80000",
            "--asw",
            "100.53",
            "--sw",
            "200",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "pass"
    assert payload["requires_engineer_review"] is True
    assert "Shear check" not in captured.out


def test_cli_select_longitudinal_outputs_at_least_one_option(capsys):
    exit_code = main(
        [
            "select-longitudinal",
            "--moment",
            "150000000",
            "--max-results",
            "3",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "scheme:" in captured.out
    assert "status: pass" in captured.out


def test_cli_select_transverse_outputs_at_least_one_option(capsys):
    exit_code = main(
        [
            "select-transverse",
            "--cover",
            "32",
            "--q",
            "80000",
            "--max-results",
            "3",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "scheme:" in captured.out
    assert "status: pass" in captured.out


def test_cli_design_outputs_overall_pass(capsys):
    exit_code = main(
        [
            "design",
            "--cover",
            "32",
            "--moment",
            "150000000",
            "--q",
            "80000",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "selected longitudinal reinforcement:" in captured.out
    assert "selected transverse reinforcement:" in captured.out
    assert "overall status: pass" in captured.out


def test_cli_generate_dataset_creates_csv(tmp_path, capsys):
    output_path = tmp_path / "dataset.csv"
    exit_code = main(
        [
            "generate-dataset",
            "--limit",
            "3",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "generated rows: 3" in captured.out
    assert Path(output_path).exists()
    assert output_path.read_text(encoding="utf-8").startswith("case_id,")


def test_cli_generate_dataset_split_creates_three_csv_files(tmp_path, capsys):
    output_dir = tmp_path / "splits"
    exit_code = main(
        [
            "generate-dataset",
            "--limit",
            "10",
            "--output-dir",
            str(output_dir),
            "--split",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "train:" in captured.out
    assert "validation:" in captured.out
    assert "test:" in captured.out
    assert (output_dir / "train.csv").exists()
    assert (output_dir / "validation.csv").exists()
    assert (output_dir / "test.csv").exists()


def test_cli_design_json_outputs_json_only(capsys):
    exit_code = main(
        [
            "design",
            "--cover",
            "32",
            "--moment",
            "150000000",
            "--q",
            "80000",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.lstrip().startswith("{")
    assert '"status": "pass"' in captured.out
