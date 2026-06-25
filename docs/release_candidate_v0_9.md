# Release Candidate v0.9 Report

requires_engineer_review = true

## Purpose

K75 adds a draft release candidate report for the current engineering workflow
package. It gathers validation and workflow statuses without publishing a
release and without certifying project use.

## CLI

```bash
python -m sp63_core release-candidate-report \
  --output-dir reports/release_candidate_v0_9 \
  --json
```

Optional version:

```bash
python -m sp63_core release-candidate-report \
  --output-dir reports/release_candidate_v0_9 \
  --version 0.9.0-rc1 \
  --markdown
```

## Output Files

```text
reports/release_candidate_v0_9/
  release_candidate_report.json
  release_candidate_report.md
  README_RELEASE_CANDIDATE.md
```

## Collected Statuses

- golden validation status;
- manual verification cases status;
- material audit status;
- material verification closure status can be added from an engineer-filled
  verification CSV;
- external validation sample status;
- engineering workflow self-check status;
- input form schema status;
- input preflight status;
- static report index status;
- protected files guard status;
- user manual status.

## Known Limitations

- not certified;
- engineer review required;
- material audit review_required;
- material verification closure does not update material catalogs or approve
  project use;
- external validation sample is limited;
- ML advisory-only;
- no project use approval;
- no full GUI yet.

## Safety

- The report does not publish a release.
- The report does not certify designs.
- Deterministic SP63 checks remain mandatory.
- Engineer review remains mandatory.
- ML remains advisory-only.
- `ml_ready_for_project_use` remains false.
