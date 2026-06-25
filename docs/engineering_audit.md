# Engineering Audit

requires_engineer_review = true

## Implemented

- Draft material catalogs for heavy concrete B15-B40 and reinforcement A240/A400/A500.
- Rectangular section geometry with effective depth handling.
- Draft bending check for rectangular sections.
- Draft shear check for rectangular sections.
- Longitudinal reinforcement selection with layout and constructive filters.
- Transverse reinforcement selection with shear and constructive filters.
- K7 draft warnings for conditions of counting transverse reinforcement in shear.
- K8 hardened dataset generation with consistent stirrup geometry, deterministic
  shuffled limits, group split, and extended dataset reports.
- K9 validation package for draft golden cases, dataset checks, and SCAD/LIRA
  comparison template.
- K10 external validation structures and acceptance gates for manual SCAD/LIRA
  review.
- K11 strict loading of filled SCAD/LIRA comparisons, delta export, and strict
  acceptance report.
- K12 experimental baseline ML sandbox for beam-only strength dataset.
- K12.1 leakage removal and deterministic safety checks for reconstructed ML
  reinforcement proposals.
- K12.2 target hygiene removing `stirrup_diameter` prediction and adding an ML
  sandbox quality gate.
- K13 service concrete properties `Rbser` and `Rbtser` for future second
  limit-state preparation.
- K15 draft normal crack width `acrc` check for rectangular beams.
- K16 draft short-term curvature and deflection check for rectangular beams.
- K17 separated strength, serviceability, and overall protocol statuses.
- End-to-end rectangular element design workflow.
- CLI scenarios for checks, selection, design, and dataset generation.

## Applicability Boundaries

- Rectangular bending elements only.
- Heavy concrete and MVP reinforcement classes only.
- Units follow the project convention: N, mm, MPa.
- Results are draft engineering outputs and require review before production use.

## Requires Engineering Review

- Material values and load-duration assumptions.
- Bending and shear formula cards and golden cases.
- Constructive limits and edge cases.
- Reinforcement layout assumptions.
- Dataset ranges before bulk generation.
- Dataset reports, group split behavior, and golden cases before ML work.
- K9 validation reports before any baseline ML training.
- External SCAD/LIRA comparison rows and acceptance gates before ML is treated
  as more than experimental.
- Filled external CSV with strict pass status before baseline ML proceeds beyond
  an experimental sandbox.

## Not Implemented

- Long-term deflections and other refined serviceability checks beyond draft
  normal crack formation, draft normal crack width, and draft short-term
  deflection.
- T-sections, columns, punching, torsion, prestress, anchorage, support zones,
  and bar curtailment.
- HTML/PDF protocol rendering.
- Production ML-backed recommendations.
- Streamlit or other UI.

## Why ML Is Not A Final Calculation Stage Yet

The deterministic calculation core is still draft and requires engineering review.
ML can only be used after the calculation rules, constructive filters, datasets,
and validation cases are reviewed. Even then, ML output must remain advisory and
must be checked by deterministic SP 63 calculation modules.

K7 strengthens the shear check by reporting draft Qsw-counting conditions. This
does not make ML acceptable as a final stage; deterministic checks and manual
engineering review are still required.

K8 makes the dataset pipeline more stable, but it still does not cover
serviceability data, deflections, T-sections, columns, slabs, punching, torsion,
anchorage, support zones, or bar curtailment. ML may begin only after reviewing
`dataset_report` outputs and manually checking the draft golden cases.

K9 adds automated validation summaries, but this is not certification. The
outputs still require manual engineering review and external comparison.

K10 adds acceptance gates. A `warning` result means external comparison has not
been filled yet; this blocks treating ML as engineering-ready.

K11 requires completed external values and engineer acceptance flags for strict
`pass`. Missing values, rejected rows, or excessive deltas fail acceptance.

K12 introduces a baseline ML sandbox only after the validation-gate structure is
in place. The sandbox is experimental and advisory. It must not be used as a
final calculation stage, and every prediction must be checked by deterministic
SP 63 modules.

K12.1 removes `h0` from ML input features because it leaks selected bar diameter
information. It adds `cover` as the geometry input and checks the reconstructed
ML reinforcement proposal itself through deterministic layout, constructive,
bending, and shear checks. `unsafe_prediction_rate` must be monitored before
any ML use beyond sandbox experiments.

K12.2 treats `geometry_stirrup_diameter` as an input geometry parameter and
removes `stirrup_diameter` from ML targets because they are equal in the current
dataset MVP. The ML quality gate monitors `As_MAPE`,
`deterministic_accept_rate`, and `unsafe_prediction_rate`, but even a passing
gate leaves ML advisory-only.

## K13 Service Concrete Properties

K13 adds `Rbser` and `Rbtser` to the heavy concrete B15-B40 draft catalog. These
properties prepare the core for future second limit-state checks such as normal
crack formation and deflection calculations.

Crack checks and deflection checks are not implemented in K13. ML is not trained
on serviceability data, and the K13 validation still covers the strength MVP
only.

## K14 Normal Crack Formation

K14 adds the first draft serviceability check: normal crack formation `Mcrc` for
rectangular reinforced concrete beams. The implementation uses `Rbtser` and a
gross elastic concrete section.

This is not a crack width or deflection check. It does not include transformed
section behavior, long-term effects, axial force, prestress, slabs, T-sections,
or nonlinear deformation modeling. The result is a draft-MVP signal that crack
width `acrc` must be checked in a later deterministic step when normal cracks
are expected.

## K15 Normal Crack Width

K15 adds a draft normal crack width `acrc` check for rectangular reinforced
concrete beams. The implementation uses service reinforcement property `Rsser`,
a simplified elastic cracked reinforcement stress estimate, and bounded draft
crack spacing.

