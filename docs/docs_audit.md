# K79 Documentation Link and Command Audit

K79 adds `docs-audit`, a static documentation completeness check:

```bash
python -m sp63_core docs-audit --json
python -m sp63_core docs-audit --output-dir reports/docs_audit_smoke --json
python -m sp63_core docs-audit --markdown
```

The audit checks:

- required documentation files;
- local Markdown links;
- required CLI example snippets;
- mandatory safety flags.

The audit is documentation infrastructure only. It does not execute
deterministic calculations, certify designs, change formulas, change material
values, implement UI, or make ML project-ready.
