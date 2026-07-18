# Material Verification Closure Workflow

K83 adds a closure workflow for the material verification review gate:

`tests/fixtures/material_verification_sample.csv` is a synthetic, test-only,
non-evidence fixture. Every row has
`evidence_kind = synthetic_test_fixture`, so the parser must downgrade any
infrastructure `engineer_verified` label to `needs_review` and the sample must
produce `review_required`. It must never be substituted for an engineer-filled
CSV or cited as material verification evidence.

```bash
python -m sp63_core material-verification-closure \
  --material-verification-csv tests/fixtures/material_verification_sample.csv \
  --output-dir reports/material_verification_closure_smoke \
  --json
```

Markdown output can be printed without writing files:

```bash
python -m sp63_core material-verification-closure \
  --material-verification-csv tests/fixtures/material_verification_sample.csv \
  --no-output-files \
  --markdown
```

The workflow checks current catalog material property keys against an
engineer-filled material verification CSV. It reports:

- required material keys;
- verified material keys;
- missing material keys;
- rejected material keys;
- review-required material keys;
- coverage ratio;
- `material_ready_for_engineering_review`;
- `material_ready_for_project_use = false`.

Output files:

```text
material_verification_closure.json
material_verification_closure.md
README_MATERIAL_VERIFICATION_CLOSURE.md
```

Status logic:

- no CSV: `review_required`;
- incomplete CSV: `review_required`;
- rejected rows: `fail`;
- all required keys engineer-verified with
  `evidence_kind = independent_engineer_evidence`: `pass` and
  `material_ready_for_engineering_review = true`;
- `material_ready_for_project_use` always remains `false`.

This workflow does not change material values, does not update the material
catalog, does not include full SP 63 text, and does not approve project use.
Engineer review remains mandatory.
