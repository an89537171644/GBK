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
