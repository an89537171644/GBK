# Golden case: shear rectangular 01

draft_requires_engineer_review = true

## SP Clause

SP 63.13330.2018 8.1.31-8.1.33.

## Inputs

- b = 300 mm
- h0 = 450 mm
- concrete B25: Rb = 14.5 MPa, Rbt = 1.05 MPa
- transverse reinforcement A240: Rsw = 170 MPa
- stirrup D8, two legs
- Asw = 100.53 mm2
- sw = 200 mm
- Q = 80000 N

## Expected Draft Values

- qsw ~= 85.45 N/mm
- Q_strip ~= 587250 N
- C ~= 900 mm
- Qb ~= 106310 N
- Qsw ~= 57680 N
- Qult ~= 163990 N
- qsw_rule_status = pass
- transverse_reinforcement_countable = true
- status = pass

## Tests

- `tests/test_shear_rectangular.py::test_shear_rectangular_draft_golden_case_pass`
- `tests/test_shear_rectangular.py::test_shear_reports_sw_max_and_qsw_rule`

