# Guided synthetic generation for class balancing

requires_engineer_review = true

## Purpose

K54 adds deterministic-guided synthetic input generation for report-derived ML
smoke datasets. It generates candidate `input.json` files, evaluates each
candidate through the deterministic SP63 draft design pipeline, and accepts a
candidate only when its deterministic `overall_status` helps reach the target
distribution.

The default target distribution is:

```json
{
  "pass": 50,
  "fail": 50,
  "review_or_fail": 50
}
```

This is synthetic data only. It is not external validation and not project
design data.

## Command

```bash
python -m sp63_core guided-synthetic-inputs \
  --output-dir reports/guided_synthetic_inputs \
  --target-pass 50 \
  --target-fail 50 \
  --target-review 50 \
  --seed 42 \
  --max-attempts 3000 \
  --json
```

Smoke example:

```bash
python -m sp63_core guided-synthetic-inputs \
  --output-dir reports/guided_synthetic_inputs_smoke \
  --target-pass 2 \
  --target-fail 2 \
  --target-review 2 \
  --seed 42 \
  --max-attempts 500 \
  --json
```

Use `--no-serviceability` only when review/serviceability cases are not needed.
If `review_or_fail` is requested without serviceability checks, the generator
returns `review_required` when the target cannot be reached.

## Output

The output directory contains:

- `case_0001.json`, `case_0002.json`, and so on;
- `README_GUIDED_SYNTHETIC.md`;
- `guided_synthetic_manifest.json`.

The manifest records:

- generator name;
- target distribution goal;
- final distribution;
- seed;
- max attempts;
- generated, accepted, and rejected counts;
- advisory and engineer-review flags;
- each accepted case path, SHA256, deterministic `overall_status`, desired
  status, attempt number, and input summary.

## Guided Logic

The generator uses simple deterministic heuristics:

- pass candidates use larger sections, moderate loads, moderate spans, and
  stronger materials;
- fail candidates use smaller sections and high moment/shear levels;
- review candidates enable crack formation while omitting crack-width and
  deflection checks so deterministic serviceability review can be triggered.

Every candidate is classified by deterministic SP63 draft design results. ML is
not used to accept candidates and does not guide generation.

## Pipeline

After generating inputs:

```bash
python -m sp63_core design-report-batch --input-dir reports/guided_synthetic_inputs --output-dir reports/guided_synthetic_reports --json
python -m sp63_core report-dataset-export --path reports/guided_synthetic_reports --batch --output reports/guided_synthetic_dataset.jsonl --json
python -m sp63_core synthetic-dataset-balance --dataset reports/guided_synthetic_dataset.jsonl --json
```

The report batch reader ignores `guided_synthetic_manifest.json`, so the guided
input folder can be passed directly to `design-report-batch`.

## Safety Notes

- Guided synthetic data is synthetic-only.
- Guided synthetic data is not external validation.
- Material verification remains separate.
- External validation remains separate.
- ML remains advisory-only.
- Deterministic SP63 checks remain mandatory.
- Engineer review is required.
- Large generated reports and datasets should not be committed.
- Full SP 63 text, private SCAD/LIRA files, personal data, and grant documents
  are not part of this workflow.
