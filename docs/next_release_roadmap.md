# Next Release Roadmap

K106 adds a formal roadmap for work after the v0.9 review build.

Sections:

- v0.9 internal review;
- v0.9 user trial;
- v1.0 engineering release;
- GUI/launcher milestone;
- material verification milestone;
- external validation milestone;
- ML advisory maturity milestone;
- installer/packaging milestone.

The roadmap is planning evidence only and does not approve project use.

```bash
python -m sp63_core next-release-roadmap --output-dir reports/next_release_roadmap_smoke --json
```

K107 consumes the roadmap in the v0.9 review closure command:

```bash
python -m sp63_core v09-review-closure --output-dir reports/v09_review_closure_smoke --version 0.9.0-rc1 --json
```

The next roadmap step after closure remains manual engineer review and external
validation evidence, not automatic project approval.

K108 creates the final package for that manual review:

```bash
python -m sp63_core v09-release-candidate-package --output-dir reports/v09_release_candidate_package_smoke --version 0.9.0-rc1 --json
```

The package remains `review_required` while manual review gates remain open.
