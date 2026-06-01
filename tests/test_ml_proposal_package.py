import json

from sp63_core.cli import main
from sp63_core.dataset import export_dataset_from_report_archive
from sp63_core.ml.report_neural_safety_audit import (
    EXTERNAL_VALIDATION_WARNING,
    MATERIAL_VERIFICATION_WARNING,
    PREDICTION_MISMATCH_WARNING,
    SMALL_DATASET_WARNING,
    NeuralAdvisorySafetyAuditResult,
)
from sp63_core.ml.report_proposal_package import (
    ML_OUTPUT_NOT_DESIGN_DECISION,
    build_ml_proposal_package,
)

BATCH_EXAMPLES_DIR = "docs/reports/examples/batch"
INPUT_JSON = "docs/reports/examples/rectangular_design_input_example.json"


def _write_batch_archive(output_dir) -> int:
    return main(
        [
            "design-report-batch",
            "--input-dir",
            BATCH_EXAMPLES_DIR,
            "--output-dir",
            str(output_dir),
        ]
    )


def _write_batch_dataset(tmp_path, *, output_format="jsonl"):
    source_dir = tmp_path / "batch_bundle"
    suffix = "csv" if output_format == "csv" else output_format
    output_path = tmp_path / f"batch_dataset.{suffix}"
    assert _write_batch_archive(source_dir) == 0
    result = export_dataset_from_report_archive(
        source_path=source_dir,
        output_path=output_path,
        output_format=output_format,
    )
    assert result.status == "pass"
    return output_path


def _fake_audit(**overrides):
    values = {
        "status": "pass",
        "audit_status": "pass",
        "source_dataset": "dataset.jsonl",
        "input_json_path": INPUT_JSON,
        "target": "overall_status",
        "feature_mode": "input_only",
        "predicted_status": "pass",
        "prediction_confidence": 0.91,
        "deterministic_strength_status": "pass",
        "deterministic_serviceability_status": "pass",
        "deterministic_overall_status": "pass",
        "prediction_matches_deterministic": True,
        "advisory_signal_usable": True,
        "rejection_reasons": (),
        "warnings": (),
        "errors": (),
        "markdown": "fake",
        "json_data": {
            "class_probabilities": {
                "fail": 0.04,
                "pass": 0.91,
                "review_or_fail": 0.05,
            }
        },
        "neural_network_used": True,
    }
    values.update(overrides)
    return NeuralAdvisorySafetyAuditResult(**values)


