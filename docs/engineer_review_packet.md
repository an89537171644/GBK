# Engineer Review Packet

K101 adds a single engineer review packet that indexes v0.9 review evidence.

Included evidence:

- v09-freeze-report;
- v09-final-audit;
- v10-gap-report;
- material verification closure;
- external validation evidence package;
- traceability matrix;
- clean demo verification;
- release notes;
- known limitations;
- acceptance checklist.

The packet is a review handoff artifact only. It does not certify calculations,
approve project use, or make ML project-ready.

```bash
python -m sp63_core engineer-review-packet --output-dir reports/engineer_review_packet_smoke --json
```
