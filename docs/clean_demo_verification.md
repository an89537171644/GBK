# Clean Demo Verification

K94 verifies that the clean deterministic demo workflow produced all expected
user-facing artifacts.

requires_engineer_review = true
ml_is_advisory_only = true
deterministic_checks_required = true
ml_ready_for_project_use = false

## Commands

Verify an existing clean demo workflow directory:

```bash
python -m sp63_core clean-demo-verify --workflow-dir reports/clean_demo_workflow_smoke --json
```

Run the clean demo and verify generated artifacts:

```bash
python -m sp63_core clean-demo-verify --run --output-dir reports/clean_demo_verify_smoke --json
```

## Checked Artifacts

- preflight JSON and Markdown;
- deterministic report Markdown, JSON, HTML, manifest, and review README;
- deterministic report ZIP;
- workflow summary JSON and Markdown;
- workflow README;
- static `index.html`;
- `ml_ready_for_project_use` must not be true.

This verification is release-review evidence only and does not certify designs.
