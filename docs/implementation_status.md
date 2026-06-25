# Implementation status

| module | status | tests | requires_engineer_review | next_action |
|---|---|---|---|---|
| `units.py` | done | yes | no | keep stable |
| `materials/concrete.py` | implemented draft with strength/service values exposed in material audit | yes | yes | engineer must verify values against SP 63 tables before final use |
| `materials/rebar.py` | implemented draft with strength/service values exposed in material audit | yes | yes | engineer must verify values against SP 63 tables before final use |
| `materials/audit.py` | implemented material audit report | yes | yes | engineer must verify values against SP 63 tables before final use |
| `materials/verification.py` | implemented material catalog engineer verification gate with draft/needs_review/engineer_verified statuses | yes | yes | engineer must fill verification CSV before material values are treated as verified |
| `materials/verification_report.py` | implemented Markdown/JSON report integration for engineer-filled material verification CSV | yes | yes | engineer must review needs_review rows before accepting material catalog values |
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
| `report/design_report.py` | implemented draft rectangular design calculation report export in Markdown/HTML/JSON | yes | yes | engineer review report output before project use |
| `report/design_report_input.py` | implemented JSON input loader and traceable report bundle for rectangular design reports | yes | yes | keep input schema explicit and reject unknown critical fields |
| `report/batch_report.py` | implemented batch rectangular design report bundles and shared indexes | yes | yes | engineer review batch report output before project use |
| `report/manifest.py` | implemented report bundle manifest and SHA256 reproducibility metadata | yes | yes | engineer review archived report bundles before project use |
| `report/archive_validation.py` | implemented report archive manifest/checksum/index validation | yes | yes | engineer review archive validation output before relying on report bundles |
| `report/archive_zip.py` | implemented report archive ZIP export and ZIP integrity validation | yes | yes | engineer review ZIP packages before handoff or project archiving |
| `report/review_package.py` | implemented engineering review README for single and batch report packages | yes | yes | engineer review package README before handoff or project archiving |
| `dataset/generator.py` | implemented draft with beam-only MVP, expanded deterministic strength/serviceability output columns and status fields | yes | yes | engineer review enriched dataset ranges before ML readiness gate |
| `dataset/diagnostic.py` | implemented group-diverse scalable deterministic diagnostic dataset with group_key and leakage-safe split | yes | yes | engineer review group diversity before neural-network consideration |
| `dataset/from_reports.py` | implemented ML-ready dataset export from validated report archives | yes | yes | engineer review exported rows before future ML use |
| `dataset/quality_gate.py` | implemented report-derived dataset quality gate for ML readiness | yes | yes | engineer review quality warnings before any ML training |
| `dataset/ml_features.py` | implemented leakage-safe feature and split metadata for report-derived datasets | yes | yes | engineer review feature columns before baseline ML |
| `dataset/synthetic_report_inputs.py` | implemented reproducible synthetic design-report input generation for report-derived ML smoke datasets | yes | yes | use only for synthetic ML experiments; external validation remains separate |
| `dataset/synthetic_balance.py` | implemented synthetic report-derived dataset balance and stratified readiness gate | yes | yes | review class balance and split readiness before synthetic ML experiments |
| `dataset/synthetic_guided.py` | implemented deterministic-guided synthetic input generation for class balancing | yes | yes | use only for synthetic ML experiments; external validation remains separate |
| `dataset/split.py` | implemented with row split and group_key split | yes | no | keep deterministic split stable |
| `dataset/report.py` | implemented with extended K21 report counters for deterministic statuses and serviceability output ranges | yes | no | compare enriched report ranges during dataset review |
| `validation/golden.py` | implemented draft golden-case runner | yes | yes | engineer review expected values and tolerances |
| `validation/manual_cases.py` | implemented manual SP63 verification cases | yes | yes | engineer review manual expected values and tolerances |
| `validation/dataset_checks.py` | implemented dataset batch validation | yes | yes | review validation report before ML |
| `validation/scad_lira_template.py` | implemented manual comparison template | yes | yes | fill with SCAD/LIRA engineer results |
| `validation/external.py` | implemented external validation templates, filled CSV loading, delta export, and strict acceptance gates | yes | yes | fill SCAD/LIRA values manually |
| `validation/external_report.py` | implemented external validation summary workflow with K33 strict real-data CSV intake gate | yes | yes | engineer must fill and review real external values before final acceptance |
| `ml/features.py` | implemented leakage-controlled feature extraction | yes | yes | engineer review before ML use |
| `ml/baseline.py` | implemented target-hygiene baseline ML | yes | yes | retrain models after K12.2 |
| `ml/proposal.py` | implemented ML prediction snapping to reinforcement proposal | yes | yes | engineer review snapping policy |
| `ml/proposal_safety.py` | implemented deterministic verification wrapper for advisory ML proposals | yes | yes | keep all ML proposal acceptance behind deterministic SP63 checks |
| `ml/evaluate.py` | implemented baseline and deterministic safety metrics | yes | yes | review unsafe prediction rate after dataset acceptance |
| `ml/safety.py` | implemented deterministic safety check for reconstructed ML proposal | yes | yes | keep ML advisory only |
| `ml/quality.py` | implemented ML sandbox quality gate | yes | yes | review metrics and external validation before any UI |
| `ml/readiness.py` | implemented deterministic dataset ML readiness gate with diagnostic group diversity and distribution reporting | yes | yes | review unique group counts and leakage before classification ML |
| `ml/baseline_report.py` | implemented non-neural baseline ML report with group-aware group-diverse diagnostic classification evaluation | yes | yes | review expanded diagnostic metrics and leakage warnings before any model promotion |
| `ml/report_baseline.py` | implemented baseline ML report for leakage-safe report-derived features | yes | yes | engineer review metrics before any ML promotion |
| `ml/neural_surrogate.py` | implemented advisory-only neural surrogate smoke MVP | yes | yes | engineer review metrics and deterministic validation before any broader neural-network work |
| `ml/report_neural_surrogate.py` | implemented advisory neural surrogate v2 for leakage-safe report-derived features | yes | yes | engineer review metrics and deterministic verification before any ML proposal use |
| `ml/report_neural_prediction.py` | implemented neural advisory prediction with mandatory deterministic report verification | yes | yes | engineer review prediction/deterministic comparison before any ML proposal use |
| `ml/report_neural_safety_audit.py` | implemented neural advisory safety audit report and proposal-audit wrapper | yes | yes | engineer review audit_status, rejection reasons, and deterministic comparison before any ML proposal use |
| `ml/report_proposal_package.py` | implemented advisory ML proposal package through deterministic safety wrapper | yes | yes | engineer review proposal_status, rejection reasons, and deterministic safety evidence before any ML proposal use |
| `ml/proposal_review_package.py` | implemented engineering review folder and ZIP package for advisory ML proposal handoff | yes | yes | engineer review package manifest, ZIP checksums, and deterministic evidence before any ML proposal use |
| `ml/synthetic_benchmark.py` | implemented large balanced synthetic ML benchmark orchestration | yes | yes | use only for synthetic advisory ML experiments; external validation and engineer review remain mandatory |
| `ml/benchmark_comparison.py` | implemented benchmark model comparison export for baseline and neural synthetic metrics | yes | yes | review model_comparison reports before interpreting synthetic benchmark trends |
| `ml/benchmark_trend.py` | implemented multi-seed synthetic benchmark trend report export | yes | yes | review trend stability across seeds before interpreting benchmark metrics |
| `ml/external_readiness.py` | implemented external validation awareness for ML readiness | yes | yes | provide external validation and material verification CSVs before engineering ML review |
| `ml/material_readiness.py` | implemented material verification coverage readiness for report-derived ML datasets | yes | yes | provide complete engineer-filled material verification CSV before engineering ML review |
| `ml/engineering_readiness_bundle.py` | implemented aggregated engineering ML readiness bundle | yes | yes | review dataset, external validation, material verification, benchmark, and proposal evidence before ML research use |
| `workflows/engineering_workflow.py` | implemented end-to-end engineering workflow runner with optional input preflight, deterministic reports, archive validation, ZIP, static index, and optional ML readiness | yes | yes | use only as review orchestration; engineer review and deterministic SP63 checks remain mandatory |
| `workflows/engineering_workflow_batch.py` | implemented batch engineering workflow runner over input JSON folders with clean batch examples, command/batch status separation, case lists, recommendations, and static batch index | yes | yes | use only as batch review orchestration; failed and review-required cases require engineer review |
| `workflows/self_check.py` | implemented engineering workflow self-check and quickstart readiness layer | yes | yes | run before handoff; self-check does not certify calculations or approve project use |
| `workflows/interface_contract.py` | implemented future GUI/desktop wrapper interface contract | yes | yes | use as planning contract only; no UI implementation and no project approval |
| `workflows/gui_planning.py` | implemented planning-only GUI technology decision with CLI-first static report recommendation | yes | yes | K65 may add static report index/launcher planning without heavy UI dependencies |
| `workflows/project_template.py` | implemented project template package with input/evidence templates, run commands, checklist, and SHA256 manifest | yes | yes | use as handoff scaffold only; engineer must fill evidence and review deterministic outputs |
| `workflows/static_report_index.py` | implemented static HTML workflow report index over generated engineering workflow artifacts, including optional preflight report links | yes | yes | use as static navigation only; no calculations, server, GUI framework, or project approval |
| `workflows/input_form_schema.py` | implemented future UI input JSON form schema and validation hints | yes | yes | use as metadata only; no UI implementation, no calculations, and no ML project-use approval |
| `workflows/input_preflight.py` | implemented input JSON preflight validator and engineering validation report | yes | yes | run before engineering workflow or future GUI launcher; report only and no calculations |
| `workflows/static_input_form_preview.py` | implemented static HTML preview of the input form schema | yes | yes | use as read-only preview only; no calculations, JavaScript calculator, server, or project approval |
| `workflows/diagnostics_catalog.py` | implemented human-friendly EN/RU diagnostics catalog for workflow errors and warnings | yes | yes | use as guidance metadata only; deterministic checks and engineer review remain mandatory |
| `workflows/docs_audit.py` | implemented documentation link and CLI command audit for v0.9 readiness documentation | yes | yes | use as completeness check only; audit does not approve project use |
| `workflows/evidence_templates.py` | implemented external/material evidence templates package with SHA256 manifest | yes | yes | engineer must fill templates manually; package does not approve project use |
| `workflows/material_verification_closure.py` | implemented material verification closure report for engineer-filled CSV coverage | yes | yes | use to decide readiness for engineering review only; project use remains false and catalog values are not changed |
| `workflows/clean_demo_workflow.py` | implemented clean deterministic demo workflow for preflight/report/archive/ZIP/index smoke validation | yes | yes | use as v0.9 review evidence only; project use remains false |
| `workflows/protected_files_guard.py` | implemented protected files guard for formula/material/external validation release checks with GitHub Actions ref handling | yes | yes | use as review aid only; guard does not approve merge or project use |
| `.github/workflows/safety.yml` | implemented CI safety workflow for pytest, ruff, golden/manual/external validation, protected-files guard, and release-candidate smoke | yes | yes | keep fetch-depth 0 so protected-files guard has reliable base refs |
| `workflows/user_manual_index.py` | implemented user manual package completeness index | yes | yes | keep manual updated with workflow changes; manual does not certify project use |
| `workflows/user_acceptance_smoke.py` | implemented aggregated user acceptance smoke suite for v0.9 readiness review | yes | yes | use as review evidence only; smoke suite does not certify project use |
| `workflows/release_candidate.py` | implemented draft v0.9 release candidate report across validation/workflow/manual guard statuses | yes | yes | review report before any release; report does not certify project use |
| `workflows/release_manifest.py` | implemented release artifact manifest with version, git metadata, and SHA256 checksums | yes | yes | use as reproducibility metadata only; manifest does not publish or certify a release |
| `workflows/v09_readiness.py` | implemented final aggregated v0.9 readiness gate across protected files, docs, release manifest, user acceptance smoke, and release candidate report | yes | yes | review readiness gate output before any release; gate does not publish, certify, or approve project use |
| `cli.py` | implemented with subcommands including crack formation, crack width, deflection, separated design statuses, and input-driven design report export | yes | no | keep report/export commands smoke-tested |
| `automation/codex workflow` | implemented issue/PR workflow docs and templates | no | no | protect main branch in GitHub settings |
| `validation_report.md` | draft validation report | yes | yes | engineer review |
| transverse reinforcement selection | implemented draft | yes | yes | engineer review of selected schemes |
| ML | experimental baseline sandbox implemented | yes | yes | advisory only; deterministic checks mandatory |
| UI | planning contract, technology decision, static report index, input form schema, input preflight reporting, workflow preflight integration, and static input form preview only | yes | yes | full UI implementation remains a separate approved step |
