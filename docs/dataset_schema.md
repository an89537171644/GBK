# Схема датасета v0.1

## Назначение

Датасет нужен для обучения surrogate-модели и проверки ее качества. Источник целевых значений для MVP — детерминированное расчетное ядро `sp63_core`.

## Поля

| Поле | Тип | Единицы | Описание |
|---|---|---|---|
| `case_id` | str | - | идентификатор расчета |
| `element_type` | str | - | beam/slab |
| `b` | float | мм | ширина |
| `h` | float | мм | высота |
| `h0` | float | мм | рабочая высота |
| `concrete_class` | str | - | класс бетона |
| `rebar_class` | str | - | класс продольной арматуры |
| `stirrup_class` | str | - | класс поперечной арматуры |
| `M` | float | Н*мм | изгибающий момент |
| `Q` | float | Н | поперечная сила |
| `As_required` | float | мм² | требуемая/рациональная площадь продольной арматуры |
| `As_provided` | float | мм² | фактически подобранная площадь |
| `main_rebar_scheme` | str | - | например, 4D16 |
| `stirrup_scheme` | str | - | например, D8/150, 2 ветви |
| `Mult` | float | Н*мм | предельный момент |
| `Qult` | float | Н | предельная поперечная сила |
| `bending_utilization` | float | - | M/Mult |
| `shear_utilization` | float | - | Q/Qult |
| `status` | str | - | pass/fail |
| `sp63_core_version` | str | - | версия расчетного ядра |
| `dataset_version` | str | - | версия датасета |

## Разделение выборки

- train: 70 %;
- validation: 15 %;
- test: 15 %.

## Метрики ML

- MAE по `As_required`;
- MAPE по `As_required`;
- доля проходящих вариантов с первого кандидата;
- средний перерасход арматуры;
- `unsafe_accept_rate = 0`.

## K6 dataset generation notes

Target values are produced by the deterministic `design_rectangular_element()` service.
ML is not used to generate dataset rows.

Rows are exported only when:
- design status is `pass`;
- selected longitudinal and transverse reinforcement exist;
- protocol exists;
- bending and shear utilization are not greater than 1.0;
- single-layer longitudinal layout is feasible.

Additional v0.2 columns:

| Field | Type | Units | Description |
|---|---|---|---|
| `main_bar_count` | int | - | selected longitudinal bar count |
| `main_bar_diameter` | float | mm | selected longitudinal bar diameter |
| `stirrup_diameter` | float | mm | selected stirrup diameter |
| `stirrup_legs` | int | - | selected stirrup legs |
| `stirrup_spacing` | float | mm | selected stirrup spacing |
| `Asw` | float | mm2 | selected transverse reinforcement area |
| `layout_clear_width` | float | mm | clear width available for one reinforcement layer |
| `layout_required_width` | float | mm | required width for the selected one-layer layout |
| `layout_feasible` | bool | - | selected layout feasibility flag |
| `requires_engineer_review` | bool | - | draft calculation review marker |

Split export creates deterministic files by row order:
- `train.csv`;
- `validation.csv`;
- `test.csv`.
