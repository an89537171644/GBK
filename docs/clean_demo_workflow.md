# K84 Clean Deterministic Demo Workflow

K84 adds a clean deterministic demo workflow for v0.9 release preparation. The
workflow runs a known rectangular beam input through preflight, deterministic
design report generation, archive validation, ZIP export, and static report
index generation.

The demo input is:

```text
docs/reports/examples/clean_demo/rectangular_clean_demo_input.json
```

Run the workflow:

```bash
python -m sp63_core clean-demo-workflow --output-dir reports/clean_demo_workflow_smoke --json
```

Optional Markdown output:

```bash
python -m sp63_core clean-demo-workflow --output-dir reports/clean_demo_workflow_smoke --markdown
```

The command writes:

- `deterministic_report/`
- `deterministic_report.zip`
- `workflow_summary.json`
- `workflow_summary.md`
- `README_WORKFLOW.md`
- `index.html`
- `clean_demo_workflow.json`
- `clean_demo_workflow.md`

The demo is considered clean when preflight, deterministic report generation,
archive validation, ZIP creation, and static index generation all return
`pass`.

Safety flags are always explicit:

- `requires_engineer_review = true`
- `ml_is_advisory_only = true`
- `deterministic_checks_required = true`
- `ml_ready_for_project_use = false`

K84 does not change calculation formulas, material values, reinforcement
selection, protected calculation files, external validation logic, ML safety
logic, or UI behavior. The demo is release-review evidence only and does not
certify calculations or approve project use.
