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

Run the clean deterministic demo workflow:

```bash
python -m sp63_core clean-demo-workflow \
  --output-dir reports/clean_demo_workflow_smoke \
  --json
```

The clean demo uses a known passing input and verifies preflight, deterministic
report generation, archive validation, ZIP creation, and static report index
generation. It is review evidence only and still requires engineer review.

Create a Windows-oriented portable command skeleton:

```bash
python -m sp63_core portable-package --output-dir reports/portable_package_smoke --json
```

The package contains `.cmd` files that call existing `python -m sp63_core`
commands. It does not add UI dependencies and does not certify designs.
