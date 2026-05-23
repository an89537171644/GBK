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
- `h0`;
- `M`;
- `Q`;
- ordinal codes for `concrete_class`, `rebar_class`, and `stirrup_class`;
- binary `load_duration`;
- `geometry_stirrup_diameter`.

Selected reinforcement, status values, and utilization values are not used as
input features when they are targets.

## Targets

The baseline models predict draft dataset targets:

- `As_provided`;
- `main_bar_count`;
- `main_bar_diameter`;
- `stirrup_diameter`;
- `stirrup_legs`;
- `stirrup_spacing`;
- `bending_utilization`;
- `shear_utilization`.

## Models And Metrics

The baseline uses RandomForest models:

- regressors for `As_provided`, `bending_utilization`, and `shear_utilization`;
- classifiers for bar diameter/count and stirrup diameter/legs/spacing.

Reported metrics include:

- `As_MAE`;
- `As_MAPE`;
- `bending_utilization_MAE`;
- `shear_utilization_MAE`;
- classification accuracy for main bar diameter/count and stirrup
  diameter/spacing.

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
  --dataset data/generated/dataset_v001.csv \
  --model-output models/baseline_model.pkl \
  --metrics-output reports/interim/baseline_metrics.json \
  --json
```

The CLI always prints:

```text
Baseline ML is experimental and advisory only. Deterministic SP63 checks remain mandatory.
```

## Safety Wrapper

`check_ml_prediction_safety()` is a draft K12 safety wrapper. It reconstructs a
`RectangularDesignInput` from the original dataset row and runs
`design_rectangular_element()`. For K12 it accepts an ML proposal only when the
deterministic design status is `pass`.

This is intentionally conservative and incomplete. It does not yet reconstruct
or verify the exact predicted reinforcement scheme.

## Limits

- beam-only dataset MVP;
- strength-only checks;
- no cracks;
- no deflections;
- no slabs, columns, T-sections, punching, torsion, anchorage, support zones, or
  bar curtailment;
- deterministic checks and external validation gates remain mandatory.
