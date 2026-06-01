# Engineering GUI Acceptance Criteria

requires_engineer_review = true

## Future UI Criteria

- [ ] UI clearly shows deterministic SP63 status.
- [ ] UI never shows ML result as project decision.
- [ ] UI always displays engineer-review warning.
- [ ] UI shows `ml_ready_for_project_use = false`.
- [ ] UI exposes generated `report.md`, `report.json`, and `report.html` files.
- [ ] UI exposes manifest and ZIP validation status.
- [ ] UI links to `README_WORKFLOW.md`.
- [ ] UI allows export of engineering workflow package.
- [ ] UI does not modify material catalog automatically.
- [ ] UI does not hide failed or `review_required` statuses.

## Hard Stops

- UI must not certify the design.
- UI must not replace deterministic SP63 checks.
- UI must not use ML or neural output as final design approval.
- UI must not enable `ml_ready_for_project_use = true`.
- UI must not hide missing material verification or external validation.
- UI must not add closed SCAD/LIRA files, personal data, grant documents, or
  full SP 63 text.

## Review Note

These criteria are planning artifacts for a future wrapper. K63 does not
implement Streamlit, Qt, Flask, FastAPI, Electron, Tkinter, PyQt, or web UI.
