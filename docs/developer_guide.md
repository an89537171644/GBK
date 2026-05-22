# Руководство разработчика

## 1. Структура репозитория

- `src/sp63_core/checks` — deterministic расчетные проверки.
- `src/sp63_core/materials` — draft-справочники материалов.
- `src/sp63_core/sections` — геометрические модели.
- `src/sp63_core/rebar` — подбор и раскладка арматуры.
- `src/sp63_core/services` — end-to-end сервисы.
- `src/sp63_core/report` — протокол и экспорт.
- `src/sp63_core/dataset` — генерация проверенных датасетов.
- `src/sp63_core/ml` — ML-помощники, не принимающие инженерные решения.
- `apps` — демонстрационные приложения.
- `tests` — unit, integration и golden-case проверки.
- `docs` — formula cards, validation и release-документация.

## 2. Как запускать тесты

```bash
python -m pip install -e ".[dev,ml]"
python -m pytest
ruff check .
```

Для Streamlit:

```bash
python -m pip install -e ".[dev,ui]"
streamlit run apps/streamlit_app.py
```

## 3. Как добавлять расчетный модуль

1. Создать или обновить formula card в `docs/formulas`.
2. Добавить draft golden cases в `tests/golden_cases`.
3. Реализовать функцию в отдельном модуле `checks`.
4. Возвращать итог и промежуточные значения для протокола.
5. Добавить тесты pass/fail/review cases.
6. Обновить `docs/implementation_status.md`.

## 4. Как писать formula card

Formula card должна содержать:

- область применимости;
- используемые обозначения;
- единицы измерения;
- формулы без скрытых допущений;
- ограничения MVP;
- контрольные примеры;
- отметку `requires_engineer_review`.

Полный текст СП в репозиторий не включается.

## 5. Как добавлять golden case

Golden case хранится в JSON и должен иметь:

```json
{
  "approved_by_engineer": false,
  "requires_engineer_review": true
}
```

До инженерного утверждения запрещено помечать case как approved.

## 6. Как использовать Codex

Задачи следует выполнять пошагово. Для расчетных модулей сначала утверждаются
formula cards и контрольные примеры, затем пишется код. Нельзя переходить к
следующему расчетному разделу без отдельной команды.

## 7. Definition of Done

Для каждого шага:

- изменения ограничены scope задачи;
- есть тесты или документированная причина их отсутствия;
- `python -m pytest` проходит;
- `ruff check .` проходит;
- документация обновлена;
- draft/engineer-review ограничения явно указаны.

## 8. Запрет на unsafe ML decisions

ML-модули могут только прогнозировать вспомогательные значения. Любое
армирование, предложенное ML, должно пройти deterministic checks. Unsafe accept
rate должен оставаться равным 0.
