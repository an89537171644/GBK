# Implementation status

| module | status | tests | requires_engineer_review | next_action |
|---|---|---|---|---|
| `units.py` | done | yes | no | keep stable |
| `materials/concrete.py` | implemented draft with strength and service properties Rb/Rbt/Rbser/Rbtser | yes | yes | engineer review of SP63 table values before crack calculations |
| `materials/rebar.py` | implemented draft with `Rsc_short`/`Rsc_long` | yes | yes | engineer review of material values |
| `sections/rectangular.py` | implemented with `h0_override` validation | yes | no | keep geometry checks covered |
| `checks/bending.py` | implemented with `load_duration` support | yes | yes | engineer review of formula card and golden cases |
| `checks/shear.py` | implemented with draft transverse reinforcement counting warnings | yes | yes | engineer review of formula card and golden cases |
| `checks/cracking.py` | implemented draft normal crack formation check | yes | yes | crack width check acrc |
| `rebar/constructive.py` | implemented draft constructive checks | yes | yes | engineer review |
| `rebar/longitudinal.py` | implemented with h0 recalculation and draft single-layer layout check | yes | yes | engineer review of layout assumptions |
| `rebar/transverse.py` | implemented draft transverse reinforcement selection | yes | yes | engineer review of spacing and legs assumptions |
| `design/rectangular.py` | implemented draft end-to-end rectangular design | yes | yes | engineer review and CLI integration |
| `report/protocol.py` | draft | yes | yes | keep protocol structure stable |
| `dataset/generator.py` | implemented draft with beam-only MVP, expanded columns including cover, stirrup geometry consistency, and shuffled full-grid limit | yes | yes | engineer review dataset ranges |
| `dataset/split.py` | implemented with row split and group_key split | yes | no | keep deterministic split stable |
| `dataset/report.py` | implemented with extended K8 report counters | yes | no | compare report ranges during dataset review |
| `validation/golden.py` | implemented draft golden-case runner | yes | yes | engineer review expected values and tolerances |
| `validation/dataset_checks.py` | implemented dataset batch validation | yes | yes | review validation report before ML |
| `validation/scad_lira_template.py` | implemented manual comparison template | yes | yes | fill with SCAD/LIRA engineer results |
| `validation/external.py` | implemented external validation templates, filled CSV loading, delta export, and strict acceptance gates | yes | yes | fill SCAD/LIRA values manually |
| `ml/features.py` | implemented leakage-controlled feature extraction | yes | yes | engineer review before ML use |
| `ml/baseline.py` | implemented target-hygiene baseline ML | yes | yes | retrain models after K12.2 |
| `ml/proposal.py` | implemented ML prediction snapping to reinforcement proposal | yes | yes | engineer review snapping policy |
| `ml/evaluate.py` | implemented baseline and deterministic safety metrics | yes | yes | review unsafe prediction rate after dataset acceptance |
| `ml/safety.py` | implemented deterministic safety check for reconstructed ML proposal | yes | yes | keep ML advisory only |
| `ml/quality.py` | implemented ML sandbox quality gate | yes | yes | review metrics and external validation before any UI |
| `cli.py` | implemented with subcommands | yes | no | dataset split and ML preparation |
| `validation_report.md` | draft validation report | yes | yes | engineer review |
| transverse reinforcement selection | implemented draft | yes | yes | engineer review of selected schemes |
| ML | experimental baseline sandbox implemented | yes | yes | advisory only; deterministic checks mandatory |
| UI | not started | no | yes | separate approved step |
