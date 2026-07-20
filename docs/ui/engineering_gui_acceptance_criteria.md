# Engineering GUI Acceptance Criteria

requires_engineer_review = true

project_use = false

## Issue #134 Standalone Windows Trial

Source: `UAT-2026-07-19-GUI-01`, user feedback after installation and launch of
the standalone package on 2026-07-19. Status: `CONFIRMED` as a software-usability
requirement. These criteria apply only to the rectangular-beam Windows research
trial and require user and engineering review.

Additional source: `UAT-2026-07-20-GUI-02`, request to show results directly in
the interface and add a simpler graphical representation. Status: `CONFIRMED`
as a software-usability requirement; all engineering interpretation remains
subject to review.

### Launch and usability

- [ ] After a successful standalone installation, the engineer can start the
      interface by double-clicking `02_OPEN_GBK.cmd`; no command entry is
      required.
- [ ] The window uses clear Russian labels, visible units, grouped input fields,
      and an explicit action to run the diagnostic calculation.
- [ ] The supported element and load-duration scope are visible and fixed to the
      current standalone contract; the UI does not offer unsupported elements.
- [ ] A clean Windows/Python 3.11 package test checks that Tkinter is available
      by creating, hiding, updating, and closing a real Tk root.
- [ ] The form remains usable at Windows display scaling of 125–150%; all
      inputs remain reachable through scrolling.
- [ ] Missing Tkinter or a startup failure produces a readable safe error and
      does not silently run a calculation or switch GUI technologies.
- [ ] CLI/JSON launchers remain available for diagnosis and automation.
- [ ] The run action remains outside the scrolled input area, while the result
      area provides separate Summary, Conditional Diagram, and Messages tabs.

### Input boundary

- [ ] The UI collects only fields already present in the standalone
      `StandaloneBeamInput` contract.
- [ ] The UI clearly distinguishes the nonnegative moment magnitude from the
      separately selected `tension_face`.
- [ ] Both `moment_kNm` and `shear_kN` are labelled as nonnegative magnitudes
      `|M|` and `|Q|`; zero remains allowed by the existing contract.
- [ ] `cover_mm` retains its documented programming meaning; the UI does not
      present its normative interpretation as confirmed.
- [ ] Invalid or incomplete values receive a clear message, while the existing
      standalone model/controller remains the authoritative validator.
- [ ] The UI does not add material classes, diameters, coefficients, formulas,
      normative references, or applicability rules.
- [ ] The case identifier warning prohibits personal data, email addresses,
      signatures, and local paths.

### Results and safety

- [ ] The UI calls the existing standalone controller rather than implementing
      calculations in the event handler or presentation layer.
- [ ] The UI keeps `project_use = false` and
      `requires_engineer_review = true` continuously visible, or displays
      unambiguous Russian equivalents.
- [ ] The UI never presents `pass` from an individual check as overall approval,
      certified capacity, or permission for project use.
- [ ] The embedded summary is loaded only from the validated top-level public
      review ZIP and is bound to the exact visible input used by the current run.
- [ ] The summary exposes only user-unit inputs, public statuses, diagnostic
      reinforcement proposal strings, disabled serviceability checks, and
      mandatory safety labels. It does not expose bending capacity,
      utilization, internal intermediate values, material properties, or
      normative coefficients.
- [ ] A local shear `pass` is explicitly labelled as a local technical status,
      not a project or overall approval.
- [ ] The graphical part of the conditional diagram shows only `b × h`, the
      programming meaning of `cover`, stirrup diameter, local-face labels, and
      textual `|M|`/`|Q|`. Checked diagnostic reinforcement proposals may appear
      beside it as text; the UI does not draw bar layers or claim a layout.
- [ ] The diagram continuously states that it is not to scale, is not a working
      drawing, and does not establish the physical mapping of local faces.
- [ ] `fail`, `outside_applicability`, and `review_required` remain visible and
      are not converted to a positive status.
- [ ] Only after fail-closed revalidation of the current visible input, safe
      paths, public diagnostic ZIP semantics, and build identity can the
      engineer open `standalone_index.html`, open the current folder, or export
      the top-level `standalone_review_bundle.zip`.
- [ ] Any field edit, new run, failed run, or validation error disables all
      actions belonging to the previous result and clears the summary and
      conditional diagram.
- [ ] The launcher rejects a `.gbk_build_id` that does not match the wheel
      identity recorded by the current package.
- [ ] Each run uses a separate managed result directory and does not overwrite
      an earlier result without an explicit, safe action.
- [ ] The UI does not include ML results and does not require LIRA-SAPR or SCAD.
- [ ] The result remains diagnostic and subject to engineering review.

## Broader Future UI Criteria

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

The broader criteria below remain planning artifacts for a future wrapper. K63
did not implement Streamlit, Qt, Flask, FastAPI, Electron, Tkinter, PyQt, or web
UI. K64 added the historical technology decision and recommended
`cli_first_with_static_html_reports`. Issue #134 supersedes only the Tkinter
postponement for the narrow standalone rectangular-beam Windows trial described
above.

K65 adds a static `index.html` over workflow outputs. This satisfies only a
navigation/report-index step, not a full GUI acceptance criterion.