This is not a refined SP 63 crack width model. It does not include refined crack
spacing, tension stiffening, long-term effects, transformed-section behavior,
or nonlinear deformation modeling. Deflection is still not implemented. ML
modules were not changed and ML remains advisory-only.

## K16 Curvature And Deflection

K16 adds a draft short-term curvature and deflection check for rectangular
reinforced concrete beams. The implementation uses K14 crack formation to
select gross uncracked stiffness or a simplified cracked transformed stiffness
without tensile concrete.

This is not a refined SP 63 deformation model. It does not include long-term
deflection, creep, shrinkage, refined tension stiffening, nonlinear deformation,
slabs, columns, T-sections, punching, torsion, anchorage, support zones, bar
curtailment, or Streamlit. ML modules were not changed and ML remains
advisory-only.

## K17 Status Separation

K17 separates calculation protocol statuses into `strength_status`,
`serviceability_status`, and `overall_status`. Strength status is based only on
bending and shear. Serviceability status is based on crack formation, crack
width, and deflection. The legacy `status` field remains as an alias for
`overall_status`.

This change does not alter bending, shear, crack formation, crack width, or
deflection formulas. It makes serviceability failures visible in the final
design status instead of allowing a passed strength result to mask them. ML
modules were not changed and ML remains advisory-only.

## K19 Material Catalog Audit

K19 adds a transparent audit layer for the concrete and reinforcement catalogs.
The audit report lists current draft values, their usage in strength or
serviceability checks, units, and review flags.

All material values remain `draft_requires_engineer_review`. The audit does not
approve normative values and does not store full SP 63 text. An engineer must
verify concrete `Rb`, `Rbt`, `Rbser`, `Rbtser`, `Eb` and reinforcement `Rsn`,
`Rs`, `Rsser`, `Rsc_short`, `Rsc_long`, `Rsw`, `Es` against the applicable
tables before final use.

K19 does not change calculation formulas, ML modules, dataset generation, or
external validation gates. ML remains advisory-only and deterministic SP 63
checks remain mandatory.

## K20 Manual SP63 Verification Cases

K20 adds six manual verification cases as a repeatable check against the
deterministic draft calculation core. The cases cover a passing beam, bending
failure, crack-formation review without crack width, crack-width failure,
deflection failure, and shear failure.

The verification package compares program values with manual expected values
using documented tolerances and checks separated `strength_status`,
`serviceability_status`, and `overall_status` values.

K20 does not change calculation formulas, material values, ML modules, dataset
generation, or external validation. The cases are draft verification material
and still require engineer review.

## K21 Dataset Enrichment

K21 enriches the beam-only dataset with deterministic strength and draft
serviceability outputs from the calculation core. Rows now expose selected
reinforcement areas, bending and shear capacities, Mcrc, crack width,
deflection, separated strength/serviceability/overall statuses, warning counts,
review flags, and an `unsafe_row` marker.

This improves ML-readiness diagnostics, but it does not approve the dataset for
final design use. The generated values still depend on draft serviceability
checks and material catalogs that require engineer review. ML remains
advisory-only and every ML proposal must continue to pass deterministic checks.

## K22 ML Readiness Gate

K22 adds an ML readiness report for enriched deterministic datasets. The report
checks required columns, unsafe row counts, status distributions, group leakage,
and constant target/status columns before any later ML work.

This is a gate, not training. A safe accepted dataset with only passing rows is
useful, but it is not sufficient for classification over pass/fail/review
statuses. Fail and review diagnostic cases must be added deliberately in a
future dataset step before classification ML. ML remains advisory-only and
deterministic SP63 checks remain mandatory.

## K23 Diagnostic Dataset

K23 adds that separate diagnostic/candidate dataset. It intentionally contains
passing, failing, and review-required rows generated through deterministic
checks. The safe accepted dataset remains unchanged and should still be used for
accepted-row regression experiments.

The diagnostic dataset is not a project-design dataset. It exists to make
future classification ML development possible after engineer review. Rows with
failure and review statuses must not be interpreted as approved reinforcement
solutions. ML remains advisory-only.

## K24 Baseline ML Without Neural Network

K24 adds a non-neural baseline ML report for engineering review of dataset
readiness. It uses simple sklearn baselines for regression on the safe accepted
dataset and classification of `overall_status` on the diagnostic dataset.

The report does not make ML a calculator and does not train a neural network.
It explicitly records that ML is advisory-only and deterministic SP63 checks
remain mandatory. The diagnostic dataset is intentionally small, so
classification metrics are smoke metrics rather than evidence of production ML
quality.

## K25 Expanded Diagnostic Dataset

K25 expands the diagnostic/candidate dataset while keeping the safe accepted
dataset separate. The diagnostic set now includes generated deterministic rows
for pass, bending failure, shear failure, crack-width failure, deflection
failure, crack-review, and multiple-failure scenarios.

This improves classification readiness diagnostics, but it does not create a
design dataset and does not approve any failing or review-required rows as
solutions. Every diagnostic row still requires engineer review. ML remains
advisory-only and deterministic SP63 checks remain mandatory.

## K26 Baseline ML Evaluation on Expanded Diagnostic Dataset

K26 extends the non-neural baseline report to evaluate `overall_status`
classification on the expanded K25 diagnostic dataset with a fixed train/test
split. The report includes accuracy, macro F1, per-class precision and recall,
confusion matrix, and class distribution.

The report separates `input_only_features` from
`deterministic_derived_features`. The derived feature mode is review-only
because deterministic outputs such as capacities, crack width, and deflection
can leak calculation outcomes into a classifier. No neural network is added,
and the metrics do not authorize project use of ML. Deterministic SP63 checks
remain mandatory.

