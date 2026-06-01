# sp63-rc-ai

Проект: программный прототип для расчета и подбора армирования железобетонных элементов по СП 63 с применением нейросетевой surrogate-модели.

## Основная идея

Нейросеть не является окончательным расчетчиком. Она предлагает варианты армирования или прогнозирует расчетные характеристики, а каждый вариант проверяется через детерминированное расчетное ядро `sp63_core`.

## MVP

Первый этап: прямоугольный изгибаемый железобетонный элемент без предварительного напряжения.

Функции MVP:
- справочники материалов;
- прямоугольное сечение;
- проверка нормального сечения по изгибу;
- проверка по поперечной силе;
- подбор продольной и поперечной арматуры;
- расчетный протокол;
- генератор расчетных примеров;
- baseline/ML-модель для прогноза потребности в армировании.

## Принцип безопасности

Любой результат ML должен быть проверен расчетным модулем по СП 63. Небезопасные решения не принимаются.

## Реализовано в ядре

- `sp63_core.units` — конвертация единиц проекта.
- `sp63_core.materials` — draft-справочники материалов с пометкой инженерной проверки.
- `sp63_core.sections.RectangularSection` — геометрия прямоугольного сечения.
- `sp63_core.checks.check_bending_rectangular` — MVP-проверка прямоугольного сечения по изгибу по карточке `docs/formulas/SP63_8_1_9_bending_rectangular.md`.
- `sp63_core.checks.check_shear_rectangular` — MVP-проверка поперечной силы по карточке `docs/formulas/SP63_8_1_33_shear.md`.
- `sp63_core.rebar.select_longitudinal_rebar` — D2-перебор продольной арматуры 2–8 стержней D10–D32 с проверкой каждого варианта через изгиб.
- `sp63_core.rebar.select_transverse_rebar` — K3-перебор поперечной арматуры D6–D12, 2/4 ветви и шагов 100–300 мм с проверкой каждого варианта через поперечную силу.
- `sp63_core.design.design_rectangular_element` — K4-end-to-end расчет прямоугольного элемента: подбор продольной арматуры, подбор хомутов, расчетный протокол и итоговый статус.
- `sp63_core.report.build_calculation_protocol` — F1-структура расчетного протокола: исходные данные, материалы, геометрия, армирование, проверки, предупреждения и итоговый статус.
- `sp63_core.dataset.generate_dataset_cases` и `export_dataset_csv` — G1-генерация безопасно проверенных строк датасета и экспорт CSV по `docs/dataset_schema.md`.

## K1 stabilization status

- Longitudinal reinforcement selection recalculates `h0` for each candidate diameter.
- Each candidate uses its own `RectangularSection` with `main_bar_diameter = diameter`.
- Draft single-layer reinforcement layout check is applied before bending checks.
- Infeasible one-layer layouts are filtered out.
- Dataset rows use the selected option section when writing `h0` and running shear checks.
- Stirrup selection, ML, and Streamlit are outside K1.

## K2 load duration / Rsc status

- Reinforcement catalog separates `Rsc_short` and `Rsc_long`.
- A500 uses `Rsc_short = 400 MPa` and `Rsc_long = 435 MPa`.
- `check_bending_rectangular` accepts `load_duration = short/long`.
- `Rsc_override` still has priority for manual review cases.
- ML, stirrup selection, and Streamlit are outside K2.

## K3 transverse reinforcement selection status

- Transverse reinforcement selection is implemented as a draft enumeration.
- Candidates are accepted only when `check_shear_rectangular` returns `pass`.
- Dataset rows now store the selected stirrup scheme and shear result.
- ML and UI are still not started.

## K4 end-to-end rectangular design status

- `design_rectangular_element()` is available.
- The function combines longitudinal and transverse reinforcement selection.
- The result contains `CalculationProtocol` for passing full designs.
- ML and UI are not implemented yet.

## K5 CLI status

The CLI uses subcommands for the main MVP scenarios:

