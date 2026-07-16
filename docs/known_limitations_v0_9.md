# v0.9 Known Limitations

- ветвь шага 3 `ULS-BEND-RECT-001` передаётся только на повторную инженерную
  проверку; исправление кода не утверждает нормативные формулы;
- узкая версия изгиба ограничена тяжёлым бетоном B15–B40, A400/A500,
  однорядной растянутой арматурой и `As_prime=0`;
- машинная конвенция локальных осей, растянутой грани и семантика `cover`
  требуют проверки инженером на схемах обеих граней;
- поддержаны только два явно названных контекста `gamma_b1`: сочетание с
  кратковременными воздействиями (`1,0`) и только постоянные/длительные
  воздействия (`0,9`); остальные `gamma_bi` не покрыты;
- ветвь `long` реализована только в изолированной проверке изгиба; сквозной
  расчёт, датасеты и ML принимают только `short` и иначе завершаются
  `outside_applicability`/ошибкой контракта;
- строки A400 390/340 МПа сохраняются как provisional-регрессия шага 2;
  приложенный базовый PDF содержит 400/350 МПа, а артефакт изменения № 1
  отсутствует, поэтому источник и итоговая диспозиция остаются
  `OPEN_QUESTION`;
- при `x>xi_R*h0` версия 1 возвращает `outside_applicability` и не публикует
  расчётную способность; условная ветвь п. 8.1.12 не реализована;
- условие п. 8.1.3 не проверяется, поэтому полнота результата остаётся
  `incomplete`, в том числе при исходе узкого сравнения `pass`;
- BMR-01—BMR-05 и существующие golden/manual/synthetic cases являются
  регрессиями, а не независимым инженерным evidence;
- произвольные `h0_override` и `Rsc_override` не допускаются в проектном
  маршруте;
- `requires_engineer_review=true` и `project_use=false` сохраняются до
  независимых подписанных расчётов, реального внешнего сопоставления и нового
  инженерного протокола;
- deterministic SP63 core remains draft-MVP and requires engineer review;
- material catalog values require separate engineer verification before project use;
- real external validation with manual, Excel, SCAD, or LIRA values remains mandatory;
- ML and neural surrogate outputs are advisory-only;
- `ml_ready_for_project_use` remains `false`;
- workflow/self-check/index/schema/preflight reports do not approve project use;
- v0.9 review closure output is manual review evidence only and does not close
  material, external validation, manual signoff, or project approval gates;
- v0.9 release candidate package output is evidence packaging only and does not
  publish a release or approve project use;
- static HTML reports and launcher scripts are review conveniences only;
- no full GUI, web server, or desktop app is implemented;
- v1.0 readiness remains blocked by material verification, real external
  validation, packaging/installer governance, and ML production governance;
- no design certification is implied by any report or audit output.