## K27 Scalable Diagnostic Dataset and Leakage-Safe Splits

K27 adds `group_key` to diagnostic rows and uses it for leakage-safe
diagnostic train/test splits. The group key is based on rectangular beam
geometry and material classes so similar variants of one section/material family
are kept on one side of the split.

The expanded diagnostic dataset can be generated at 1000 rows for ML-readiness
review. It still contains intentional fail and review cases and is not a set of
approved design solutions. Deterministic-derived ML features remain marked as
potential leakage, and no neural network is added.

## K28 Group-Diverse Diagnostic Dataset

K28 increases diagnostic group diversity by expanding geometry, cover,
material, load, span, and reinforcement-family combinations. The diagnostic
`group_key` now captures more engineering context than geometry/materials
alone, including diagnostic case type, load family, and reinforcement family.

The target review signal is `diagnostic-dataset --limit 5000 --json` with at
least 50 unique groups and `group_leakage_count = 0`. `ml-readiness
--diagnostic --json` and `ml-baseline --diagnostic-limit 1000 --json` expose
the same group-split safety indicators.

K28 does not change deterministic formulas or material values, does not add a
neural network, and does not make ML a design checker. The diagnostic dataset
remains an engineer-review artifact and is not a set of approved project
solutions.

## K29 Neural Surrogate Smoke MVP

K29 introduces the first neural-network smoke surrogate using scikit-learn
`MLPClassifier` and `MLPRegressor`. This is explicitly advisory-only and is not
a calculation module. It does not change deterministic SP63 formulas, material
catalogs, validation gates, or external validation workflow.

The neural surrogate report warns that it must not be used as a design checker,
that all ML predictions require deterministic SP63 verification, that the
diagnostic dataset is synthetic and engineer-review material, and that the
metrics are not production evidence.

Before any broader neural-network work, the project still needs engineering
review of diagnostic distributions, deterministic validation, external
validation, and ML safety policy.

## K30 ML Proposal Safety Wrapper

K30 adds a deterministic safety wrapper for advisory ML and neural-surrogate
reinforcement proposals. The wrapper rebuilds the proposed rectangular
reinforcement scheme and runs the deterministic SP63 draft checks before any
proposal can be accepted.

Acceptance requires deterministic strength status `pass`, serviceability status
`pass` or `not_checked`, and overall status `pass`. Proposals producing
`fail` or `review_or_fail` are rejected and include rejection reasons.

This step does not change formulas or material values. It reinforces the
project rule that ML is advisory-only, deterministic SP63 verification is
mandatory, and engineer review remains required even for accepted proposals.

## K31 External Validation Workflow

K31 prepares the external engineering validation workflow for comparing
`sp63_core` draft-MVP outputs with independent manual, SCAD, LIRA, or
engineer-maintained Excel results.

The step adds a public CSV template and summary report only. It does not add
closed external model files, personal documents, full normative text, or any
formula changes. External values must be filled and accepted by an engineer
before the draft-MVP can be treated as externally validated.

ML and neural surrogate modules remain advisory-only. They do not replace the
external validation workflow or deterministic SP63 checks.

## K32 External Validation Filled Sample

K32 adds a public synthetic/manual filled external validation sample aligned
with the six K20 manual verification cases. The sample checks the reporting
pipeline from program values to external/manual values, deltas,
`acceptance_status`, and summary status.

The sample is not real SCAD or LIRA evidence and does not certify the
calculation core. It uses draft acceptance tolerances for bending, shear, Mcrc,
crack width, and deflection deltas. Real external values must still be filled
and accepted by an engineer before external validation can be considered
complete.

## K33 External Validation Real-Data Gate

K33 adds strict intake checks for real engineer-filled external validation CSV
files. The step does not add real SCAD/LIRA files and does not invent external
values. It prepares validation logic for data entered by an engineer.

Strict mode checks required columns, filled external values, numeric parsing,
computed or provided deltas, tolerance limits, and consistency of
`acceptance_status`. Missing values produce review status, tolerance failures
produce fail status, and contradictory acceptance status is reported.

The engineer checklist and blank CSV template define what can be committed:
only anonymized numeric comparison rows, not closed model files, private
documents, or full normative text. ML remains advisory-only and deterministic
SP63 checks remain mandatory.

## K34 Material Catalog Engineer Verification Gate

K34 adds a verification gate for the material catalog without changing material
values or calculation formulas. The current catalog values remain draft until
an engineer fills a verification CSV or records review notes.

Verification statuses are:

- `draft`;
- `needs_review`;
- `engineer_verified`.

The gate covers concrete `Rb`, `Rbt`, `Rbser`, `Rbtser`, `Eb` and reinforcement
`Rsn`, `Rs`, `Rsser`, `Rsc_short`, `Rsc_long`, `Rsw`, `Es`.

Rows can be accepted as `engineer_verified` only when `engineer_value`,
`engineer_name`, `review_date`, and `source_note` are filled and the engineer
value matches the current catalog value. Otherwise the row remains
`needs_review`.

The CSV and Markdown templates are review aids only. They must not contain full
SP 63 text, private documents, or personal data. ML remains advisory-only and
must not treat material values as final unless deterministic checks and
engineer verification both support the result.

## K35 Material Verification Report Integration

K35 adds a read-only report layer for engineer-filled material verification
CSV files. The command can emit Markdown or JSON summaries and highlights rows
that remain `needs_review`.

The report includes total rows, engineer-verified rows, rows needing review,
and missing required field counts. It does not update concrete or reinforcement
catalog values and does not change formulas.

The report is intended to support engineer review of material values before
they are treated as accepted input data. Full SP 63 text and private documents
must not be stored in the repository.

