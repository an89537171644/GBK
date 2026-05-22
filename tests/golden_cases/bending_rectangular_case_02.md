# Golden case: bending rectangular 02

draft_requires_engineer_review = true

## SP Clause

SP 63.13330.2018 8.1.8-8.1.9.

## Inputs

- b = 300 mm
- h = 500 mm
- h0 = 450 mm
- cover = 32 mm
- stirrup diameter = 8 mm
- main bar diameter = 20 mm
- concrete B25
- reinforcement A500
- As = 402.12 mm2
- As_prime = 0 mm2
- M = 150000000 N*mm

## Expected Draft Values

- x ~= 40.21 mm
- Mult ~= 75200000 N*mm
- utilization ~= 1.995
- status = fail

## Tests

- `tests/test_bending_rectangular.py::test_bending_rectangular_draft_golden_case_fail_by_moment`

