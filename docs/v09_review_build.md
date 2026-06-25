# v0.9 Review Build

K105 adds one command that generates the v0.9 review build packet.

It creates a top-level report plus an `artifacts/` folder containing:

- clean demo workflow;
- clean demo verification;
- portable package;
- release bundle;
- traceability matrix;
- v10 gap report;
- v09 freeze report;
- freeze remediation plan;
- engineer review packet;
- static launcher dashboard;
- release acceptance checklist;
- review signoff templates.

The build remains `review_required` while manual material, external validation,
and engineer signoff gates remain open. It does not approve project use.

```bash
python -m sp63_core v09-review-build --output-dir reports/v09_review_build_smoke --version 0.9.0-rc1 --json
```

K107 adds a closure layer over this packet:

```bash
python -m sp63_core v09-review-closure --output-dir reports/v09_review_closure_smoke --version 0.9.0-rc1 --json
```

The closure report checks whether the review build can be used as manual
release-candidate evidence while keeping project use and ML project readiness
disabled.
