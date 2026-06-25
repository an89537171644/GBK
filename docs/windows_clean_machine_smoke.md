# Windows Clean-Machine Smoke

K100 adds a review-only Windows smoke plan. It generates command files that an
engineer can run manually on a clean Windows machine.

The generated plan covers:

- Python version check;
- virtual environment creation;
- package installation;
- `validate --golden`;
- `clean-demo-workflow`;
- opening generated report indexes;
- `protected-files-check`;
- `release-bundle`;
- a reminder that generated artifacts must not be committed.

The workflow does not create an executable and does not certify project use.

```bash
python -m sp63_core windows-smoke-plan --output-dir reports/windows_smoke_plan_smoke --json
```
