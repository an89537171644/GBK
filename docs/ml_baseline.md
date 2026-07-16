# K12 Baseline ML Sandbox

requires_engineer_review = true

## Purpose

K12 adds an experimental baseline ML sandbox for the beam-only strength dataset.
The ML module is not a calculation engine and is not an acceptance authority.
Every ML suggestion must be checked by the deterministic `sp63_core`
calculation workflow.

## Input Features

The baseline feature extractor uses only input-like dataset fields:

- `b`;
- `h`;
- `cover`;
- `M`;
- `Q`;
- ordinal codes for `concrete_class`, `rebar_class`, and `stirrup_class`;
- binary `load_duration`;
- `geometry_stirrup_diameter`.

K12.1 explicitly removes `h0` from ML input features because effective depth
depends on the selected main bar diameter, which is an ML target. Keeping `h0`
as a feature would leak target information into training.

Selected reinforcement, status values, and utilization values are not used as
input features when they are targets.

## Targets

The baseline models predict draft dataset targets:

- `As_provided`;
- `main_bar_count`;
- `main_bar_diameter`;
- `stirrup_legs`;
- `stirrup_spacing`;
- `bending_utilization`;
- `shear_utilization`.

## Models And Metrics

The baseline uses RandomForest models:

- regressors for `As_provided`, `bending_utilization`, and `shear_utilization`;
- classifiers for bar diameter/count and stirrup legs/spacing.

Reported metrics include:

- `As_MAE`;
- `As_MAPE`;
- `bending_utilization_MAE`;
- `shear_utilization_MAE`;
- classification accuracy for main bar diameter/count and stirrup legs/spacing;
- `feature_count` and `target_count`.

K12.1 also reports deterministic safety metrics:

- `total_predictions`;
- `deterministic_accept_rate`;
- `unsafe_prediction_rate`;
- `bending_fail_rate`;
- `shear_fail_rate`;
- `layout_fail_rate`;
- `constructive_fail_rate`.

## K12.2 Target Hygiene

K12.2 removes the remaining target leakage in the MVP ML setup:

- `h0` remains excluded from ML input features because it leaks selected main
  bar diameter;
- `cover` remains an input geometry feature;
- `geometry_stirrup_diameter` remains an input geometry parameter;
- `stirrup_diameter` is no longer an ML target because in the current dataset
  MVP it is equal to `geometry_stirrup_diameter`;
- ML proposals use `geometry_stirrup_diameter` as the stirrup diameter unless an
  old prediction still contains `stirrup_diameter`, in which case a deprecation
  warning is emitted.

Models saved before K12.2 must be retrained. Backward compatibility for old
pickle files with a `stirrup_diameter` model is not guaranteed.

## CLI

Train a generated-data baseline:

```bash
python -m sp63_core train-baseline \
  --generate-dataset-limit 500 \
  --model-output models/baseline_model.pkl \
  --metrics-output reports/interim/baseline_metrics.json \
  --seed 42
```

Train from an existing dataset CSV:

```bash
python -m sp63_core train-baseline \
  --dataset data/generated/dataset_v003.csv \
  --model-output models/baseline_model.pkl \
  --metrics-output reports/interim/baseline_metrics.json \
  --json
```

The CLI always prints:

```text
Baseline ML is experimental and advisory only. Deterministic SP63 checks remain mandatory.
```

## Safety Wrapper

K12.1 reconstructs an explicit `MLReinforcementProposal` from baseline
predictions:

- main bar count;
- main bar diameter;
- stirrup diameter;
- stirrup legs;
- stirrup spacing.

Non-catalog values are snapped to the nearest supported MVP value with warnings.
`check_ml_proposal_safety()` then checks the exact proposed scheme through the
deterministic core:

- single-layer layout;
- longitudinal constructive check;
- bending check;
- shear check;
- transverse constructive check.

The proposal is accepted only when all deterministic checks pass and shear-rule
warnings do not block counting transverse reinforcement.

`check_ml_prediction_safety()` remains as a backward-compatible wrapper around
proposal reconstruction and `check_ml_proposal_safety()`.

The CLI prints:

```text
ML predictions are not accepted unless deterministic safety check passes.
```

## ML Quality Gate

K12.2 adds `evaluate_ml_quality_gate()` for sandbox training output.

Default thresholds:

- `max_unsafe_prediction_rate = 0.0`;
- `min_deterministic_accept_rate = 0.95`;
- `max_As_MAPE = 15.0`.

`pass` means only that the experimental sandbox model passed the configured
quality gate. It does not approve engineering use. `warning` or `fail` means the
model must remain sandbox-only and should not be used even as advisory output
without review.

## Limits

- beam-only dataset MVP;
- strength-only checks;
- no cracks;
- no deflections;
- no slabs, columns, T-sections, punching, torsion, anchorage, support zones, or
  bar curtailment;
- deterministic checks and external validation gates remain mandatory.
