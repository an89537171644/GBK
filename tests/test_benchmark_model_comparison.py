import json

from sp63_core.cli import main
from sp63_core.ml import (
    build_benchmark_model_comparison,
    run_synthetic_ml_benchmark,
)


def _benchmark_payload():
    return {
        "report_type": "synthetic_ml_benchmark",
        "status": "review_required",
        "benchmark_status": "review_required",
        "dataset_row_count": 120,
        "final_distribution": {"pass": 40, "fail": 40, "review_or_fail": 40},
        "baseline_status": "review_required",
        "neural_status": "review_required",
        "baseline_metrics": {
            "status": "review_required",
            "metrics": {
                "accuracy": 0.6,
                "macro_f1": 0.55,
                "weighted_f1": 0.58,
                "precision_macro": 0.5,
                "recall_macro": 0.52,
            },
        },
        "neural_metrics": {
            "status": "review_required",
            "metrics": {
                "accuracy": 0.7,
                "macro_f1": 0.55,
                "weighted_f1": 0.57,
                "precision_macro": 0.51,
                "recall_macro": 0.52,
            },
        },
        "recommendations": ["keep benchmark synthetic-only"],
        "warnings": ["synthetic benchmark metrics are not production evidence"],
        "errors": [],
        "synthetic_data_only": True,
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
    }


def _write_benchmark_report(path, payload=None):
    path.write_text(
        json.dumps(payload or _benchmark_payload(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def test_comparison_works_on_synthetic_benchmark_report(tmp_path):
    benchmark_dir = tmp_path / "benchmark"
    result = run_synthetic_ml_benchmark(
        output_dir=benchmark_dir,
        target_distribution_goal={"pass": 1, "fail": 1, "review_or_fail": 1},
        seed=42,
        max_attempts=500,
    )

    comparison = build_benchmark_model_comparison(
        benchmark_report_path=benchmark_dir / "benchmark_report.json",
        output_dir=tmp_path / "comparison",
    )

    assert result.accepted_count == 3
    assert comparison.status == "review_required"
    assert comparison.dataset_row_count == 3
    assert comparison.final_distribution == {"review_or_fail": 1, "pass": 1, "fail": 1}
    assert set(comparison.metric_winners) == {
        "accuracy",
        "macro_f1",
        "weighted_f1",
        "precision_macro",
        "recall_macro",
    }
    assert (tmp_path / "comparison" / "model_comparison.md").exists()
    assert (tmp_path / "comparison" / "model_comparison.json").exists()
    assert (tmp_path / "comparison" / "model_comparison.csv").exists()


def test_metric_winners_are_calculated(tmp_path):
    report_path = tmp_path / "benchmark_report.json"
    _write_benchmark_report(report_path)

    result = build_benchmark_model_comparison(benchmark_report_path=report_path)

    assert result.metric_winners["accuracy"] == "neural"
    assert result.metric_winners["macro_f1"] == "tie"
    assert result.metric_winners["weighted_f1"] == "baseline"
    assert result.metric_winners["precision_macro"] == "neural"
    assert result.metric_winners["recall_macro"] == "tie"
    assert len(result.csv_rows) == 5
    assert "Synthetic Benchmark Model Comparison" in result.markdown
    assert result.json_data["report_type"] == "benchmark_model_comparison"


def test_missing_metric_adds_warning(tmp_path):
    payload = _benchmark_payload()
    payload["neural_metrics"]["metrics"].pop("accuracy")
    report_path = tmp_path / "benchmark_report.json"
    _write_benchmark_report(report_path, payload)

    result = build_benchmark_model_comparison(benchmark_report_path=report_path)

    assert result.metric_winners["accuracy"] == "missing"
    assert any("accuracy" in warning for warning in result.warnings)


def test_missing_critical_field_fails(tmp_path):
    payload = _benchmark_payload()
    payload.pop("baseline_metrics")
    report_path = tmp_path / "benchmark_report.json"
    _write_benchmark_report(report_path, payload)

    result = build_benchmark_model_comparison(benchmark_report_path=report_path)

    assert result.status == "fail"
    assert any("missing critical fields" in error for error in result.errors)


def test_cli_benchmark_model_comparison_json_and_output_files(tmp_path, capsys):
    report_path = tmp_path / "benchmark_report.json"
    output_dir = tmp_path / "comparison"
    _write_benchmark_report(report_path)

    exit_code = main(
        [
            "benchmark-model-comparison",
            "--benchmark-report",
            str(report_path),
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "benchmark-model-comparison"
    assert payload["comparison_status"] == "review_required"
    assert payload["metric_winners"]["accuracy"] == "neural"
    assert (output_dir / "model_comparison.md").exists()
    assert (output_dir / "model_comparison.json").exists()
    assert (output_dir / "model_comparison.csv").exists()


def test_cli_benchmark_model_comparison_markdown(tmp_path, capsys):
    report_path = tmp_path / "benchmark_report.json"
    _write_benchmark_report(report_path)

    exit_code = main(
        [
            "benchmark-model-comparison",
            "--benchmark-report",
            str(report_path),
            "--markdown",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Synthetic Benchmark Model Comparison - Advisory Only" in captured.out


def test_cli_benchmark_model_comparison_csv(tmp_path, capsys):
    report_path = tmp_path / "benchmark_report.json"
    _write_benchmark_report(report_path)

    exit_code = main(
        [
            "benchmark-model-comparison",
            "--benchmark-report",
            str(report_path),
            "--csv",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "metric,baseline,neural,winner" in captured.out
    assert "accuracy,0.6,0.7,neural" in captured.out
