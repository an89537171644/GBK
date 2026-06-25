# Quickstart

Run the core smoke checks:

```bash
python -m sp63_core validate --golden
python -m sp63_core manual-cases --json
python -m sp63_core external-validation --sample --json
```

Run a single workflow:

```bash
python -m sp63_core engineering-workflow \
  --input-json docs/reports/examples/rectangular_design_input_example.json \
  --output-dir reports/engineering_workflow_full_smoke \
  --with-preflight \
  --with-index \
  --json
```

Review generated reports manually. Do not treat any generated file as project
approval.
