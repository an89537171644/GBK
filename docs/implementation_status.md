# Implementation status

| module | status | tests | requires_engineer_review | next_action |
|---|---|---|---|---|
| `units.py` | done | yes | no | keep stable |
| `materials/concrete.py` | implemented draft with strength/service values exposed in material audit | yes | yes | engineer must verify values against SP 63 tables before final use |
| `materials/rebar.py` | implemented draft with strength/service values exposed in material audit | yes | yes | engineer must verify values against SP 63 tables before final use |
| `materials/audit.py` | implemented material audit report | yes | yes | engineer must verify values against SP 63 tables before final use |
| `sections/rectangular.py` | implemented with `h0_override` validation | yes | no | keep geometry checks covered |
| `checks/bending.py` | implemented with `load_duration` support | yes | yes | engineer review of formula card and golden cases |
| `checks/shear.py` | implemented with draft transverse reinforcement counting warnings | yes | yes | engineer review of formula card and golden cases |
| `checks/cracking.py` | implemented draft normal crack formation check | yes | yes | keep as Mcrc input to crack width |
| `checks/crack_width.py` | implemented draft normal crack width check | yes | yes | keep as input to serviceability review |
| `checks/deflection.py` | implemented draft curvature and deflection check | yes | yes | engineer review and future long-term/refined serviceability model |
| `rebar/constructive.py` | implemented draft constructive checks | yes | yes | engineer review |
| `rebar/longitudinal.py` | implemented with h0 recalculation and draft single-layer layout check | yes | yes | engineer review of layout assumptions |
| `rebar/transverse.py` | implemented draft transverse reinforcement selection | yes | yes | engineer review of spacing and legs assumptions |
| `design/rectangular.py` | implemented draft end-to-end rectangular design with separated strength, serviceability, and overall statuses | yes | yes | engineer review and CLI integration |
| `report/protocol.py` | implemented separated strength_status, serviceability_status, and overall_status; legacy status aliases overall_status | yes | yes | keep protocol structure stable |
| `dataset/generator.py` | implemented draft with beam-only MVP, expanded deterministic strength/serviceability output columns and status fields | yes | yes | engineer review enriched dataset ranges before ML readiness gate |
| `dataset/diagnostic.py` | implemented group-diverse scalable deterministic diagnostic dataset with group_key and leakage-safe split | yes | yes | engineer review group diversity before neural-network consideration |
| `dataset/split.py` | implemented with row split and group_key split | yes | no | keep deterministic split stable |
| `dataset/report.py` | implemented with extended K21 report counters for deterministic statuses and serviceability output ranges | yes | no | compare enriched report ranges during dataset review |
| `validation/golden.py` | implemented draft golden-case runner | yes | yes | engineer review expected values and tolerances |
| `validation/manual_cases.py` | implemented manual SP63 verification cases | yes | yes | engineer review manual expected values and tolerances |
| `validation/dataset_checks.py` | implemented dataset batch validation | yes | yes | review validation report before ML |
| `validation/scad_lira_template.py` | implemented manual comparison template | yes | yes | fill with SCAD/LIRA engineer results |
| `validation/external.py` | implemented external validation templates, filled CSV loading, delta export, and strict acceptance gates | yes | yes | fill SCAD/LIRA values manually |
| `validation/external_report.py` | implemented external validation summary workflow with K32 filled synthetic/manual sample acceptance report | yes | yes | engineer must fill and review real external values before final acceptance |
| `ml/features.py` | implemented leakage-controlled feature extraction | yes | yes | engineer review before ML use |
| `ml/baseline.py` | implemented target-hygiene baseline ML | yes | yes | retrain models after K12.2 |
| `ml/proposal.py` | implemented ML prediction snapping to reinforcement proposal | yes | yes | engineer review snapping policy |
| `ml/proposal_safety.py` | implemented deterministic verification wrapper for advisory ML proposals | yes | yes | keep all ML proposal acceptance behind deterministic SP63 checks |
| `ml/evaluate.py` | implemented baseline and deterministic safety metrics | yes | yes | review unsafe prediction rate after dataset acceptance |
| `ml/safety.py` | implemented deterministic safety check for reconstructed ML proposal | yes | yes | keep ML advisory only |
| `ml/quality.py` | implemented ML sandbox quality gate | yes | yes | review metrics and external validation before any UI |
| `ml/readiness.py` | implemented deterministic dataset ML readiness gate with diagnostic group diversity and distribution reporting | yes | yes | review unique group counts and leakage before classification ML |
| `ml/baseline_report.py` | implemented non-neural baseline ML report with group-aware group-diverse diagnostic classification evaluation | yes | yes | review expanded diagnostic metrics and leakage warnings before any model promotion |
| `ml/neural_surrogate.py` | implemented advisory-only neural surrogate smoke MVP | yes | yes | engineer review metrics and deterministic validation before any broader neural-network work |
| `cli.py` | implemented with subcommands including crack formation, crack width, deflection, and separated design statuses | yes | no | dataset split and ML preparation |
| `automation/codex workflow` | implemented issue/PR workflow docs and templates | no | no | protect main branch in GitHub settings |
| `validation_report.md` | draft validation report | yes | yes | engineer review |
| transverse reinforcement selection | implemented draft | yes | yes | engineer review of selected schemes |
| ML | experimental baseline sandbox implemented | yes | yes | advisory only; deterministic checks mandatory |
| UI | not started | no | yes | separate approved step |