## K36 Design Calculation Report Export

K36 adds a draft rectangular design calculation report export for the existing
deterministic design workflow. The export can render Markdown, simple static
HTML, or JSON through:

```bash
python -m sp63_core design-report --markdown
python -m sp63_core design-report --html
python -m sp63_core design-report --json
```

The report includes input data, geometry, materials, selected longitudinal and
transverse reinforcement, bending and shear checks, serviceability checks,
separated statuses, warnings, and limitations.

This is a reporting layer only. It does not change formulas, material values,
reinforcement selection, ML behavior, or external validation gates. The report
is not a certified design conclusion, keeps `requires_engineer_review = true`,
and continues to require deterministic SP63 checks, material verification, and
external engineering validation.

## K37 Input-Driven Design Report

K37 extends the report export so an engineer can provide a rectangular beam
input JSON file instead of relying only on the K36 smoke example:

```bash
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --json
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --markdown
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --html
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --bundle-output reports/smoke_case
```

The input layer validates required fields and rejects unknown fields. It then
runs the existing deterministic `design_rectangular_element()` workflow and
renders the same report structures as K36. Bundle output stores `report.md`,
`report.json`, `report.html`, and a copied `input.json` for traceability.

This is still a reporting/input layer only. It does not change deterministic
formulas, material values, reinforcement selection algorithms, ML behavior, or
external validation gates. Reports remain draft review artifacts with
`requires_engineer_review = true`.

## K38 Batch Design Reports

K38 adds a batch reporting layer for several rectangular beam input JSON files:

```bash
python -m sp63_core design-report-batch --input-dir docs/reports/examples/batch --output-dir reports/batch
python -m sp63_core design-report-batch --input-dir docs/reports/examples/batch --output-dir reports/batch --json
```

The command writes `index.md`, `index.json`, and one report bundle per input.
Each valid case bundle contains `report.md`, `report.json`, `report.html`, and
a copied `input.json`. Invalid input files are reported as `input_error` in the
index without stopping the remaining cases.

K38 is a reporting layer only. It does not change deterministic formulas,
material values, reinforcement selection algorithms, ML behavior, or external
validation gates. Batch reports remain draft review artifacts with
`requires_engineer_review = true`.

## K39 Report Bundle Manifest

K39 adds `manifest.json` metadata to single and batch report bundles. The
manifest records generated-at time, command name, input and output artifact
paths, SHA256 checksums, statuses, warnings count, and
`requires_engineer_review = true`.

Batch output includes both a root manifest and case-level manifests. Batch
`index.json` includes manifest paths and checksums for each valid case.

K39 is a traceability layer only. It does not change deterministic formulas,
material values, reinforcement selection algorithms, ML behavior, or external
validation gates. Manifests remain draft review artifacts and do not certify a
project design.

## K40 Report Archive Validation

K40 adds a report archive integrity check for K39 single and batch report
bundles:

```bash
python -m sp63_core report-archive-validate --path reports/smoke_case --json
python -m sp63_core report-archive-validate --path reports/batch_smoke --batch --json
```

The check verifies required files, manifest file records, SHA256 checksums, and
batch `index.json` consistency with case manifests. Missing files and checksum
mismatches return `status = fail`.

K40 is an archive validation layer only. It does not change deterministic
formulas, material values, reinforcement selection algorithms, ML behavior,
neural-network code, UI, or external validation gates. Passing archive
validation still requires engineer review.

## K41 Report Archive ZIP Export

K41 adds ZIP export for validated single and batch report archives:

```bash
python -m sp63_core report-archive-zip --path reports/smoke_case --output reports/smoke_case.zip --json
python -m sp63_core report-archive-zip --path reports/batch_smoke --output reports/batch_smoke.zip --batch --json
```

The export validates the source archive, writes a ZIP with relative paths only,
computes `zip_sha256`, and validates the ZIP for required files and unsafe path
entries.

K41 is a packaging and handoff layer only. It does not change deterministic
formulas, material values, reinforcement selection algorithms, ML behavior,
neural-network code, UI, or external validation gates. ZIP packages remain
draft review artifacts and require engineer review.

## K42 Engineering Review Package README

K42 adds `README_REVIEW.md` to single report bundles and to batch archive
roots. The README explains archive contents, validation commands, ZIP export
commands, reproduction commands, file locations, final statuses, and review
warnings.

The README is included in `manifest.json` checksums and ZIP packages. Archive
validation fails if the expected README is missing.

K42 is a documentation and handoff layer only. It does not change deterministic
formulas, material values, reinforcement selection algorithms, ML behavior,
neural-network code, UI, or external validation gates. ZIP packages and
manifests still do not certify calculations; engineer review remains required.

## K43 Dataset Export From Report Archives

K43 adds `report-dataset-export` for converting validated single and batch
report archives into flat ML-ready rows:

```bash
python -m sp63_core report-dataset-export --path reports/smoke_case --output reports/smoke_dataset.jsonl --json
python -m sp63_core report-dataset-export --path reports/batch_smoke --batch --output reports/batch_dataset.jsonl --json
```

The export reads `report.json`, `input.json`, and `manifest.json` and requires
archive validation by default. It does not rerun deterministic calculations,
does not change formulas, does not train ML, and does not add neural networks.

K43 rows preserve provenance and require engineer review. ML remains
advisory-only, and deterministic SP63 checks remain mandatory.

## K44 Report-Derived Dataset Quality Gate

K44 adds `report-dataset-quality` for checking rows exported by
`report-dataset-export` before any future ML use:

```bash
python -m sp63_core report-dataset-quality --dataset reports/batch_dataset.jsonl --json
python -m sp63_core report-dataset-quality --dataset reports/batch_dataset.csv --format csv --json
```