```bash
python -m sp63_core bending --b 300 --h 500 --cover 32 --stirrup-diameter 8 --main-bar-diameter 20 --concrete B25 --rebar A500 --as-area 942.48 --moment 150000000 --load-duration short
python -m sp63_core shear --b 300 --h 500 --cover 32 --stirrup-diameter 8 --main-bar-diameter 20 --concrete B25 --stirrup-rebar A240 --Q 80000 --Asw 100.53 --sw 200
python -m sp63_core select-longitudinal --b 300 --h 500 --cover 32 --stirrup-diameter 8 --concrete B25 --rebar A500 --moment 150000000 --load-duration short
python -m sp63_core select-transverse --b 300 --h 500 --cover 32 --stirrup-diameter 8 --main-bar-diameter 20 --concrete B25 --stirrup-rebar A240 --Q 80000
python -m sp63_core design-rectangular --b 300 --h 500 --cover 32 --stirrup-diameter 8 --concrete B25 --rebar A500 --stirrup-rebar A240 --moment 150000000 --shear 80000 --load-duration short
python -m sp63_core generate-dataset --limit 100 --output data/generated/dataset_v001.csv --load-duration short
```

Each calculation command also supports `--json`.

## K6 constructive checks status

- Draft constructive checks for longitudinal and transverse reinforcement are implemented.
- Reinforcement selection now filters candidates by calculation checks and draft constructive requirements.
- Serviceability limit states are not implemented yet.
- ML is not implemented yet.

## K7 dataset split status

- Dataset generation is now beam-only for the MVP.
- Dataset rows include selected longitudinal and transverse reinforcement details, layout status, constructive statuses, and draft shear-rule fields.
- `split_dataset_cases()` provides reproducible train/validation/test splitting.
- `export_dataset_split_csv()` writes separate train, validation, and test CSV files.
- `build_dataset_report()` and `export_dataset_report_json()` create a JSON report with ranges, class counts, split sizes, and `unsafe_rows_count`.
- ML is still not started.

## K8 dataset generation hardening status

- Dataset geometry now keeps `geometry_stirrup_diameter` consistent with the selected `stirrup_diameter`.
- `limit` is applied after full-grid generation and deterministic shuffle.
- `--seed` and `--no-shuffle` control dataset ordering.
- `--group-split` performs train/validation/test split by `group_key` to reduce ML leakage.
- Dataset reports include group counts, stirrup geometry mismatch counts, duplicate case id counts, and reinforcement scheme counts.
- ML is still not started.

## K9 validation package status

The validation package is available before baseline ML:

```bash
python -m sp63_core validate --golden
python -m sp63_core validate --generate-dataset-limit 100 --json
```

- Golden validation checks draft bending, shear, and end-to-end design cases.
- Dataset validation checks unsafe rows, stirrup geometry mismatches, duplicate case ids, and group split leakage.
- `build_scad_lira_comparison_template()` provides a manual comparison template.
- ML is still not started.

## K10 external validation status

External engineering validation gates are available:

```bash
python -m sp63_core validate --external-template reports/interim/scad_lira_template.csv
python -m sp63_core validate --golden --generate-dataset-limit 100 --acceptance-report reports/interim/acceptance_report.json --json
```

- SCAD/LIRA comparison rows can be exported for manual filling.
- Acceptance gates check golden validation, dataset validation, external acceptance flags, and filled external deltas.
- Default recommended delta threshold is `5.0%`.
- Without filled external comparison, acceptance status is `warning`.
- ML is still not started.

## K11 strict external acceptance status

Filled SCAD/LIRA comparison CSV files can now be loaded and checked strictly:

```bash
python -m sp63_core validate --external-input reports/interim/scad_lira_filled.csv --external-with-deltas reports/interim/scad_lira_with_deltas.csv --golden --generate-dataset-limit 100 --acceptance-report reports/interim/acceptance_report.json --json
```

- Empty external numeric fields are parsed as missing values.
- `accepted` supports `true/false`, `1/0`, `yes/no`, and `да/нет`.
- Acceptance fails when required SCAD/LIRA values are incomplete.
- Acceptance fails when engineer acceptance is missing or false.
- Acceptance fails when filled deltas exceed the configured threshold.
- ML is still not started.

## K12 baseline ML sandbox status

Experimental baseline ML is available for the beam-only strength dataset:

```bash
python -m sp63_core train-baseline --generate-dataset-limit 500 --model-output models/baseline_model.pkl --metrics-output reports/interim/baseline_metrics.json --seed 42
```

- The baseline trains RandomForest models for reinforcement and utilization
  targets.
- The model bundle is experimental and advisory only.
- Deterministic SP63 checks remain mandatory for every ML proposal.
- Streamlit and production ML recommendations are not implemented.

## K12.1 ML leakage and safety status

- `h0` is removed from ML input features because it leaks the selected main bar
  diameter target.
- `cover` is now stored in dataset rows and used as a geometry input feature.
- Baseline predictions are reconstructed into an explicit reinforcement
  proposal.
