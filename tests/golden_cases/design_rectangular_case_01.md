# Golden case: end-to-end rectangular design 01

draft_requires_engineer_review = true

## SP Clauses

- SP 63.13330.2018 8.1.8-8.1.9
- SP 63.13330.2018 8.1.31-8.1.33
- SP 63.13330.2018 10.3 draft MVP constructive checks

## Inputs

- b = 300 mm
- h = 500 mm
- cover = 32 mm
- stirrup diameter for geometry = 8 mm
- concrete class = B25
- longitudinal reinforcement class = A500
- stirrup reinforcement class = A240
- M = 150000000 N*mm
- Q = 80000 N
- load_duration = short

## Expected Draft Values

- overall status = pass
- selected longitudinal option is not empty
- selected transverse option is not empty
- protocol status = pass
- bending status = pass
- shear status = pass
- constructive statuses = pass or warning-free pass for selected MVP case

## Tests

- `tests/test_design_rectangular.py::test_design_rectangular_element_returns_passing_result`
- `tests/test_design_rectangular.py::test_design_rectangular_protocol_contains_selected_reinforcement`

