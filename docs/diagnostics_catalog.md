# Diagnostics Catalog

requires_engineer_review = true

## Purpose

K70 adds a human-friendly diagnostics catalog for workflow-facing errors and
warnings. It is intended for CLI output, static report indexes, future workflow
launchers, and future documentation links.

The catalog is metadata only. It does not run deterministic calculations, does
not change formulas, does not change materials, and does not approve project
use.

## CLI

Print JSON:

```bash
python -m sp63_core diagnostics-catalog --json
```

Print Markdown:

```bash
python -m sp63_core diagnostics-catalog --markdown
```

Write files:

```bash
python -m sp63_core diagnostics-catalog \
  --output-dir reports/diagnostics_catalog \
  --json
```

The output directory contains:

- `diagnostics_catalog.json`;
- `diagnostics_catalog.md`.

## Categories

The catalog includes these categories:

- `input_preflight`;
- `geometry`;
- `materials`;
- `loads`;
- `workflow`;
- `archive`;
- `zip`;
- `ml_readiness`;
- `protected_files`;
- `release_candidate`.

## Diagnostic Fields

Each diagnostic includes:

- `code`;
- `category`;
- `severity`: `info`, `warning`, or `error`;
- `title_en`;
- `title_ru`;
- `message_en`;
- `message_ru`;
- `recommended_action_en`;
- `recommended_action_ru`;
- `related_command`.

## Safety

- Diagnostics are guidance messages only.
- Deterministic SP63 checks remain mandatory.
- Engineer review remains mandatory.
- ML remains advisory-only.
- `ml_ready_for_project_use` remains false.
- The catalog must not be used to approve a design.