- The exact ML proposal is checked by deterministic layout, constructive,
  bending, and shear checks.
- `unsafe_prediction_rate` and `deterministic_accept_rate` are written to the
  baseline metrics JSON.
- ML remains advisory-only.

## K12.2 ML target hygiene and quality gate status

- `stirrup_diameter` is no longer predicted by baseline ML.
- `geometry_stirrup_diameter` is treated as an input geometry parameter.
- `h0` remains excluded from ML input features.
- `cover` remains an ML input feature.
- ML proposals are still reconstructed and checked deterministically.
- Baseline metrics include `stirrup_legs_accuracy`, `feature_count`, and
  `target_count`; `stirrup_diameter_accuracy` is removed.
- `evaluate_ml_quality_gate()` reports sandbox quality status using
  `unsafe_prediction_rate`, `deterministic_accept_rate`, and `As_MAPE`.
- ML remains advisory-only and deterministic SP63 checks remain mandatory.

## K13 service material properties status

- Concrete catalog now includes `Rbser` and `Rbtser`.
- Serviceability material properties are available for future checks.
- K14 adds the first draft normal crack formation check.
- Crack width and deflection calculations are not implemented yet.

## K14 normal crack formation status

- `check_normal_crack_formation_rectangular()` is available for draft normal
  crack formation checks in rectangular beams.
- CLI command `crack-formation` is available.
- The check uses concrete service tensile resistance `Rbtser`.
- The current draft uses a gross elastic concrete section.
- `requires_engineer_review = true` is kept for the draft serviceability result.
- K15 adds the first draft crack width `acrc` check.
- Deflection checks are not implemented.

## K15 normal crack width status

- `check_normal_crack_width_rectangular()` is available for draft normal crack
  width checks in rectangular beams.
- CLI command `crack-width` is available.
- `design-rectangular` supports `--check-crack-width` and `--acrc-limit`.
- The result is draft and keeps `requires_engineer_review = true`.
- Refined crack spacing, tension stiffening, transformed section behavior, and
  long-term effects are not implemented.

## K16 curvature and deflection status

- `check_curvature_deflection_rectangular()` is available for draft short-term
  curvature and deflection checks in rectangular beams.
- CLI command `deflection` is available.
- `design-rectangular` supports `--check-deflection`.
- The result is draft and keeps `requires_engineer_review = true`.
- Long-term effects, creep, shrinkage, refined tension stiffening, and nonlinear
  deformation model are not implemented.
- ML remains advisory-only and deterministic SP63 checks remain mandatory.

## K17 status separation

- `CalculationProtocol` now reports `strength_status`,
  `serviceability_status`, and `overall_status`.
- `strength_status` covers bending and shear checks only.
- `serviceability_status` covers crack formation, crack width, and deflection
  checks.
- `overall_status` is the engineering summary status; the legacy `status`
  field is kept as an alias for `overall_status`.
- `design-rectangular` text and JSON output include all three separated
  statuses.
- K17 changes status aggregation only. K14-K16 calculation formulas are not
  changed.
- ML remains advisory-only and deterministic SP63 checks remain mandatory.

## K19 material catalog audit status

- CLI command `materials-audit` is available for printing current material
  catalog audit rows.
- Concrete and reinforcement catalog values remain draft and require engineer
  verification against SP 63 tables before final use.
- The full text of SP 63 is not stored in this repository.
- K19 adds audit structure and documentation only; it does not approve
  normative values as final design data.
- ML remains advisory-only and deterministic SP63 checks remain mandatory.

## K20 manual SP63 verification cases status

- CLI command `manual-cases` is available for running six manual verification
  cases against the deterministic calculation core.
- The cases cover passing strength/serviceability, bending failure,
  crack-formation review, crack-width failure, deflection failure, and shear
  failure.
- The command compares program values with manual expected values using
  documented tolerances and checks `strength_status`, `serviceability_status`,
  and `overall_status`.
- These cases are draft verification checks and require engineer review.
- ML remains advisory-only and deterministic SP63 checks remain mandatory.

## K21 dataset enrichment status

- Generated dataset rows now include deterministic strength outputs, draft
  serviceability outputs, and separated `strength_status`,
  `serviceability_status`, and `overall_status` values.
- The enriched fields include explicit geometry/load aliases, selected
  reinforcement areas, `Mult`, `Qult`, `Mcrc`, crack width, deflection,
  warning count, review flag, and `dataset_source`.