def test_ml_proposal_package_builds_from_jsonl(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_ml_proposal_package(
        dataset_path=dataset_path,
        input_json_path=INPUT_JSON,
        max_iter=50,
    )

    assert result.status in {"review_required", "fail"}
    assert result.proposal_status in {"review_required", "rejected"}
    assert result.predicted_status in {"fail", "pass", "review_or_fail"}
    assert result.deterministic_strength_status == "pass"
    assert result.deterministic_serviceability_status == "pass"
    assert result.deterministic_overall_status == "pass"
    assert isinstance(result.advisory_signal_usable, bool)
    assert result.safety_audit_status in {"review_required", "fail"}
    assert result.json_data["class_probabilities"]
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.deterministic_report_required is True
    assert result.requires_engineer_review is True


def test_ml_proposal_package_builds_from_csv(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path, output_format="csv")

    result = build_ml_proposal_package(
        dataset_path=dataset_path,
        dataset_format="csv",
        input_json_path=INPUT_JSON,
        max_iter=50,
    )

    assert result.source_dataset == str(dataset_path)
    assert result.predicted_status in {"fail", "pass", "review_or_fail"}
    assert "class_probabilities" in result.json_data


def test_ml_proposal_package_accepts_only_advisory_match(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "sp63_core.ml.report_proposal_package.build_neural_advisory_safety_audit",
        lambda **_kwargs: _fake_audit(),
    )

    result = build_ml_proposal_package(
        dataset_path=tmp_path / "dataset.jsonl",
        input_json_path=tmp_path / "input.json",
    )

    assert result.status == "pass"
    assert result.proposal_status == "accepted"
    assert result.proposal_accepted is True
    assert result.proposal_rejected is False
    assert result.proposal_requires_review is False
    assert result.advisory_signal_usable is True
    assert ML_OUTPUT_NOT_DESIGN_DECISION in result.warnings


def test_ml_proposal_package_reviews_match_with_missing_evidence(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "sp63_core.ml.report_proposal_package.build_neural_advisory_safety_audit",
        lambda **_kwargs: _fake_audit(
            status="review_required",
            audit_status="review_required",
            warnings=(
                SMALL_DATASET_WARNING,
                MATERIAL_VERIFICATION_WARNING,
                EXTERNAL_VALIDATION_WARNING,
            ),
        ),
    )

    result = build_ml_proposal_package(
        dataset_path=tmp_path / "dataset.jsonl",
        input_json_path=tmp_path / "input.json",
    )

    assert result.status == "review_required"
    assert result.proposal_status == "review_required"
    assert result.proposal_requires_review is True
    assert "dataset is too small for reliable ML proposal" in result.rejection_reasons
    assert "material verification is not provided" in result.rejection_reasons
    assert "external validation is not provided" in result.rejection_reasons


def test_ml_proposal_package_rejects_prediction_mismatch(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "sp63_core.ml.report_proposal_package.build_neural_advisory_safety_audit",
        lambda **_kwargs: _fake_audit(
            status="fail",
            audit_status="fail",
            predicted_status="fail",
            prediction_confidence=0.97,
            prediction_matches_deterministic=False,
            advisory_signal_usable=False,
            warnings=(PREDICTION_MISMATCH_WARNING,),
            rejection_reasons=(PREDICTION_MISMATCH_WARNING,),
        ),
    )

    result = build_ml_proposal_package(
        dataset_path=tmp_path / "dataset.jsonl",
        input_json_path=tmp_path / "input.json",
    )

    assert result.status == "fail"
    assert result.proposal_status == "rejected"
    assert result.proposal_rejected is True
    assert any("differs from deterministic" in reason for reason in result.rejection_reasons)


def test_ml_proposal_package_rejects_deterministic_fail(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "sp63_core.ml.report_proposal_package.build_neural_advisory_safety_audit",
        lambda **_kwargs: _fake_audit(
            status="fail",
            audit_status="fail",
            predicted_status="fail",
            deterministic_strength_status="fail",
            deterministic_serviceability_status="not_checked",
            deterministic_overall_status="fail",
            prediction_matches_deterministic=True,
            advisory_signal_usable=False,
        ),
    )

    result = build_ml_proposal_package(
        dataset_path=tmp_path / "dataset.jsonl",
        input_json_path=tmp_path / "input.json",
    )

    assert result.status == "fail"
    assert result.proposal_status == "rejected"
    assert "deterministic SP63 result is fail" in result.rejection_reasons


def test_ml_proposal_package_deterministic_derived_warns(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_ml_proposal_package(
        dataset_path=dataset_path,
        input_json_path=INPUT_JSON,
        feature_mode="deterministic_derived",
        max_iter=50,
    )

    assert result.feature_mode == "deterministic_derived"
    assert any(
        "deterministic-derived features may leak design decisions" in warning
        for warning in result.warnings
    )


def test_ml_proposal_package_markdown_contains_required_title(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_ml_proposal_package(
        dataset_path=dataset_path,
        input_json_path=INPUT_JSON,
        max_iter=50,
    )

    assert "ML Proposal Package — Advisory Only" in result.markdown
    assert "Deterministic SP63 verification" in result.markdown
    assert "Proposal decision" in result.markdown


def test_cli_ml_proposal_package_json_output(tmp_path, capsys):
    dataset_path = _write_batch_dataset(tmp_path)
    capsys.readouterr()

    exit_code = main(
        [
            "ml-proposal-package",
            "--dataset",
            str(dataset_path),
            "--input-json",
            INPUT_JSON,
            "--max-iter",
            "50",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "ml-proposal-package"
    assert payload["report_type"] == "ml_proposal_package"
    assert payload["deterministic_overall_status"] == "pass"
    assert "class_probabilities" in payload
    assert payload["ml_is_advisory_only"] is True
    assert payload["deterministic_checks_required"] is True
    assert payload["requires_engineer_review"] is True


def test_cli_ml_proposal_package_markdown_output(tmp_path, capsys):
    dataset_path = _write_batch_dataset(tmp_path)
    capsys.readouterr()

    exit_code = main(
        [
            "ml-proposal-package",
            "--dataset",
            str(dataset_path),
            "--input-json",
            INPUT_JSON,
            "--max-iter",
            "50",
            "--markdown",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "ML Proposal Package — Advisory Only" in output
    assert "Proposal decision" in output


def test_cli_ml_proposal_package_output_file(tmp_path, capsys):
    dataset_path = _write_batch_dataset(tmp_path)
    output_path = tmp_path / "ml_proposal_package.md"
    capsys.readouterr()

    exit_code = main(
        [
            "ml-proposal-package",
            "--dataset",
            str(dataset_path),
            "--input-json",
            INPUT_JSON,
            "--max-iter",
            "50",
            "--markdown",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    assert "ML Proposal Package — Advisory Only" in output_path.read_text(encoding="utf-8")
