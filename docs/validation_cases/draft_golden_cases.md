# Draft golden cases

These cases are preliminary and must be reviewed by the engineering reviewer before
they become acceptance tests for calculation modules.

`requires_engineer_review = true`
`approved_by_engineer = false`

## Bending, passing case

- b = 300 mm
- h = 500 mm
- h0 = 450 mm
- a_prime = 40 mm
- concrete B25: Rb = 14.5 MPa
- rebar A500: Rs = 435 MPa, Rsc = 400 MPa, Es = 200000 MPa
- As = 3D20 = 942.48 mm2
- As_prime = 0
- M = 150000000 N*mm

Expected draft values:

- x ~= 94.25 mm
- xi ~= 0.209
- xi_R ~= 0.493
- Mult ~= 165.17 kN*m
- utilization ~= 0.908
- status = pass

## Bending, failing case

- b = 300 mm
- h = 500 mm
- h0 = 450 mm
- concrete B25
- rebar A500
- As = 2D16 = 402.12 mm2
- As_prime = 0
- M = 150000000 N*mm

Expected draft values:

- x ~= 40.21 mm
- Mult ~= 75.20 kN*m
- utilization ~= 1.995
- status = fail

## Shear, preliminary passing case

- b = 300 mm
- h0 = 450 mm
- concrete B25: Rb = 14.5 MPa, Rbt = 1.05 MPa
- stirrup rebar A240: Rsw = 170 MPa
- stirrup D8, two legs
- Asw = 100.53 mm2
- sw = 200 mm
- Q = 80000 N

Expected draft values for C in [h0, 2*h0]:

- qsw ~= 85.45 N/mm
- Q_strip ~= 587.25 kN
- minimum Qb + Qsw near C = 900 mm
- Qb ~= 106.31 kN
- Qsw ~= 57.68 kN
- Qult ~= 163.99 kN
- status = pass
