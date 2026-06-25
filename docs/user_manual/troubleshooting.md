# Troubleshooting

Use the diagnostics catalog for common workflow messages:

```bash
python -m sp63_core diagnostics-catalog --markdown
```

Common actions:

- fix preflight errors before running deterministic workflow;
- regenerate report bundles when archive validation fails;
- rerun ZIP export when ZIP output is missing;
- provide engineer-filled material/external validation CSVs before final
  review;
- run `protected-files-check` before release-candidate review;
- use `cli-status-contract` to check which CLI statuses are shell failures.

CLI status contract:

```bash
python -m sp63_core cli-status-contract --json
```