- `dataset_source` is `deterministic_sp63_core`; the dataset is produced by the
  deterministic calculation core and remains a draft engineering artifact.
- `unsafe_row` is stored in every row and should remain `false` for exported MVP
  rows used by validation and ML experiments.
- ML remains advisory-only and the dataset does not replace engineering review.

## K22 ML readiness gate

- CLI command `ml-readiness` is available for checking deterministic dataset
  readiness before later ML stages.
- K22 does not train an ML model and does not add a neural network.
- The readiness report checks required enriched dataset columns, deterministic
  status distributions, unsafe rows, group leakage count, and constant
  target/status columns.
- The current safe accepted dataset can contain only `overall_status = pass`;
  in that case readiness is `review_required` because classification ML needs
  fail/review diagnostic cases.
- ML remains advisory-only and deterministic SP63 checks remain mandatory.

## K23 diagnostic dataset status

- CLI command `diagnostic-dataset` is available for deterministic diagnostic
  rows with `pass`, `fail`, and `review_or_fail` statuses.
- The diagnostic dataset is separate from the safe accepted dataset;
  `generate_dataset_cases()` keeps producing safe accepted rows.
- Diagnostic rows are computed through the deterministic SP63 draft core and
  use `dataset_source = diagnostic_deterministic_sp63_core`.
- `ml-readiness --diagnostic --json` can be used to verify that
  `overall_status` is no longer a constant classification target.
- The diagnostic dataset is for future ML classification readiness only. It is
  not a project-design solution dataset, and every row requires engineer review.
- ML remains advisory-only and no model is trained in K23.

## K24 baseline ML without neural network

- CLI command `ml-baseline` is available for a non-neural ML smoke report.
- The report runs simple baselines for safe dataset regression targets
  `longitudinal_as_mm2` and `bending_utilization`.
- The report runs simple classification baselines for `overall_status` on the
  diagnostic dataset.
- Neural networks are not used, and the report explicitly states that ML is
  advisory-only.
- Deterministic SP63 checks remain mandatory for every ML proposal.
- Small diagnostic dataset warnings must be reviewed before any later ML stage.

## K25 expanded diagnostic dataset status

- CLI command `diagnostic-dataset --limit 100 --json` now emits an expanded
  deterministic candidate dataset instead of only the six seed cases.
- The first six K20/K23 manual diagnostic cases are preserved.
- Additional candidate rows cover `pass_base`, `bending_fail`, `shear_fail`,
  `crack_review_without_width`, `crack_width_fail`, `deflection_fail`, and
  `multiple_fail`.
- The safe accepted dataset remains separate and is still the source for safe
  regression experiments.
- The diagnostic dataset is for classification readiness only. It is not a
  project-design solution dataset, and every row requires engineer review.
- ML remains advisory-only and deterministic SP63 checks remain mandatory.

## K26 baseline ML evaluation status

- CLI command `ml-baseline --diagnostic-limit 100 --json` now includes an
  `expanded_diagnostic_classification` block for the K25 diagnostic dataset.
- The expanded block reports train/test classification metrics for
  `overall_status`, including accuracy, macro F1, per-class precision/recall,
  confusion matrix, and class distribution.
- Two feature modes are reported: `input_only_features` and
  `deterministic_derived_features`.
- Deterministic-derived features are explicitly marked as review-only because
  they can leak deterministic calculation outcomes into project ML.
- No neural network is used. ML remains advisory-only, and deterministic SP63
  checks remain mandatory.

## K27 scalable diagnostic dataset status

- CLI command `diagnostic-dataset --limit 1000 --json` is supported for a
  larger deterministic diagnostic/candidate dataset.
- Every diagnostic row now includes `group_key` for leakage-safe ML splitting.
- `ml-readiness --diagnostic --json` reports `group_key_present`,
  `group_leakage_count`, status distribution, and failure-reason distribution.
- `ml-baseline --diagnostic-limit 1000 --json` uses a group-aware diagnostic
  split when `group_key` is available.
- The diagnostic dataset is not a set of approved design solutions; every row
  remains engineer-review material.
- ML remains advisory-only and deterministic SP63 checks remain mandatory.

## K28 group-diverse diagnostic dataset status

- CLI command `diagnostic-dataset --limit 5000 --json` is supported for a
  larger and more group-diverse deterministic diagnostic/candidate dataset.
- Diagnostic `group_key` now includes case type, geometry, cover, material
  classes, load family, and reinforcement family so ML validation can split
  across more independent groups.
