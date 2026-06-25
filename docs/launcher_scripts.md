# K86 Launcher Scripts Package

K86 adds lightweight launcher scripts for engineering review workflows.

Run:

```bash
python -m sp63_core launcher-scripts --output-dir reports/launcher_scripts_smoke --json
```

The package writes `.cmd` and `.sh` wrappers for:

- clean deterministic demo workflow;
- single engineering workflow;
- batch engineering workflow;
- opening the clean demo static report index.

The scripts call existing `python -m sp63_core ...` commands only. They do not
contain calculation formulas, start a web server, add UI dependencies, update
materials, or make ML project-ready.

Safety flags:

- `requires_engineer_review = true`
- `ml_is_advisory_only = true`
- `deterministic_checks_required = true`
- `ml_ready_for_project_use = false`
