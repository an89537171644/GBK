# v0.9 Release Candidate Package

K108 adds the final v0.9 release candidate package command for engineering
review.

Run:

```bash
python -m sp63_core v09-release-candidate-package \
  --output-dir reports/v09_release_candidate_package_smoke \
  --version 0.9.0-rc1 \
  --json
```

Markdown output is also available:

```bash
python -m sp63_core v09-release-candidate-package \
  --output-dir reports/v09_release_candidate_package_markdown_smoke \
  --version 0.9.0-rc1 \
  --markdown
```

The package writes:

- `README_START_HERE.md`;
- `README_RELEASE_CANDIDATE.md`;
- `v09_release_candidate_package.json`;
- `v09_release_candidate_package.md`;
- `v09_release_candidate_manifest.json`;
- `v09_release_candidate_package.zip`;
- compact artifact evidence under `artifacts/`.

Included evidence:

- review closure;
- review build;
- freeze report;
- final audit;
- clean demo and clean demo verification;
- engineer review packet;
- release acceptance checklist;
- review signoff templates;
- Windows smoke plan;
- release notes;
- known limitations;
- release bundle.

Expected normal status is `review_required` because manual review gates remain
open. With no critical failures, `ready_for_engineering_review = true`.

Safety flags:

- `requires_engineer_review = true`
- `ml_is_advisory_only = true`
- `deterministic_checks_required = true`
- `ml_ready_for_project_use = false`
- `ready_for_project_use = false`

K108 does not publish a release, certify calculations, approve project use,
change formulas, change material values, implement UI, or make ML a calculator.

## Verification

K109 adds a verifier for this package:

```bash
python -m sp63_core v09-package-verify \
  --package-dir reports/v09_release_candidate_package_smoke \
  --output-dir reports/v09_package_verification_smoke \
  --json
```

Use `--build` to create a fresh K108 package before verification. The verifier
checks required package files, ZIP contents, forbidden file exclusions, and
manifest checksum coverage where practical. It writes
`v09_package_verification.json`, `v09_package_verification.md`,
`README_V09_PACKAGE_VERIFICATION.md`, and
`manual_acceptance_log_template.md`.

Manual review gates keep the expected status at `review_required`, while
`ready_for_manual_review = true` is possible when critical verification errors
are zero. Project use and ML project readiness remain false.