- The diagnostic report includes `unique_group_count`, `group_key_present`,
  `group_leakage_count`, status distribution, failure-reason distribution, and
  warnings when group diversity is too low.
- `ml-readiness --diagnostic --json` reports diagnostic group diversity, and
  `ml-baseline --diagnostic-limit 1000 --json` continues to use group-aware
  splitting.
- The diagnostic dataset is not a set of approved design solutions. ML remains
  advisory-only, deterministic SP63 checks remain mandatory, and neural
  networks are still not implemented.

## K29 neural surrogate smoke MVP status

- CLI command `neural-surrogate --diagnostic-limit 1000 --json` is available
  for an advisory-only neural surrogate smoke report.
- Classification uses a small scikit-learn `MLPClassifier` on the K28
  diagnostic dataset target `overall_status`.
- Regression smoke metrics use scikit-learn `MLPRegressor` on safe deterministic
  dataset targets such as `longitudinal_as_mm2` and `bending_utilization`.
- The neural surrogate is not a design checker, is not certified, and must not
  be used as the basis for project design.
- Every ML prediction requires deterministic SP63 verification, and external
  engineering validation remains required before any broader ML work.

## K30 ML proposal safety wrapper

- CLI command `ml-proposal-verify --json` is available for deterministic
  verification smoke examples.
- ML and neural surrogate proposals are advisory-only and are never accepted
  directly as project calculations.
- The K30 wrapper verifies proposed rectangular reinforcement schemes through
  deterministic SP63 core checks for bending, shear, crack formation, crack
  width, and deflection when the required service inputs are present.
- Unsafe or review-required proposals are rejected by the wrapper. Accepted
  proposals still require engineer review.
- Deterministic SP63 checks remain mandatory for every ML output.

## K31 external validation workflow

- CLI command `external-validation --template` prints the engineer-filled CSV
  template path for manual, SCAD, LIRA, or Excel comparison cases.
- CLI command `external-validation --csv path/to/file.csv --json` summarizes
  filled external validation rows and reports `pass`, `review_required`, or
  `fail`.
- SCAD, LIRA, Excel, or manual external values are not included automatically;
  an engineer must fill and review them.
- The calculation core remains a draft-MVP until external validation is
  completed and accepted.
- ML and neural surrogate outputs remain advisory-only, and deterministic SP63
  checks remain mandatory.

## K32 external validation filled sample status

- CLI command `external-validation --sample --json` runs a filled public
  synthetic/manual external validation sample.
- The sample contains six K20-aligned cases: base pass beam, bending fail,
  crack review without width, crack width fail, deflection fail, and shear fail.
- Sample external values are synthetic/manual values close to program output;
  they are not real SCAD or LIRA files.
- Draft acceptance tolerances are recorded in code for bending, shear, Mcrc,
  crack width, and deflection deltas.
- The sample validates the external-validation pipeline only. Real SCAD, LIRA,
  Excel, or manual values must still be filled and reviewed by an engineer.
- The calculation core remains draft until full external validation is
  completed. ML remains advisory-only and deterministic SP63 checks remain
  mandatory.

## K33 external validation real-data gate

- CLI command `external-validation --csv path/to/engineer_filled.csv --strict --json`
  is available for real engineer-filled CSV intake.
- Strict mode checks required columns, filled external values, numeric parsing,
  delta/tolerance results, and `acceptance_status` consistency.
- Missing external values return `review_required`; tolerance failures return
  `fail`.
- `docs/validation/external_validation_engineer_checklist.md` describes what an
  engineer must fill and what must not be committed.
- `docs/validation/templates/external_validation_engineer_input_template.csv`
  provides a blank anonymized input template.
- K33 does not add real SCAD/LIRA files or invent external values. ML remains
  advisory-only, and deterministic SP63 checks remain mandatory.

## K34 material catalog engineer verification gate

- CLI command `material-verification --json` reports current material catalog
  verification status.
- Supported statuses are `draft`, `needs_review`, and `engineer_verified`.
- `material-verification --template` prints the CSV template for engineer
  checking of concrete and reinforcement catalog values.
- `materials-audit --verification-template` and
  `materials-audit --verification-csv path/to/material_verification.csv --json`
  provide the same verification gate through the audit command.
- `material-verification --csv path/to/material_verification.csv --json`
  checks an engineer-filled CSV without changing material values.
- `engineer_verified` rows require `engineer_name`, `review_date`, and
  `source_note`.
