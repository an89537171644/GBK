# SP63 6.1.12 - concrete working-condition factor by load combination

requires_engineer_review = true
project_use = false

## Scope

This card defines only the two ULS load contexts accepted by the provisional
rectangular-bending path for heavy concrete B15-B40. It does not form load
combinations and does not cover other concrete working-condition factors.

Provisional profile identifier:
`SP63-2018-AMD1-AMD2-PROVISIONAL@2026-07-15`.

## Closed context mapping

| Input key | Declared combination | `gamma_b1` |
|---|---|---:|
| `short` | permanent, long-term, and short-term loads | 1.0 |
| `long` | only permanent and long-term loads | 0.9 |

The effective concrete compression resistance is the catalog `Rb` with the
declared `gamma_b1` applied by the centralized material resolver. An unknown or
unspecified combination is rejected.

## Traceability

- Source artifact: user-provided scan of SP 63.13330.2018 with Amendments 1
  and 2, SHA-256
  `8dfe7fc1af47d6adf2a4d91ed91ee92fe0762abe20a0c54b3c248c7ff138fe00`;
  PDF page 2 confirms the stated amendment composition and dates.
- Source for base `Rb`: clause 6.1.11 and tables 6.8-6.9; reviewed PDF
  pages 24-29.
- Source for `gamma_b1`: clause 6.1.12(a); reviewed PDF page 25.
- Artifact-content status: `CONFIRMED` for the two values and their stated
  conditions.
- Evidence boundary: authenticity, legal status, and currentness beyond
  Amendment 2 remain `OPEN_QUESTION`.
- Architecture impact: `resolve_uls_material_context(...)` owns the mapping and
  exposes `Rb_base`, `gamma_b1`, `Rb_effective`, combination, and profile.
- Engineering verification: independent review is required before release;
  this card does not approve formulas or project use.
- Limitation: other `gamma_bi`, special situations, and combination generation
  remain outside this resolver.
