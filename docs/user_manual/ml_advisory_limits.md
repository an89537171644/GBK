# ML Advisory Limits

ML and neural surrogate outputs are advisory-only.

Rules:

- ML is not a design checker.
- ML output must not be used as a project decision.
- Every ML proposal must pass deterministic SP63 verification.
- `ml_ready_for_project_use` remains false.
- Engineer review remains mandatory.

Use:

```bash
python -m sp63_core ml-proposal-verify --json
```

for the deterministic wrapper smoke check.
