# CLI Status And Exit-Code Contract

K91 defines a stable status and shell exit-code contract for user-facing CLI
commands.

This contract is automation guidance only. It does not certify designs, approve
project use, or make ML project-ready.

requires_engineer_review = true
ml_is_advisory_only = true
deterministic_checks_required = true
ml_ready_for_project_use = false

## Status Mapping

| status | exit code | meaning |
|---|---:|---|
| `pass` | 0 | command completed and reported a passing review status |
| `review_required` | 0 | command completed, but engineer review remains mandatory |
| `fail` | 1 | command completed and reported a blocking failure |

Invalid CLI usage and uncaught technical errors keep standard argparse or Python
nonzero behavior.

## CI Notes

- `protected-files-check` status `fail` is a CI blocker.
- `review_required` is not treated as shell failure because review evidence can
  be generated successfully while still requiring an engineer.
- Deterministic SP63 checks remain mandatory before project use.
- ML output remains advisory-only and cannot approve a design.

## Command

```bash
python -m sp63_core cli-status-contract --json
python -m sp63_core cli-status-contract --markdown
python -m sp63_core cli-status-contract --output-dir reports/cli_status_contract_smoke --json
```
