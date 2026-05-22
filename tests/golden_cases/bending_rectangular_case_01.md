# Golden case: bending rectangular 01

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
- concrete B25: Rb = 14.5 MPa
- reinforcement A500: Rs = 435 MPa, Es = 200000 MPa
- As = 942.48 mm2
- As_prime = 0 mm2
- M = 150000000 N*mm

## Expected Draft Values

- x ~= 94.25 mm
- xi ~= 0.209
- xi_R ~= 0.493
- Mult ~= 165170000 N*mm
- utilization ~= 0.908
- status = pass

## Tests

- `tests/test_bending_rectangular.py::test_bending_rectangular_draft_golden_case_pass`