- Concrete verification covers `Rb`, `Rbt`, `Rbser`, `Rbtser`, and `Eb`.
- Reinforcement verification covers `Rsn`, `Rs`, `Rsser`, `Rsc_short`,
  `Rsc_long`, `Rsw`, and `Es`.
- K34 does not approve material values automatically, does not store full
  SP 63 text, and does not make ML a calculator.

## K35 material verification report integration

- CLI command `material-verification-report --csv path/to/material_verification.csv`
  renders a Markdown report for an engineer-filled material verification CSV.
- Add `--json` for a structured report with `total_rows`,
  `engineer_verified_count`, `needs_review_count`, and
  `missing_required_fields_count`.
- Add `--output report.md` to write the Markdown report to disk.
- The report lists rows that remain `needs_review`.
- K35 does not change material catalog values automatically and does not store
  full SP 63 text.

## K36 design calculation report export

- CLI command `design-report --markdown`, `design-report --html`, and
  `design-report --json` exports a draft rectangular design calculation report.
- Add `--output path/to/report.md` to write the selected report format to disk.
- The report includes input data, geometry, materials, selected reinforcement,
  bending and shear checks, serviceability checks, final separated statuses,
  warnings, and limitations.
- The report is not a certified design conclusion and keeps
  `requires_engineer_review = true`.
- Material verification and external validation remain separate gates.
- ML remains advisory-only, and deterministic SP63 checks remain mandatory.

## K37 input-driven design report status

- CLI command `design-report --input-json path/to/input.json --json` builds a
  report from user-provided rectangular beam input.
- The same input path works with `--markdown`, `--html`, `--output`, and
  `--bundle-output`; bundle mode writes `report.md`, `report.json`,
  `report.html`, and a copied `input.json`.
- The K36 smoke mode without `--input-json` is preserved.
- The input schema is documented in
  `docs/reports/design_report_input_schema.md`.
- Example input is available at
  `docs/reports/examples/rectangular_design_input_example.json`.
- Unknown input fields are rejected, and missing required fields raise clear
  errors.
- The report is not a certified design conclusion and keeps
  `requires_engineer_review = true`.
- Material verification and external validation remain separate gates.
- ML remains advisory-only, and deterministic SP63 checks remain mandatory.

## K38 batch design reports status

- CLI command `design-report-batch --input-dir docs/reports/examples/batch
  --output-dir reports/batch` builds report bundles for multiple JSON inputs.
- Repeated `--input-json` arguments are also supported for explicit input lists.
- Batch output writes `index.md`, `index.json`, and one `case_###` directory per
  input with `report.md`, `report.json`, `report.html`, and copied `input.json`.
- Invalid input JSON is reported as `input_error` in the index without stopping
  the remaining cases.
- Public synthetic batch examples are stored in `docs/reports/examples/batch`.
- Batch reports are draft review artifacts with `requires_engineer_review = true`.
- Material verification and external validation remain separate gates.
- ML remains advisory-only, and deterministic SP63 checks remain mandatory.

## K39 report bundle manifest status

- Single `design-report --bundle-output` bundles now write `manifest.json` by
  default.
- Batch `design-report-batch` output writes a root `manifest.json` and one
  case-level `manifest.json` per case.
- Manifests include input/output artifact paths, SHA256 checksums, generation
  time, command name, statuses, warnings count, and
  `requires_engineer_review = true`.
- Batch `index.json` includes manifest paths and checksums for each valid case.
- Manifest metadata is for traceability only and does not certify the design.
- Material verification and external validation remain separate gates.
- ML remains advisory-only, and deterministic SP63 checks remain mandatory.

## K40 report archive validation status

- CLI command `report-archive-validate --path reports/smoke_case --json`
  validates a single report bundle.
- CLI command `report-archive-validate --path reports/batch_smoke --batch
  --json` validates a batch report archive.
- The check verifies `manifest.json`, required report files, SHA256 checksums,
  and batch `index.json` consistency with case manifests.
- Missing files or checksum mismatches return `status = fail`.
- Archive validation is an integrity check only and still requires engineer
  review.
- Material verification and external validation remain separate gates.
- ML remains advisory-only, and deterministic SP63 checks remain mandatory.

## K41 report archive ZIP export status

- CLI command `report-archive-zip --path reports/smoke_case --output
  reports/smoke_case.zip --json` exports a single report bundle to ZIP.
- CLI command `report-archive-zip --path reports/batch_smoke --output
  reports/batch_smoke.zip --batch --json` exports a batch report archive to
  ZIP.
