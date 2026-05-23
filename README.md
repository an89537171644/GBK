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
