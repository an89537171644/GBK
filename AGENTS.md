# AGENTS.md

## Project context

GBK is a research draft-MVP for reinforced concrete calculation according to
selected parts of SP 63 and for ML-assisted reinforcement selection.

The deterministic calculation core is the authority.
ML is advisory-only.
Every ML proposal must be checked by deterministic sp63_core.

## Codex automation rules

Codex must work through feature branches and pull requests.

Rules:

- Never push directly to main.
- Never merge pull requests automatically.
- Work on exactly one task or issue at a time.
- Create a branch named:
  codex/<issue-number>-<short-task-name>
- Run:
  python -m pytest
  ruff check .
- If the task touches validation, dataset, or ML, run the relevant CLI smoke
  tests from docs/codex_automation_plan.md.
- Show changed files, test results, ruff result, and commit hash.
- Stop after opening a pull request.
- Do not proceed to the next issue unless explicitly instructed.
- Do not change engineering formulas unless the issue explicitly allows it.
- Do not implement ML as a final calculator.
- All engineering formulas must remain deterministic and must include
  requires_engineer_review = true.
- ML outputs are advisory only and must be checked by deterministic sp63_core.
- Full text of SP 63 must not be committed.
- Personal data, grant application files, passports, phones, signatures, and
  private documents must not be committed.
- If a task requests access to private/grant documents, summarize only what is
  necessary and never commit personal data.

## Engineering rules

- Do not change formulas in checks/bending.py or checks/shear.py unless the
  issue explicitly approves formula changes.
- New SP63 formula modules must have:
  - docs/formulas/... card;
  - tests;
  - requires_engineer_review = true;
  - validation or golden case when possible.
- Strength checks, serviceability checks, dataset generation, and ML must remain
  separated.
- Deterministic checks are mandatory for every ML proposal.

## Required checks

Always run:

python -m pytest
ruff check .

For validation changes also run:

python -m sp63_core validate --golden
python -m sp63_core validate --generate-dataset-limit 20 --json

For dataset changes also run:

python -m sp63_core generate-dataset --limit 20 --split --group-split --output-dir data/generated --prefix smoke_dataset --report reports/interim/smoke_dataset_report.json

For ML changes also run:

python -m sp63_core train-baseline --generate-dataset-limit 50 --model-output models/smoke_baseline.pkl --metrics-output reports/interim/smoke_baseline_metrics.json

## Pull Request rules

Every Codex task must end with a Pull Request.

PR must include:

- issue link;
- changed files;
- tests run;
- pytest result;
- ruff result;
- engineering review notes;
- statement that main was not directly modified;
- statement that ML remains advisory-only if ML was touched.
