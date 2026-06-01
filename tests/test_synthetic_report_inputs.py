import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.dataset import generate_synthetic_report_inputs
from sp63_core.report import load_rectangular_design_input_from_json


def test_synthetic_report_input_generator_creates_requested_cases(tmp_path):
    output_dir = tmp_path / "synthetic_inputs"

    result = generate_synthetic_report_inputs(
        output_dir=output_dir,
        case_count=5,
        seed=42,
    )

    assert result.status == "pass"
    assert result.generated_count == 5
    assert result.skipped_count == 0
    assert result.requires_engineer_review is True
    assert result.synthetic_data_only is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert len(sorted(output_dir.glob("case_*.json"))) == 5
    assert (output_dir / "README_SYNTHETIC.md").exists()
    assert (output_dir / "synthetic_manifest.json").exists()


def test_synthetic_report_inputs_are_reproducible_with_seed(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    generate_synthetic_report_inputs(output_dir=first_dir, case_count=4, seed=123)
    generate_synthetic_report_inputs(output_dir=second_dir, case_count=4, seed=123)

    first_cases = [
        path.read_text(encoding="utf-8") for path in sorted(first_dir.glob("case_*.json"))
    ]
    second_cases = [
        path.read_text(encoding="utf-8") for path in sorted(second_dir.glob("case_*.json"))
    ]
    assert first_cases == second_cases


def test_synthetic_report_inputs_load_with_existing_reader(tmp_path):
    output_dir = tmp_path / "synthetic_inputs"
    generate_synthetic_report_inputs(output_dir=output_dir, case_count=3, seed=42)

    for input_path in sorted(output_dir.glob("case_*.json")):
        data = json.loads(input_path.read_text(encoding="utf-8"))
        assert {
            "b",
            "h",
            "cover",
            "stirrup_diameter_for_geometry",
            "concrete_class",
            "longitudinal_rebar_class",
            "stirrup_rebar_class",
            "M",
            "Q",
        }.issubset(data)
        design_input = load_rectangular_design_input_from_json(input_path)
        assert design_input.b > 0
        assert design_input.h > 0
        assert design_input.M > 0
        assert design_input.Q > 0


def test_synthetic_manifest_records_case_sha256(tmp_path):
    output_dir = tmp_path / "synthetic_inputs"
    generate_synthetic_report_inputs(output_dir=output_dir, case_count=3, seed=42)

    manifest = json.loads((output_dir / "synthetic_manifest.json").read_text(encoding="utf-8"))

    assert manifest["generator"] == "synthetic_report_inputs"
    assert manifest["case_count"] == 3
    assert manifest["seed"] == 42
    assert manifest["synthetic_data_only"] is True
    assert manifest["requires_engineer_review"] is True
    assert len(manifest["cases"]) == 3
    assert all(case["sha256"] for case in manifest["cases"])
    assert all(Path(case["path"]).name.startswith("case_") for case in manifest["cases"])


def test_cli_synthetic_report_inputs_json(tmp_path, capsys):
    output_dir = tmp_path / "synthetic_inputs"

    exit_code = main(
        [
            "synthetic-report-inputs",
            "--output-dir",
            str(output_dir),
            "--case-count",
            "4",
            "--seed",
            "42",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "synthetic-report-inputs"
    assert payload["status"] == "pass"
    assert payload["generated_count"] == 4
    assert payload["synthetic_data_only"] is True


def test_cli_synthetic_report_inputs_no_serviceability(tmp_path, capsys):
    output_dir = tmp_path / "synthetic_inputs"

    exit_code = main(
        [
            "synthetic-report-inputs",
            "--output-dir",
            str(output_dir),
            "--case-count",
            "2",
            "--no-serviceability",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    first_case = json.loads((output_dir / "case_0001.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["warnings"] == ["serviceability fields and checks were disabled"]
    assert "Mser" not in first_case
    assert "check_crack_width" not in first_case


def test_synthetic_inputs_can_feed_design_report_batch(tmp_path, capsys):
    input_dir = tmp_path / "synthetic_inputs"
    output_dir = tmp_path / "synthetic_reports"
    generate_synthetic_report_inputs(output_dir=input_dir, case_count=10, seed=42)

    exit_code = main(
        [
            "design-report-batch",
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["input_count"] == 10
    assert payload["report_count"] == 10
    assert (output_dir / "index.json").exists()


def test_committed_synthetic_batch_smoke_examples_exist():
    example_dir = Path("docs/reports/examples/synthetic_batch_smoke")
    manifest_path = example_dir / "synthetic_manifest.json"

    assert manifest_path.exists()
    assert len(sorted(example_dir.glob("case_*.json"))) == 10
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["case_count"] == 10
    assert manifest["synthetic_data_only"] is True
