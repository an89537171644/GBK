# Implementation status

| module | status | tests | requires_engineer_review | next_action |
|---|---|---|---|---|
| `units.py` | done | yes | no | keep stable |
| `materials/concrete.py` | draft | yes | yes | engineer review of material values |
| `materials/rebar.py` | draft with `Rsc_long`/`Rsc_short` load-duration support | yes | yes | engineer review of material values |
| `sections/rectangular.py` | implemented | yes | no | keep geometry checks covered |
| `checks/bending.py` | implemented | yes | yes | engineer review of formula card and golden cases |
| `checks/shear.py` | implemented | yes | yes | engineer review of formula card and golden cases |
| `rebar/longitudinal.py` | implemented with h0 recalculation and draft single-layer layout check | yes | yes | engineer review of layout assumptions |
| `services/rectangular_design.py` | draft end-to-end deterministic design service | yes | yes | engineer review of selected reinforcement workflow |
| `cli.py` | implemented with subcommands for demo, checks, selection, design, and dataset generation | yes | yes | keep CLI examples synced with service changes |
| `report/protocol.py` | draft | yes | yes | keep protocol structure stable |
| `report/export.py` | JSON and HTML protocol export | yes | yes | add PDF only in a separate approved step |
| `dataset/generator.py` | draft with design-service rows and deterministic splits | yes | yes | engineer review dataset ranges before ML use |
| transverse reinforcement selection | draft implemented | yes | yes | engineer review of stirrup selection assumptions |
| `ml/features.py` | baseline feature preparation for `As_required` prediction | yes | yes | deterministic checks remain mandatory |
| `ml/baseline.py` | draft RandomForest baseline for `As_required` prediction only | yes | yes | do not use as final engineering decision |
| `ml/neural.py` | draft MLPRegressor surrogate for `As_required` prediction only | yes | yes | do not use as final engineering decision |
| `ml/safe_suggestions.py` | deterministic guard for ML-assisted longitudinal suggestions | yes | yes | keep unsafe_accept_rate at 0 |
| Streamlit prototype | implemented draft in `apps/streamlit_app.py` | yes | yes | manual UI review before demonstration |
| validation golden cases | draft JSON cases with automated checks | yes | yes | engineer approval required before acceptance |
| `docs/validation` | detailed validation plan and SCAD/LIRA template | no | yes | fill comparisons with engineer-reviewed results |
| release documentation | implemented draft user/developer/release docs | no | yes | review before grant/report publication |
