# K81 User Acceptance Smoke Suite

K81 adds `user-acceptance-smoke`, an aggregated smoke suite for v0.9 readiness
review:

```bash
python -m sp63_core user-acceptance-smoke \
  --output-dir reports/user_acceptance_smoke \
  --json
```

The suite records lightweight statuses for:

- golden validation;
- manual verification cases;
- external validation sample;
- materials audit;
- protected-files guard;
- docs audit;
- project template package;
- clean batch workflow examples;
- release artifact manifest.

The result may be `review_required` while engineer gates remain open. This is
expected and is not a failure of the command.

The suite does not certify designs, approve project use, change formulas,
change material values, implement UI, or make ML project-ready. Engineer review
and deterministic SP63 checks remain mandatory.
