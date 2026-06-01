# Synthetic report dataset generation

requires_engineer_review = true

## Purpose

K52 adds a reproducible generator for synthetic `input.json` cases used by the
report-derived dataset pipeline.

The workflow is:

```bash
python -m sp63_core synthetic-report-inputs --output-dir reports/synthetic_inputs --case-count 300 --seed 42 --json
python -m sp63_core design-report-batch --input-dir reports/synthetic_inputs --output-dir reports/synthetic_batch_reports --json
python -m sp63_core report-archive-validate --path reports/synthetic_batch_reports --batch --json
python -m sp63_core report-dataset-export --path reports/synthetic_batch_reports --batch --output reports/synthetic_report_dataset.jsonl --json
python -m sp63_core report-dataset-quality --dataset reports/synthetic_report_dataset.jsonl --json
python -m sp63_core report-dataset-features --dataset reports/synthetic_report_dataset.jsonl --json
python -m sp63_core report-ml-baseline --dataset reports/synthetic_report_dataset.jsonl --json
python -m sp63_core report-neural-surrogate --dataset reports/synthetic_report_dataset.jsonl --json
```

## Command

```bash
python -m sp63_core synthetic-report-inputs \
  --output-dir reports/synthetic_inputs \
  --case-count 300 \
  --seed 42 \
  --json
```

Options:

- `--case-count` controls the number of generated `case_*.json` files;
- `--seed` makes generation reproducible;
- `--no-serviceability` omits `Mser`, `span`, and serviceability check flags.

## Generated Files

The output directory contains:

- `case_0001.json`, `case_0002.json`, and so on;
- `README_SYNTHETIC.md`;
- `synthetic_manifest.json`.

The manifest records:

- generator name;
- case count;
- seed;
- advisory and engineer-review flags;
- per-case relative path;
- per-case SHA256;
- input summary.

## Synthetic Ranges

Generated cases use anonymized public synthetic values:

- section width `b`: 200-500 mm;
- section height `h`: 300-900 mm;
- cover: 25-50 mm;
- concrete: B20, B25, B30, B35;
- longitudinal reinforcement: A400, A500;
- stirrup reinforcement: A240, A400;
- moment: 20-500 kN*m converted to N*mm;
- shear: 20-300 kN converted to N;
- service moment: 0.3-0.8 of moment;
- span: 3000-9000 mm.

## Safety Notes

Synthetic data does not replace external validation.

The generated inputs are intended only for ML smoke experiments and pipeline
testing. They are not project design data, not SCAD/LIRA data, and not evidence
that the calculation core is certified.

ML remains advisory-only. Deterministic SP63 checks remain mandatory. Material
verification and external validation remain separate engineering gates.

Large generated report archives should not be committed to the repository.

## K53 Balance Gate

After exporting JSONL or CSV rows, check target balance and stratified split
readiness with:

```bash
python -m sp63_core synthetic-dataset-balance --dataset reports/synthetic_report_dataset.jsonl --json
python -m sp63_core synthetic-dataset-balance --dataset reports/synthetic_report_dataset.csv --format csv --json
```

The balance gate reports target distribution, required `overall_status`
classes, class imbalance, split counts, leakage-like audit columns, warnings,
and generation recommendations. It is still synthetic-only and requires
engineer review.

## K54 Guided Synthetic Balancing

K54 adds guided generation toward a target status distribution:

```bash
python -m sp63_core guided-synthetic-inputs --output-dir reports/guided_synthetic_inputs --target-pass 50 --target-fail 50 --target-review 50 --seed 42 --max-attempts 3000 --json
```

The generator evaluates candidates through deterministic SP63 draft design
results and accepts only cases that help fill the requested `overall_status`
distribution. ML does not guide generation.
