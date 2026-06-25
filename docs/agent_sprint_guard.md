# K89 Agent Sprint Guard

K89 adds a local sprint guard for checking expected K-step artifacts.

Run:

```bash
python -m sp63_core agent-sprint-guard --from-k 83 --to-k 90 --json
```

The guard checks whether required module, test, and documentation files exist
for each K-step in the requested range. If a step is missing, the command
returns `review_required` and reports `proposed_next_k`.

This is a local completeness check only. It does not inspect GitHub issues,
open pull requests, branch protection, or CI status. It also does not approve a
merge, publish a release, certify calculations, or approve project use.

Safety flags:

- `requires_engineer_review = true`
- `ml_is_advisory_only = true`
- `deterministic_checks_required = true`
- `ml_ready_for_project_use = false`
