# Clean Deterministic Demo

This folder contains a public synthetic rectangular beam input for the clean
deterministic workflow demo.

Run:

```bash
python -m sp63_core clean-demo-workflow --output-dir reports/clean_demo_workflow_smoke --json
```

The demo runs input preflight, deterministic report generation, archive
validation, ZIP export, and static report index generation. It does not run ML
readiness, does not use external/material evidence CSV files, and does not
approve project use.

