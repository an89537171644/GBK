# Detailed validation plan

All validation cases in this repository are draft materials until an engineer
approves them. Machine-checkable golden cases must keep:

```text
approved_by_engineer = false
requires_engineer_review = true
```

## 1. Цель валидации

Confirm that deterministic `sp63_core` checks, selection services, reports, and
dataset generation match approved manual calculations and independent software
references before any result is used for design decisions.

## 2. Проверка единиц

- Check all public conversion helpers.
- Confirm project units: N, mm, MPa, N*mm, mm2.
- Add regression tests for negative and zero values where behavior is defined.

## 3. Проверка материалов

- Review draft concrete values B15-B40.
- Review draft rebar values A240/A400/A500.
- Record source clauses and engineer approval status.

## 4. Проверка изгиба

- Compare rectangular bending checks with hand calculations.
- Keep passing, failing, and review-required examples.
- Verify intermediate values: `x`, `xi`, `xi_R`, `Mult`, `utilization`.

## 5. Проверка поперечной силы

- Compare shear checks with hand calculations.
- Verify concrete strip and inclined section checks.
- Verify selected minimum `C` in the MVP search range.

## 6. Проверка подбора продольной арматуры

- Confirm every returned option has `status == "pass"`.
- Confirm `h0` is recalculated for each selected bar diameter.
- Confirm single-layer layout feasibility is checked.

## 7. Проверка подбора хомутов

- Confirm every returned stirrup option has `status == "pass"`.
- Confirm ordering by steel consumption and spacing.
- Review assumptions for legs and spacing options.

## 8. Сравнение с ручными расчётами

- Store hand calculation sheets or markdown notes for each approved case.
- Record formulas, units, and rounding.
- Mark engineer approval separately from automated test acceptance.

## 9. Сравнение с SCAD/LIRA

- Use `docs/validation/scad_lira_comparison_template.md`.
- Record model assumptions, load cases, material settings, and differences.
- Do not mark a case approved until an engineer signs off.

## 10. Проверка датасета

- Ensure generated rows are deterministic and safe/pass only.
- Confirm `unsafe_accept_rate = 0`.
- Confirm train/validation/test split is deterministic.

## 11. Проверка ML

- ML can only predict helper values such as `As_required`.
- ML output must never bypass deterministic checks.
- Track metrics separately from engineering acceptance.

## 12. Границы применимости

- MVP is limited to supported heavy concrete and reinforcement classes.
- MVP formulas are limited to the approved formula cards.
- Draft reports, UI, and ML outputs require engineering review.
