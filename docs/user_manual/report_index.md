# Report Index

Use the static report index to navigate generated workflow artifacts:

```bash
python -m sp63_core engineering-report-index \
  --workflow-dir reports/engineering_workflow \
  --json
```

The index is static HTML only. It does not run calculations, start a server,
approve a design, or make ML project-ready.
