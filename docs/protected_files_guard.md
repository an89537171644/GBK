# Protected Files Guard

requires_engineer_review = true

## Purpose

K73 adds a guard that checks whether a branch changed protected calculation,
material-catalog, or external-validation files. It is a release safety aid only
and must not be used as automatic merge approval.

## Protected Files

- `src/sp63_core/checks/bending.py`;
- `src/sp63_core/checks/shear.py`;
- `src/sp63_core/checks/cracking.py`;
- `src/sp63_core/checks/crack_width.py`;
- `src/sp63_core/checks/deflection.py`;
- `src/sp63_core/validation/external.py`;
- `src/sp63_core/materials/concrete.py`;
- `src/sp63_core/materials/rebar.py`.

## CLI

```bash
python -m sp63_core protected-files-check --json
```

Options:

```bash
python -m sp63_core protected-files-check --base-ref main --head-ref HEAD --json
python -m sp63_core protected-files-check --allow-review-required --json
```

K76 adds GitHub Actions ref handling. When `GITHUB_ACTIONS=true`, the guard
records `github_actions_detected = true` and resolves the default base to
`origin/<GITHUB_BASE_REF>` for pull requests or `origin/main` for push jobs.
The JSON output includes `base_ref`, `head_ref`, and `checked_git_ref`.

In CI, the checkout should use `fetch-depth: 0` so the base ref is available:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
```

## Status Rules

- `pass`: git diff was available and no protected files changed.
- `fail`: one or more protected files changed.
- `review_required`: git diff is unavailable, the repository is not a git
  checkout, or refs cannot be compared.

The CLI exits with status code `1` only for `fail`, so a real protected-file
change breaks CI. `review_required` exits with `0` but remains an engineer
review signal.

## Safety

- The guard does not certify a design.
- The guard does not approve a PR for merge.
- Deterministic SP63 checks remain mandatory.
- Engineer review remains mandatory.
- Material verification and external validation remain separate gates.
