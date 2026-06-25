# JSON Output Contract

K92 documents lightweight JSON output contracts for the main workflow and
review commands.

The project intentionally avoids adding a heavy JSON schema dependency here.
Each contract records:

- `command`;
- `required_keys`;
- `status_keys`;
- `boolean_safety_keys`.

requires_engineer_review = true
ml_is_advisory_only = true
deterministic_checks_required = true
ml_ready_for_project_use = false

## Command

```bash
python -m sp63_core json-output-contract --json
python -m sp63_core json-output-contract --markdown
python -m sp63_core json-output-contract --output-dir reports/json_output_contract_smoke --json
```

## Safety

- JSON output contracts do not approve project use.
- `ml_ready_for_project_use` remains false.
- Deterministic SP63 checks remain mandatory.
- Engineer review remains mandatory.
