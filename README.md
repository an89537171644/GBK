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