The gate checks required columns, empty critical values, archive validation
status, provenance, advisory flags, status distribution, and leakage-like
status/check columns. It does not train ML, does not add a neural network, and
does not make ML a calculator.

Rows with `material_verification_status = not_provided` or
`external_validation_status = not_provided` remain review-only. Deterministic
SP63 checks and engineer review remain mandatory.

## K45 Leakage-Safe Report Dataset Features

K45 adds `report-dataset-features` for preparing report-derived feature and
target metadata:

```bash
python -m sp63_core report-dataset-features --dataset reports/batch_dataset.jsonl --json
python -m sp63_core report-dataset-features --dataset reports/batch_dataset.csv --format csv --json
```

The command separates input-only features from target/status/check columns,
reports excluded leakage columns, calculates target distribution, and returns
train/validation/test split counts. The deterministic-derived feature mode
requires review because it may leak design decisions.

K45 does not train ML, does not add a neural network, and does not make ML a
calculator. Deterministic SP63 checks and engineer review remain mandatory.

## K46 Baseline ML on Report-Derived Safe Features

K46 adds `report-ml-baseline` for non-neural classification evaluation on
K45 leakage-safe report-derived feature sets:

```bash
python -m sp63_core report-ml-baseline --dataset reports/batch_dataset.jsonl --json
python -m sp63_core report-ml-baseline --dataset reports/batch_dataset.csv --format csv --json
```

The command reports target distribution, split counts, baseline metrics,
confusion matrix, and excluded leakage columns. The default `input_only` mode
keeps status/check/result columns out of model inputs. The
`deterministic_derived` mode is review-only and warns about possible
design-decision leakage.

K46 does not change formulas, material values, reinforcement selection, report
generation, external validation, or material verification. It does not add a
neural network and does not make ML a calculator. Deterministic SP63 checks and
engineer review remain mandatory.

## K47 Neural Surrogate v2 on Report-Derived Safe Features

K47 adds `report-neural-surrogate` for advisory-only neural surrogate smoke
evaluation on K45 leakage-safe report-derived feature sets:

```bash
python -m sp63_core report-neural-surrogate --dataset reports/batch_dataset.jsonl --json
python -m sp63_core report-neural-surrogate --dataset reports/batch_dataset.csv --format csv --json
```

The command uses scikit-learn MLPClassifier only because scikit-learn is
already used by the project. It does not add PyTorch, TensorFlow, or Keras.
The default `input_only` mode keeps status/check/result columns out of model
inputs. The `deterministic_derived` mode is review-only and warns about
possible design-decision leakage.

K47 does not change formulas, material values, reinforcement selection, report
generation, external validation, or material verification. Neural surrogate is
not a design checker. Deterministic SP63 checks, K30 safety wrapper, and
engineer review remain mandatory for any ML proposal.

## K48 Neural Advisory Prediction with Deterministic Verification

K48 adds `report-neural-predict` for one-input advisory neural prediction with
mandatory deterministic design-report verification:

