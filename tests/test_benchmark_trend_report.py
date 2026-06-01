import json

from sp63_core.cli import main
from sp63_core.ml import (
    build_benchmark_trend_report,
    discover_benchmark_reports,
)


def _benchmark_payload(
    *,
    dataset_row_count=120,
    pass_count=40,
    fail_count=40,
    review_count=40,
    baseline_accuracy=0.6,
    neural_accuracy=0.7,
    baseline_macro_f1=0.55,
    neural_macro_f1=0.55,
):
    return {
        "report_type": "synthetic_ml_benchmark",
        "status": "review_required",
        "benchmark_status": "review_required",
        "target_distribution_goal": {
            "pass": pass_count,
            "fail": fail_count,
            "review_or_fail": review_count,
        },
        "final_distribution": {
            "pass": pass_count,
            "fail": fail_count,
            "review_or_fail": review_count,
        },
        "dataset_row_count": dataset_row_count,
        "balance_status": "review_required",
        "quality_status": "review_required",
        "feature_status": "review_required",
        "baseline_status": "review_required",
        "neural_status": "review_required",
        "baseline_metrics": {
            "status": "review_required",
            "metrics": {
                "accuracy": baseline_accuracy,
                "macro_f1": baseline_macro_f1,
                "weighted_f1": 0.58,
                "precision_macro": 0.5,
                "recall_macro": 0.52,
            },
        },
        "neural_metrics": {
            "status": "review_required",
            "metrics": {
                "accuracy": neural_accuracy,
                "macro_f1": neural_macro_f1,
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload or _benchmark_payload(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def test_trend_report_aggregates_multiple_reports(tmp_path):
    report_a = tmp_path / "seed_1" / "benchmark_report.json"
    report_b = tmp_path / "seed_2" / "benchmark_report.json"
    _write_benchmark_report(
        report_a,
        _benchmark_payload(baseline_accuracy=0.6, neural_accuracy=0.7),
    )
    _write_benchmark_report(
        report_b,
        _benchmark_payload(baseline_accuracy=0.8, neural_accuracy=0.5),
    )

    result = build_benchmark_trend_report(
        benchmark_report_paths=(report_a, report_b),
        output_dir=tmp_path / "trend",
    )

    assert result.status == "review_required"
    assert result.benchmark_count == 2
    assert result.dataset_row_count_summary["total"] == 240
    assert result.dataset_row_count_summary["mean"] == 120
    assert result.distribution_summary["total"] == {
        "pass": 80,
        "fail": 80,
        "review_or_fail": 80,
    }
    assert result.baseline_metric_summary["accuracy"]["mean"] == 0.7
    assert result.baseline_metric_summary["accuracy"]["min"] == 0.6
    assert result.baseline_metric_summary["accuracy"]["max"] == 0.8
    assert result.baseline_metric_summary["accuracy"]["std"] == 0.10000000000000003
    assert result.winner_summary["accuracy"]["baseline_win_count"] == 1
    assert result.winner_summary["accuracy"]["neural_win_count"] == 1
    assert result.winner_summary["macro_f1"]["tie_count"] == 2
    assert (tmp_path / "trend" / "benchmark_trend_report.md").exists()
    assert (tmp_path / "trend" / "benchmark_trend_report.json").exists()
    assert (tmp_path / "trend" / "benchmark_trend_metrics.csv").exists()
    assert (tmp_path / "trend" / "benchmark_trend_winners.csv").exists()


def test_discover_benchmark_reports(tmp_path):
    report_a = tmp_path / "seed_1" / "benchmark_report.json"
    report_b = tmp_path / "nested" / "seed_2" / "benchmark_report.json"
    _write_benchmark_report(report_a)
    _write_benchmark_report(report_b)

    reports = discover_benchmark_reports(tmp_path)

    assert reports == tuple(sorted((report_a, report_b)))


def test_missing_metric_adds_warning_and_missing_count(tmp_path):
    payload = _benchmark_payload()
    payload["neural_metrics"]["metrics"].pop("accuracy")
    report_path = tmp_path / "benchmark_report.json"
    _write_benchmark_report(report_path, payload)

    result = build_benchmark_trend_report(benchmark_report_paths=(report_path,))

    assert result.neural_metric_summary["accuracy"]["missing_count"] == 1
    assert result.winner_summary["accuracy"]["missing_count"] == 1
    assert any("accuracy" in warning for warning in result.warnings)


def test_missing_critical_fields_do_not_block_valid_reports(tmp_path):
    valid_report = tmp_path / "valid" / "benchmark_report.json"
    invalid_report = tmp_path / "invalid" / "benchmark_report.json"
    payload = _benchmark_payload()
    broken_payload = _benchmark_payload()
    broken_payload.pop("baseline_metrics")
    _write_benchmark_report(valid_report, payload)
    _write_benchmark_report(invalid_report, broken_payload)

    result = build_benchmark_trend_report(
        benchmark_report_paths=(invalid_report, valid_report),
    )

    assert result.status == "review_required"
    assert result.benchmark_count == 1
    assert result.dataset_row_count_summary["total"] == 120
    assert any("input_error" in warning for warning in result.warnings)


def test_all_invalid_reports_fail(tmp_path):
    invalid_report = tmp_path / "invalid" / "benchmark_report.json"
    broken_payload = _benchmark_payload()
    broken_payload.pop("baseline_metrics")
    _write_benchmark_report(invalid_report, broken_payload)

    result = build_benchmark_trend_report(benchmark_report_paths=(invalid_report,))

    assert result.status == "fail"
    assert result.benchmark_count == 0
    assert "no valid benchmark reports were found" in result.errors


def test_cli_benchmark_trend_report_json_and_output_files(tmp_path, capsys):
    report_a = tmp_path / "seed_1" / "benchmark_report.json"
    report_b = tmp_path / "seed_2" / "benchmark_report.json"
    output_dir = tmp_path / "trend"
    _write_benchmark_report(
        report_a,
        _benchmark_payload(baseline_accuracy=0.6, neural_accuracy=0.7),
    )
    _write_benchmark_report(
        report_b,
        _benchmark_payload(baseline_accuracy=0.8, neural_accuracy=0.5),
    )

    exit_code = main(
        [
            "benchmark-trend-report",
            "--benchmark-report",
            str(report_a),
            "--benchmark-report",
            str(report_b),
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "benchmark-trend-report"
    assert payload["benchmark_count"] == 2
    assert payload["dataset_row_count_summary"]["total"] == 240
    assert (output_dir / "benchmark_trend_report.md").exists()
    assert (output_dir / "benchmark_trend_report.json").exists()
    assert (output_dir / "benchmark_trend_metrics.csv").exists()
    assert (output_dir / "benchmark_trend_winners.csv").exists()


def test_cli_benchmark_trend_report_discovery(tmp_path, capsys):
    report_a = tmp_path / "seed_1" / "benchmark_report.json"
    report_b = tmp_path / "seed_2" / "benchmark_report.json"
    _write_benchmark_report(report_a)
    _write_benchmark_report(report_b)

    exit_code = main(
        [
            "benchmark-trend-report",
            "--benchmark-dir",
            str(tmp_path),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["benchmark_count"] == 2


def test_cli_benchmark_trend_report_markdown(tmp_path, capsys):
    report_path = tmp_path / "benchmark_report.json"
    _write_benchmark_report(report_path)

    exit_code = main(
        [
            "benchmark-trend-report",
            "--benchmark-report",
            str(report_path),
            "--markdown",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Synthetic Benchmark Trend Report - Advisory Only" in captured.out


def test_cli_benchmark_trend_report_csv(tmp_path, capsys):
    report_path = tmp_path / "benchmark_report.json"
    _write_benchmark_report(report_path)

    exit_code = main(
        [
            "benchmark-trend-report",
            "--benchmark-report",
            str(report_path),
            "--csv",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "row_type,model,metric,count,mean,min,max,std,missing_count" in captured.out
    assert "metric,baseline,accuracy" in captured.out
    assert (
        "row_type,metric,baseline_win_count,neural_win_count,tie_count,missing_count"
        in captured.out
    )