- ZIP export validates the source archive before packaging and validates the
  ZIP after creation.
- ZIP entries use relative paths; path traversal entries are rejected.
- JSON output includes `zip_sha256`, `validation_status`, and
  `requires_engineer_review = true`.
- ZIP export is a handoff/archive aid only and does not certify the design.
- Material verification and external validation remain separate gates.
- ML remains advisory-only, and deterministic SP63 checks remain mandatory.

## K42 engineering review package README status

- Single `design-report --bundle-output` folders now include
  `README_REVIEW.md`.
- Batch `design-report-batch` output now includes one root `README_REVIEW.md`.
- The README explains archive purpose, contents, validation commands, ZIP
  export commands, reproduction commands, file locations, final statuses, and
  review warnings.
- `README_REVIEW.md` is included in `manifest.json` checksums and ZIP export.
- Archive validation fails if the expected README is missing.
- The README is a handoff/review guide only and does not certify the design.
- Material verification and external validation remain separate gates.
- ML remains advisory-only, and deterministic SP63 checks remain mandatory.

## K43 ML-ready dataset from report archives status

- CLI command `report-dataset-export --path reports/smoke_case --output
  reports/smoke_dataset.jsonl --json` exports one row from a validated single
  report bundle.
- CLI command `report-dataset-export --path reports/batch_smoke --batch
  --output reports/batch_dataset.jsonl --json` exports rows from a validated
  batch report archive.
- `--format csv` and `--format json` are also supported.
- Export reads `report.json`, `input.json`, and `manifest.json`; it does not
  recalculate the deterministic core.
- Rows include provenance, SHA256 checksums, final statuses,
  `requires_engineer_review = true`, `ml_is_advisory_only = true`, and
  `deterministic_checks_required = true`.
- Material verification and external validation statuses are recorded as
  `not_provided` when they are not embedded in the report archive.
- ML remains advisory-only, and deterministic SP63 checks remain mandatory.

## K44 report-derived dataset quality gate status

- CLI command `report-dataset-quality --dataset reports/batch_dataset.jsonl
  --json` checks report-derived dataset rows before ML use.
- CSV output from `report-dataset-export --format csv` is supported with
  `--format csv`.
- The gate checks required columns, empty critical values, archive validation
  status, provenance, advisory-only flags, `overall_status` distribution, and
  leakage-like status/check columns.
- Small synthetic datasets and rows without embedded material or external
  validation statuses return `review_required`.
- K44 does not train ML and does not add neural-network code.
- ML remains advisory-only, and deterministic SP63 checks remain mandatory.

## K45 leakage-safe report dataset features status

- CLI command `report-dataset-features --dataset reports/batch_dataset.jsonl
  --json` prepares feature, target, and split metadata for report-derived rows.
- CSV datasets are supported with `--format csv`.
- `input_only` keeps source geometry, material, load, and serviceability switch
  fields separate from target/status/check columns.
- `deterministic_derived` can include selected deterministic outputs, but it
  always warns that these features may leak design decisions.
- Targets such as `overall_status`, `strength_status`, `serviceability_status`,
  `bending_status`, `shear_status`, `crack_width_status`, and
  `deflection_status` are supported.
- K45 does not train ML and does not add neural-network code.
- ML remains advisory-only, and deterministic SP63 checks remain mandatory.

## K46 baseline ML on report-derived safe features status

- CLI command `report-ml-baseline --dataset reports/batch_dataset.jsonl --json`
  runs a non-neural baseline classifier on K45 leakage-safe features.
- CSV datasets are supported with `--format csv`.
- `input_only` is the default feature mode and excludes status, direct check
  result, utilization, and target columns from model inputs.
- `deterministic_derived` is available only as a review-only smoke mode and
  warns about possible design-decision leakage.
- The report includes target distribution, train/validation/test counts,
  metrics, confusion matrix, and excluded leakage columns.
- Small report-derived example datasets return `review_required`.
- K46 does not add a neural network and does not make ML a design checker.
- ML remains advisory-only, and deterministic SP63 checks remain mandatory.

## K47 neural surrogate v2 on report-derived safe features status

- CLI command `report-neural-surrogate --dataset reports/batch_dataset.jsonl
  --json` runs an advisory-only neural surrogate smoke report on K45
  leakage-safe features.
- CSV datasets are supported with `--format csv`.
- `input_only` remains the default and excludes status, direct check result,
  utilization, and target columns from neural surrogate inputs.
