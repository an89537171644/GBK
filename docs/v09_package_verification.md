# v0.9 Package Verification

K109 adds verification for the v0.9 release candidate package produced by K108.

Verify an existing package:

```bash
python -m sp63_core v09-package-verify \
  --package-dir reports/v09_release_candidate_package_smoke \
  --output-dir reports/v09_package_verification_smoke \
  --json
```

Build the K108 package first, then verify it:

```bash
python -m sp63_core v09-package-verify \
  --build \
  --output-dir reports/v09_package_verification_smoke \
  --version 0.9.0-rc1 \
  --json
```

Markdown output is also available:

```bash
python -m sp63_core v09-package-verify \
  --package-dir reports/v09_release_candidate_package_smoke \
  --output-dir reports/v09_package_verification_markdown_smoke \
  --markdown
```

The verifier writes:

- `v09_package_verification.json`;
- `v09_package_verification.md`;
- `README_V09_PACKAGE_VERIFICATION.md`;
- `manual_acceptance_log_template.md`.

The checks cover:

- required package files and artifact folders;
- ZIP entries for start-here README, release README, manifest, known
  limitations, signoff templates, engineer review packet, clean demo evidence,
  and release acceptance checklist;
- forbidden smoke folders, caches, full SP 63 text markers, private/personal
  document markers, SCAD/LIRA files, CAD/BIM files, secrets, and tokens;
- manifest file coverage and SHA256 checksums where practical.

Expected normal status is `review_required` when the package is complete but
manual review gates remain open. With zero critical verification errors,
`ready_for_manual_review = true`.

Safety flags:

- `requires_engineer_review = true`
- `ml_is_advisory_only = true`
- `deterministic_checks_required = true`
- `ml_ready_for_project_use = false`
- `ready_for_project_use = false`

K109 does not publish a release, certify calculations, approve project use,
change formulas, change material values, implement UI, or make ML a calculator.
