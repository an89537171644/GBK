# Static Launcher Dashboard

K102 adds a minimal static local launcher dashboard. It is not a GUI framework,
not a web server, and not a project approval interface.

The dashboard provides:

- copyable CLI commands;
- links to clean demo outputs;
- links to portable package notes;
- links to the user manual;
- links to report indexes;
- safety warnings.

It contains no JavaScript calculations and keeps:

- `ml_ready_for_project_use = false`;
- `project_use_allowed = false`;
- deterministic SP63 checks mandatory;
- engineer review mandatory.

```bash
python -m sp63_core static-launcher-dashboard --output-dir reports/static_launcher_dashboard_smoke --json
```