- `deterministic_derived` is review-only and warns about possible
  design-decision leakage.
- The report includes target distribution, train/validation/test counts,
  `neural_network_used`, metrics, confusion matrix, and excluded leakage
  columns.
- Small report-derived example datasets return `review_required`; metrics are
  smoke diagnostics and not production evidence.
- K47 uses scikit-learn MLP only; PyTorch, TensorFlow, and Keras are not added.
- Neural surrogate is not a design checker. ML remains advisory-only, and
  deterministic SP63 checks remain mandatory.

## K48 neural advisory prediction status

- CLI command `report-neural-predict --dataset reports/batch_dataset.jsonl
  --input-json docs/reports/examples/rectangular_design_input_example.json
  --json` runs one advisory prediction and then builds the deterministic SP63
  design report for the same input.
- CSV datasets are supported with `--format csv`.
- The command returns predicted status, class probabilities, deterministic
  strength/serviceability/overall statuses, and
  `prediction_matches_deterministic`.
- Prediction mismatch is reported as `review_required`.
- Small report-derived example datasets return `review_required`; predictions
  and metrics are not production evidence.
- Neural prediction is not a design checker. Deterministic SP63 verification
  and engineer review remain mandatory.

## K49 neural advisory safety audit status

- CLI command `neural-safety-audit --dataset reports/batch_dataset.jsonl
  --input-json docs/reports/examples/rectangular_design_input_example.json
  --json` builds an engineer-facing safety audit around K48 advisory
  prediction output.
- CSV datasets are supported with `--format csv`.
- Markdown output is supported with `--markdown`, and `--output` can write the
  audit report to disk.
- The audit records predicted status, deterministic strength/serviceability/
  overall statuses, `prediction_matches_deterministic`,
  `advisory_signal_usable`, `audit_status`, rejection reasons, warnings, and
  errors.
- Prediction mismatch, deterministic `fail`, or deterministic
  `review_or_fail` prevents advisory signal use.
- Neural prediction remains advisory-only and is not a project decision.
  Deterministic SP63 verification and engineer review remain mandatory.

## K50 ML proposal package status

- CLI command `ml-proposal-package --dataset reports/batch_dataset.jsonl
  --input-json docs/reports/examples/rectangular_design_input_example.json
  --json` builds one advisory proposal package.
- CSV datasets are supported with `--format csv`.
- Markdown output is supported with `--markdown`, and `--output` can write the
  package report to disk.
- The package connects neural advisory prediction, K49 safety audit,
  deterministic SP63 verification, proposal decision status, rejection/review
  reasons, warnings, and class probabilities.
- `proposal_status` can be `accepted`, `review_required`, or `rejected`.
  Acceptance is advisory-only and still requires deterministic SP63 verification
  and engineer review.
- `deterministic_derived` remains a review-only feature mode and warns about
  possible design-decision leakage.
- K50 does not make ML a calculator and does not add a new neural-network
  dependency.

## K51 ML proposal engineering review package status

- CLI command `ml-proposal-review-package --dataset reports/batch_dataset.jsonl
  --input-json docs/reports/examples/rectangular_design_input_example.json
  --output-dir reports/ml_proposal_review --json` creates an engineer-facing
  handoff folder and ZIP for one advisory ML proposal.
- CSV datasets are supported with `--format csv`.
- `--no-zip` writes only the review folder.
- The package contains `input.json`, deterministic report MD/JSON/HTML,
  neural safety audit MD/JSON, ML proposal package MD/JSON,
  `README_REVIEW.md`, and `manifest.json`.
- The manifest records SHA256 checksums for package payload files, proposal
  status, deterministic statuses, prediction match flag, advisory signal
  usability, and safety flags.
- ZIP and manifest packaging do not certify the design. ML remains
  advisory-only, deterministic SP63 verification remains mandatory, and
  engineer review is required.

## Codex automation workflow

Codex automation is intended to work through GitHub Issues and Pull Requests.

Rules:

- Codex must not push directly to main.
- Codex must not merge PRs automatically.
- Every task must be implemented in a separate branch.
- Every task must end with a Pull Request.
- Every calculation formula requires engineer review.
- ML is advisory-only and must be checked by deterministic sp63_core.
- Personal data and full normative text must not be committed.

Recommended human setup:

1. Protect the main branch in GitHub settings.
2. Require Pull Request before merge.
3. Require pytest and ruff checks.
4. Use codex-ready issues as the task queue.
5. Review every PR before merge.