```bash
python -m sp63_core report-neural-predict --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

The command reads a report-derived dataset, trains a review-only neural
surrogate on K45 leakage-safe features, reads the input JSON, predicts an
advisory status, builds the deterministic SP63 design report for the same input,
and compares the statuses.

K48 does not change formulas, material values, reinforcement selection, report
generation, external validation, or material verification. Neural prediction is
not a design checker. Prediction mismatches require review, and deterministic
SP63 verification remains authoritative.

## K49 Neural Advisory Safety Audit

K49 adds `neural-safety-audit` as a safety-report layer around K48 advisory
prediction. It reuses the K48 prediction and deterministic verification output
instead of adding a parallel ML core.

The audit records predicted status, prediction confidence, class
probabilities, deterministic strength/serviceability/overall statuses,
`prediction_matches_deterministic`, `advisory_signal_usable`, `audit_status`,
warnings, errors, and rejection reasons. Markdown output is available for
engineer review.

A mismatch between neural advisory output and deterministic SP63 status, or a
deterministic `fail` / `review_or_fail`, blocks advisory signal use. Small
datasets, deterministic-derived features, and missing material/external
verification context remain review items.

K49 does not change formulas, material values, reinforcement selection, report
generation, external validation, or material verification. Neural prediction is
not a project decision, K30 safety-wrapper philosophy remains mandatory, and
deterministic SP63 verification remains authoritative.

## K50 ML Proposal Package with Deterministic Safety Wrapper

K50 adds `ml-proposal-package` as a package layer around K48 advisory prediction
and K49 safety audit:

```bash
python -m sp63_core ml-proposal-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
python -m sp63_core ml-proposal-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --markdown
```

The package records predicted status, confidence, class probabilities,
deterministic strength/serviceability/overall statuses,
`prediction_matches_deterministic`, `advisory_signal_usable`,
`safety_audit_status`, `proposal_status`, proposal accept/reject/review flags,
warnings, errors, and rejection/review reasons.

K50 does not change formulas, material values, reinforcement selection, report
generation, external validation, or material verification. It does not make ML
a design checker. Even an accepted package is only an advisory signal and still
requires deterministic SP63 verification and engineer review.

## K51 ML Proposal Engineering Review Package

K51 adds `ml-proposal-review-package` for engineer handoff of one advisory ML
proposal:

```bash
python -m sp63_core ml-proposal-review-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/ml_proposal_review --json
```

The package writes `input.json`, deterministic report MD/JSON/HTML, neural
safety audit MD/JSON, ML proposal package MD/JSON, `README_REVIEW.md`,
`manifest.json`, and optional ZIP archive. The manifest records SHA256 payload
checksums, deterministic statuses, proposal status, prediction match flag,
advisory signal usability, and mandatory review flags.

K51 does not change formulas, material values, reinforcement selection, report
generation, external validation, or material verification. ZIP and manifest
packaging do not certify a design. ML remains advisory-only, deterministic SP63
verification remains mandatory, and engineer review remains required.

## Next Stages

- Engineer review of material catalogs and formula cards.
- Engineer review of constructive checks.
- Dataset split and validation policy.
- Golden-case expansion.
- Baseline ML review only after deterministic checks and external validation
  gates are accepted.
## K52 Synthetic Report Dataset Generation

K52 adds a deterministic generator for synthetic report input JSON cases:

```bash
python -m sp63_core synthetic-report-inputs --output-dir reports/synthetic_inputs --case-count 300 --seed 42 --json
```

The generated cases are anonymous synthetic values for report-derived dataset
and ML smoke experiments. They do not replace external validation, material
verification, or engineer review. The generator does not change calculation
formulas, material values, reinforcement selection, or ML safety rules.

## K53 Synthetic Dataset Balance Readiness

K53 adds `synthetic-dataset-balance` for reviewing synthetic report-derived
datasets before ML smoke evaluation:

```bash
python -m sp63_core synthetic-dataset-balance --dataset reports/synthetic_report_dataset.jsonl --json
python -m sp63_core synthetic-dataset-balance --dataset reports/synthetic_report_dataset.csv --format csv --json
```

The report checks target class distribution, required `overall_status` classes,
minority class counts, imbalance ratio, stratified split feasibility, leakage
column detection, and advisory safety flags. It can write a split-index JSON for
review.

K53 does not change formulas, material values, reinforcement selection, report
generation, external validation, or material verification. Synthetic data
remains synthetic-only, ML remains advisory-only, and deterministic SP63 checks
remain mandatory.

## K54 Guided Synthetic Class Balancing

K54 adds `guided-synthetic-inputs` for deterministic-guided synthetic input
generation:

```bash
python -m sp63_core guided-synthetic-inputs --output-dir reports/guided_synthetic_inputs --target-pass 50 --target-fail 50 --target-review 50 --seed 42 --max-attempts 3000 --json
```

Candidates are generated from engineering-style synthetic ranges and accepted
only when deterministic SP63 draft design returns an `overall_status` needed by
the target distribution. ML is not used to guide or accept candidates.

K54 does not change formulas, material values, reinforcement selection, report
generation, external validation, material verification, or ML safety rules.
Synthetic data remains synthetic-only and requires engineer review.

## K55 Large Balanced Synthetic ML Benchmark

K55 adds `synthetic-ml-benchmark` as an orchestration layer for synthetic ML
experiments:

```bash
python -m sp63_core synthetic-ml-benchmark --output-dir reports/synthetic_ml_benchmark --target-pass 100 --target-fail 100 --target-review 100 --json
```

The command connects guided synthetic input generation, deterministic report
batching, report dataset export, synthetic balance/readiness checks, feature
selection, non-neural baseline ML, and advisory neural surrogate smoke metrics.

K55 does not change formulas, material values, reinforcement selection, report
generation, external validation, material verification, or ML safety rules.
Benchmark metrics are synthetic-only and are not production evidence. ML
remains advisory-only, deterministic SP63 checks remain mandatory, and engineer
review remains required.

## K56 Benchmark Model Comparison

K56 adds a read-only comparison report for K55 `benchmark_report.json` files.
It compares non-neural baseline metrics with advisory neural surrogate metrics
and can export Markdown, JSON, and CSV review artifacts.

The comparison does not rerun the benchmark, does not train a model, does not
change formulas, does not change material values, and does not modify
reinforcement selection. It is a trend-review aid for synthetic benchmark
metrics only.

Any interpretation of model winners still requires engineer review. ML remains
advisory-only and deterministic SP63 checks remain mandatory.

## K57 Multi-Seed Benchmark Trend Report

K57 adds an aggregate trend report for several K55 synthetic benchmark reports.
It summarizes dataset row counts, class distributions, metric mean/min/max/std
values, and baseline-vs-neural winner counts across runs.

The trend report reads existing benchmark outputs and does not rerun K55, train
models, change formulas, change materials, or change reinforcement selection.
It is not external validation and is not production evidence.

Engineer review remains mandatory before drawing conclusions from benchmark
trends. Material verification and external validation remain separate gates.

## K58 External Validation ML Readiness

K58 adds `ml-external-readiness` as a review layer for ML datasets:

```bash
python -m sp63_core ml-external-readiness --dataset reports/synthetic_dataset_smoke.jsonl --json
```

The command distinguishes synthetic/report-derived data from datasets with
engineer-filled external validation CSVs and material verification CSVs. It
reports research, engineering-review, and project-use readiness flags.

`ml_ready_for_project_use` remains false in K58. Synthetic benchmark data is
not external validation, ML remains advisory-only, deterministic SP63 checks
remain mandatory, and engineer review remains required.

## K59 Material Verification ML Readiness

K59 adds `ml-material-readiness` as a focused review layer for material
verification coverage in report-derived ML datasets:

```bash
python -m sp63_core ml-material-readiness --dataset reports/synthetic_dataset_smoke.jsonl --json
python -m sp63_core ml-material-readiness --dataset reports/synthetic_dataset_smoke.jsonl --material-verification-csv tests/fixtures/material_verification_sample.csv --json
```

The command extracts concrete, longitudinal rebar, and stirrup rebar classes
from dataset rows and checks that every required material key has complete
engineer-filled verification CSV coverage. Missing, rejected, or
review-required material keys keep the dataset out of engineering-review
readiness.

K59 also connects this coverage to `ml-external-readiness`; ML engineering
review readiness now requires accepted external validation and complete
material verification coverage. Project-use readiness remains false. K59 does
not change formulas, material values, reinforcement selection, report
generation, external validation, or ML safety rules.

## K60 Engineering ML Readiness Bundle

K60 adds `engineering-ml-readiness` as an aggregate review layer across:

- report-derived dataset quality;
- external validation readiness;
- material verification readiness;
- optional synthetic benchmark and model-comparison evidence;
- optional advisory ML proposal package evidence.

The bundle writes Markdown, JSON, CSV matrix, and `README_REVIEW.md` outputs
when `--output-dir` is supplied. It can set
`ml_ready_for_engineering_review = true` only when external validation has
accepted cases without failures and material verification coverage is complete.

K60 keeps `ml_ready_for_project_use = false`. It does not change deterministic
formulas, material values, reinforcement selection, external validation logic,
or ML safety rules.

## K61 Engineering Workflow Runner

K61 adds `engineering-workflow` as an orchestration layer for existing review
steps:

```bash
python -m sp63_core engineering-workflow --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/engineering_workflow_smoke --json
```

The workflow creates a deterministic report bundle, validates the archive,
creates a ZIP package by default, and can optionally run the K60 advisory ML
readiness bundle when a dataset is supplied.

K61 does not certify a design and does not approve ML for project use.
`ml_ready_for_project_use` remains false. Material verification, external
validation, deterministic SP63 checks, and engineer review remain mandatory.

## K62 Engineering Workflow Self-Check

K62 adds `engineering-workflow-self-check` as a user-facing readiness check:

```bash
python -m sp63_core engineering-workflow-self-check --output-dir reports/workflow_self_check --json
```

The self-check verifies that the K61 workflow can create the deterministic
report bundle, archive validation output, ZIP package, workflow summaries, and
review README files. It can optionally include advisory ML readiness, but
`ml_ready_for_project_use` remains false.

K62 is a technical workflow check only. It does not certify calculations,
change formulas, change material values, change reinforcement selection, or
approve ML for project use.

## K63 Future GUI/Desktop Wrapper Contract

K63 adds `engineering-interface-contract` and planning documents under
`docs/ui/`. This is a requirements and interface-contract step only. It does not
implement UI/Streamlit, does not change calculations, does not change materials,
does not change reinforcement selection, and does not make ML a calculator.

Future GUI/desktop wrappers must expose deterministic SP63 status, archive
validation status, generated report files, material verification, external
validation, engineer-review warnings, and `ml_ready_for_project_use = false`.

## K64 Engineering GUI Planning Decision

K64 adds `engineering-gui-planning` as a planning-only technology decision for a
future minimal engineering interface:

```bash
python -m sp63_core engineering-gui-planning --output-dir reports/gui_planning --json
```

The recommended option is `cli_first_with_static_html_reports`. This keeps the
existing deterministic CLI/workflow layer as the authority and postpones heavy
UI frameworks. Streamlit, Gradio, Flask, FastAPI, PyQt, PySide, Tkinter,
Electron, PyTorch, TensorFlow, and Keras are not added.

K64 preserves calculation formulas, material values, reinforcement selection,
ML safety policy, external validation, material verification, and archive
validation gates. It is planning work only; engineer review remains mandatory
and `ml_ready_for_project_use` remains false.

## K65 Static Workflow Report Index

K65 adds `engineering-report-index` and optional
`engineering-workflow --with-index` to generate a static `index.html` for an
existing workflow output folder.

The index links to deterministic report files, manifests, ZIP packages,
workflow summaries, review README files, and optional ML-readiness artifacts. It
does not execute calculations, start a web server, implement a GUI framework,
or approve a design.

K65 preserves calculation formulas, material values, material catalog gates,
reinforcement selection, external validation, and ML safety policy. HTML output
does not make ML a calculator; engineer review remains mandatory and
`ml_ready_for_project_use` remains false.

## K66 Input Form Schema Audit

K66 adds `input-form-schema` and `workflows/input_form_schema.py` for future UI
metadata only. It documents field groups, validation hints, mandatory warnings,
and anonymized input templates.

K66 does not implement UI, start a server, run calculations, change formulas,
change material values, change reinforcement selection, or approve ML for
project use. `ml_ready_for_project_use` remains false and engineer review
remains mandatory.

## K67 Input JSON Preflight

K67 adds `input-preflight` and `workflows/input_preflight.py` as an early
engineering validation report for input JSON files:

```bash
python -m sp63_core input-preflight --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/input_preflight --json
```

The preflight report checks JSON shape, required fields, unknown fields,
numeric input sanity, catalog material class names, optional ML-readiness
paths, and review conditions such as `Mser > M`.

K67 is reporting only. It does not execute design calculations, change
formulas, change material values, change reinforcement selection, implement UI,
or make ML a calculator. Deterministic SP63 checks, material verification,
external validation, and engineer review remain mandatory.

## K68 Static Input Form Preview

K68 adds `input-form-preview` and `workflows/static_input_form_preview.py` to
render a static HTML preview from the input form schema:

```bash
python -m sp63_core input-form-preview --output-dir reports/input_form_preview --json
```

The preview displays fields, units, defaults, validation hints, and safety
warnings only. It does not perform calculations, does not add JavaScript
calculators, does not start a web server, does not implement a GUI framework,
and does not approve project use. `ml_ready_for_project_use` remains false.

## K69 Workflow Preflight Index Integration

K69 adds `engineering-workflow --with-preflight` so the K67 preflight report can
run inside the reproducible engineering workflow before deterministic report
generation:

```bash
python -m sp63_core engineering-workflow --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/engineering_workflow_full_smoke --with-preflight --with-index --json
```

If preflight fails, deterministic calculation is skipped and the workflow
summary records `deterministic_report_status = skipped`,
`archive_validation_status = skipped`, and `zip_status = skipped`. If preflight
requires review, deterministic workflow may run but the workflow remains
`review_required`.

The static index links to `input_preflight_report.json` and
`input_preflight_report.md` when they exist. K69 does not change formulas,
materials, reinforcement selection, validation/external.py, UI policy, or ML
safety policy. Engineer review remains mandatory and ML remains advisory-only.

## K70 User-Friendly Diagnostics Catalog

K70 adds `diagnostics-catalog` and `workflows/diagnostics_catalog.py` as a
static EN/RU catalog of workflow-facing diagnostics:

```bash
python -m sp63_core diagnostics-catalog --json
```

The catalog covers input preflight, geometry, materials, loads, workflow,
archive, ZIP, ML-readiness, protected files, and release-candidate review. Each
entry includes severity, messages, recommended actions, and a related CLI
command.

K70 is guidance metadata only. It does not execute calculations, change
formulas, change material values, change reinforcement selection, implement UI,
or make ML a calculator.

## K71 Batch Engineering Workflow Runner

K71 adds `engineering-workflow-batch` and
`workflows/engineering_workflow_batch.py` to run the existing single-case
workflow across an input JSON folder:

```bash
python -m sp63_core engineering-workflow-batch --input-dir docs/reports/examples/form_templates --output-dir reports/engineering_workflow_batch --with-preflight --with-index --json
```

The batch runner creates one case folder per input JSON, a batch summary,
static batch index, and review README. Invalid cases are reported as failed
case results and do not stop the remaining cases.

K71 is orchestration only. It does not execute new formulas, change
calculation modules, change material values, change reinforcement selection,
implement UI, or make ML a calculator. Engineer review remains mandatory for
every case.

## K77 Clean Batch Examples and Summary UX

K77 adds `docs/reports/examples/batch_valid/` for clean batch smoke validation:

```bash
python -m sp63_core engineering-workflow-batch --input-dir docs/reports/examples/batch_valid --output-dir reports/engineering_workflow_batch_valid_smoke --with-preflight --with-index --json
```

The batch summary now separates command completion from engineering aggregate
status through `command_exit_status` and `batch_status`, lists passed,
review-required, and failed case ids, and includes recommendations for fixing
invalid cases. The existing `form_templates` folder remains a diagnostic set
with intentional invalid/review examples.

K77 is workflow UX and example-data hardening only. It does not change
formulas, material values, reinforcement selection, deterministic checks,
external validation logic, UI behavior, or ML safety policy.

## K78 Project Template Package

K78 adds `project-template` and `workflows/project_template.py`:

```bash
python -m sp63_core project-template --output-dir reports/project_template_smoke --json
```

The command creates a handoff scaffold with an editable rectangular input JSON,
blank external validation and material verification templates, recommended run
commands, an acceptance checklist, and a SHA256 manifest.

K78 is packaging only. It does not execute calculations, change formulas,
change material values, auto-update catalogs, implement UI, add private
SCAD/LIRA files, include full SP 63 text, or make ML a calculator. Engineer
review remains mandatory.

## K79 Documentation Link and Command Audit

K79 adds `docs-audit` and `workflows/docs_audit.py`:

```bash
python -m sp63_core docs-audit --json
```

The audit checks required documentation files, local Markdown links, and key
CLI example snippets so v0.9 readiness documentation remains navigable and
reproducible.

K79 is documentation infrastructure only. It does not execute calculations,
change formulas, change material values, update catalogs, implement UI, or make
ML a calculator.

## K72 External/Material Evidence Templates Package

K72 adds `evidence-templates` and `workflows/evidence_templates.py` to package
blank engineer-input templates:

```bash
python -m sp63_core evidence-templates --output-dir reports/evidence_templates --json
```

The package contains external-validation and material-verification CSV
templates, a README, and a SHA256 manifest. It reuses existing schemas and does
not invent incompatible formats.

K72 does not add real external values, closed SCAD/LIRA files, personal data,
full SP 63 text, formula changes, material value changes, or automatic catalog
updates. Engineer review remains mandatory.

## K73 Protected Files Guard

K73 adds `protected-files-check` and
`workflows/protected_files_guard.py` to detect protected file changes before a
release or sprint PR is reviewed:

```bash
python -m sp63_core protected-files-check --json
```

The protected set includes deterministic formula modules,
`validation/external.py`, and the concrete/rebar material catalog files. A
changed protected file produces `fail`; unavailable git diff produces
`review_required`.

K73 is a review aid only. It does not approve merge, certify designs, change
formulas, change materials, or make ML a calculator.

## K74 User Manual Package

K74 adds `docs/user_manual/` and `user-manual-index`:

```bash
python -m sp63_core user-manual-index --json
```

The manual covers quickstart, input data, preflight validation, workflow runs,
report indexes, batch workflow, ML advisory limits, evidence templates,
troubleshooting, and acceptance checklist.

K74 is documentation only. It does not change formulas, material values,
reinforcement selection, external validation logic, UI behavior, or ML safety
policy. Engineer review remains mandatory.

## K75 Release Candidate Report

K75 adds `release-candidate-report` and `workflows/release_candidate.py`:

```bash
python -m sp63_core release-candidate-report --output-dir reports/release_candidate_v0_9 --json
```

The report gathers golden validation, manual verification, material audit,
external validation sample, workflow self-check, input schema/preflight, static
index, protected-files guard, and user manual statuses.

K75 does not publish a release, certify designs, change formulas, change
material values, change reinforcement selection, implement UI, or make ML a
calculator. The report remains `review_required` while material audit and
external validation remain engineer gates.
