# Engineering Workflow Commands

## Basic Readiness Commands

```bash
python -m sp63_core validate --golden
python -m sp63_core materials-audit --json
python -m sp63_core manual-cases --json
python -m sp63_core engineering-workflow-self-check --output-dir reports/workflow_self_check --json
python -m sp63_core engineering-workflow --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/engineering_workflow_smoke --json
```

## Deterministic Workflow Without ZIP

```bash
python -m sp63_core engineering-workflow \
  --input-json docs/reports/examples/rectangular_design_input_example.json \
  --output-dir reports/engineering_workflow_nozip_smoke \
  --no-zip \
  --json
```

## Optional Advisory ML Readiness

```bash
python -m sp63_core engineering-workflow \
  --input-json docs/reports/examples/rectangular_design_input_example.json \
  --output-dir reports/engineering_workflow_ml_smoke \
  --include-ml-readiness \
  --dataset reports/synthetic_dataset_smoke.jsonl \
  --external-validation-csv tests/fixtures/external_validation_sample.csv \
  --material-verification-csv tests/fixtures/material_verification_sample.csv \
  --json
```

ML readiness is advisory-only. `ml_ready_for_project_use` must remain false.
