# Review Signoff Templates

K104 adds placeholder-only signoff templates for future manual review.

Generated templates:

- material review signoff;
- external validation signoff;
- ML advisory signoff;
- release review signoff.

The templates contain placeholder fields only:

- `engineer_name_placeholder`;
- `review_date_placeholder`;
- `organization_placeholder`;
- `scope`;
- `reviewed_artifacts`;
- `status`;
- `notes`;
- `signature_placeholder`.

Do not commit filled templates if they contain personal or private data.

```bash
python -m sp63_core review-signoff-templates --output-dir reports/review_signoff_templates_smoke --json
```
