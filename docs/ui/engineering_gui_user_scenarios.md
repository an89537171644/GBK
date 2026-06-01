# Engineering GUI User Scenarios

requires_engineer_review = true

## Scope

These scenarios describe future GUI/desktop wrapper behavior. They do not
implement UI and do not change deterministic calculations.

## Scenarios

1. Engineer runs the deterministic workflow.

   The UI selects an `input.json`, an output directory, and launches
   `python -m sp63_core engineering-workflow ...`. The UI displays generated
   deterministic report files and keeps engineer-review warnings visible.

2. Engineer checks ZIP/report archive.

   The UI displays `manifest.json`, archive validation status, ZIP status, and
   checksum/integrity results. It must not hide `review_required` or `fail`
   statuses.

3. Engineer runs workflow self-check.

   The UI launches `engineering-workflow-self-check` and shows whether the
   local environment can create the expected report package artifacts.

4. Engineer connects ML-readiness.

   The UI can pass a dataset path and optional engineer-filled validation CSVs
   into the workflow. ML readiness remains advisory-only and
   `ml_ready_for_project_use` remains false.

5. Engineer checks material verification.

   The UI displays material verification CSV status, missing fields, and
   engineer verification status. It must not update material catalog values
   automatically.

6. Engineer checks external validation.

   The UI displays external validation strict-mode summary, deltas, acceptance
   status, missing external values, and engineer comments.

7. Engineer reviews neural advisory output.

   The UI may display neural advisory or surrogate outputs only as review
   information. It must show that deterministic SP63 verification is mandatory.

8. Engineer forms acceptance checklist.

   The UI exposes generated files, warnings, validation gates, material
   verification, external validation, and final engineer acceptance checklist.
   The UI must not produce a project approval automatically.
