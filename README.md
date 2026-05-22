# GBK / sp63-rc-ai

Программный MVP-прототип для предварительного расчета и подбора армирования
прямоугольных железобетонных элементов. Проект развивает deterministic
расчетное ядро `sp63_core`, CLI, отчетность, датасет и безопасные ML-помощники.

## Статус MVP

Реализовано:

- единицы измерения и draft-справочники материалов;
- геометрия прямоугольного сечения;
- проверки изгиба и поперечной силы по MVP formula cards;
- подбор продольной и поперечной арматуры через deterministic checks;
- end-to-end сервис `design_rectangular_element()`;
- расчетный протокол и экспорт JSON/HTML;
- генератор safe/pass датасета и train/validation/test split;
- CLI;
- Streamlit draft prototype;
- baseline и neural ML-прогноз `As_required`;
- safe ML suggestions с `unsafe_accept_rate = 0`;
- draft golden cases и validation docs;
- release documentation package.

## Инженерное предупреждение

Все результаты имеют draft/MVP-статус и требуют инженерной проверки.
`requires_engineer_review = true` означает, что результат нельзя использовать как
самостоятельную проектную документацию. ML-модули не являются расчетчиком:
каждый предложенный вариант должен проходить deterministic checks.

## Быстрый старт

```bash
python -m pip install -e ".[dev,ml]"
python -m pytest
ruff check .
```

Для UI:

```bash
python -m pip install -e ".[dev,ui]"
streamlit run apps/streamlit_app.py
```

## CLI

Примеры:

```bash
sp63-core demo
sp63-core bending --cover 32 --as-area 942.48 --moment 150000000
sp63-core bending --cover 32 --as-area 942.48 --moment 150000000 --json
sp63-core shear --cover 32 --q 80000 --asw 100.53 --sw 200
sp63-core shear --cover 32 --q 80000 --asw 100.53 --sw 200 --json
sp63-core select-longitudinal --moment 150000000 --max-results 5
sp63-core select-transverse --cover 32 --q 80000 --max-results 5
sp63-core design --cover 32 --moment 150000000 --q 80000
sp63-core design --cover 32 --moment 150000000 --q 80000 --json
sp63-core design --cover 32 --moment 150000000 --q 80000 --report-html reports/demo.html
sp63-core generate-dataset --limit 10 --output data/generated/sample.csv
sp63-core generate-dataset --limit 100 --output-dir data/generated --split
```

## Report export

Calculation protocols can be exported as JSON for machine processing and HTML for review.
Both formats keep `requires_engineer_review` and the MVP/draft warning.

```bash
sp63-core design --moment 150000000 --q 80000 --report-json reports/demo.json
sp63-core design --moment 150000000 --q 80000 --report-html reports/demo.html
```

## Streamlit

```bash
streamlit run apps/streamlit_app.py
```

Интерфейс использует только deterministic service и показывает предупреждение о
необходимости инженерной проверки.

## Тесты

```bash
python -m pytest
ruff check .
```

## Документация

- [User manual](docs/user_manual.md)
- [Developer guide](docs/developer_guide.md)
- [Applicability limits](docs/applicability_limits.md)
- [Implementation status](docs/implementation_status.md)
- [Dataset schema](docs/dataset_schema.md)
- [Detailed validation plan](docs/validation/detailed_validation_plan.md)
- [SCAD/LIRA comparison template](docs/validation/scad_lira_comparison_template.md)
- [Grant report structure](docs/grant_report_structure.md)
- [Program registration notes](docs/program_registration_notes.md)
- [Changelog](CHANGELOG.md)

## Что еще не реализовано

- полный набор расчетных разделов СП;
- кручение, продавливание, колонны, сложные сечения;
- трещиностойкость, прогибы, нелинейная деформационная модель;
- PDF export;
- production UI/API;
- инженерно утвержденные golden cases.

## Границы применимости

См. [docs/applicability_limits.md](docs/applicability_limits.md). MVP применим
только для предварительного анализа прямоугольных изгибаемых элементов без
предварительного напряжения и не заменяет полный проектный расчет.

## Текущие ограничения MVP

- Все материалы и расчетные примеры имеют draft-статус и требуют инженерной проверки.
- Draft-справочник арматуры различает `Rsc_long` и `Rsc_short`; значения требуют инженерной проверки.
- Подбор продольной арматуры пересчитывает `h0` для каждого диаметра кандидата.
- Подбор продольной арматуры учитывает draft-проверку однослойной раскладки.
- Подбор поперечной арматуры выполняет draft-перебор хомутов и проверяет каждый вариант через `check_shear_rectangular()`.
- End-to-end сервис подбирает продольную и поперечную арматуру и возвращает расчётный протокол с `requires_engineer_review`.
- Baseline ML прогнозирует только `As_required`; любой предложенный вариант обязан проходить deterministic checks.
- Neural surrogate использует `MLPRegressor` только как помощник; `unsafe_accept_rate` остаётся 0 за счёт deterministic selection.
- Golden cases имеют draft-статус: `approved_by_engineer = false`, `requires_engineer_review = true`.
- ML и UI остаются вспомогательными слоями и не заменяют deterministic checks.
