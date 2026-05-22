# Engineering Audit

requires_engineer_review = true

## Implemented

- Draft material catalogs for heavy concrete B15-B40 and reinforcement A240/A400/A500.
- Rectangular section geometry with effective depth handling.
- Draft bending check for rectangular sections.
- Draft shear check for rectangular sections.
- Longitudinal reinforcement selection with layout and constructive filters.
- Transverse reinforcement selection with shear and constructive filters.
- End-to-end rectangular element design workflow.
- CLI scenarios for checks, selection, design, and dataset generation.

## Applicability Boundaries

- Rectangular bending elements only.
- Heavy concrete and MVP reinforcement classes only.
- Units follow the project convention: N, mm, MPa.
- Results are draft engineering outputs and require review before production use.

## Requires Engineering Review

- Material values and load-duration assumptions.
- Bending and shear formula cards and golden cases.
- Constructive limits and edge cases.
- Reinforcement layout assumptions.
- Dataset ranges before bulk generation.

## Not Implemented

- Serviceability limit states, including cracks and deflections.
- T-sections, columns, punching, torsion, prestress, anchorage, and support zones.
- HTML/PDF protocol rendering.
- ML training and ML-backed recommendations.
- Streamlit or other UI.

## Why ML Is Not A Final Calculation Stage Yet

The deterministic calculation core is still draft and requires engineering review.
ML can only be used after the calculation rules, constructive filters, datasets,
and validation cases are reviewed. Even then, ML output must remain advisory and
must be checked by deterministic SP 63 calculation modules.

## Next Stages

- Engineer review of material catalogs and formula cards.
- Engineer review of constructive checks.
- Dataset split and validation policy.
- Golden-case expansion.
- ML preparation only after deterministic checks are accepted.
