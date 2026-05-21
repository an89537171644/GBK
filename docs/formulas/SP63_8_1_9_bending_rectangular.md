# Formula card: rectangular bending section

`requires_engineer_review = true`

## Normative link

SP 63.13330.2018, clauses 8.1.8-8.1.9.

This card contains MVP formulas for implementation after engineering review.
It does not replace the source code document.

## Scope

Rectangular reinforced concrete bending element without prestressing.
Applicable in the MVP only for heavy concrete B15-B40.

## Units

- b, h, h0, x, a_prime: mm
- As, As_prime: mm2
- Rb, Rs, Rsc, Es: MPa = N/mm2
- M, Mult: N*mm

## Inputs

- b: section width
- h: section height
- h0: effective depth
- a_prime: compression reinforcement depth
- Rb: concrete compression design resistance
- Rs: tensile reinforcement design resistance
- Rsc: compression reinforcement design resistance
- Es: reinforcement modulus
- As: tensile reinforcement area
- As_prime: compression reinforcement area
- M: design bending moment

## Outputs

- x: compression zone height
- xi = x / h0
- xi_R: limiting relative compression zone height
- Mult: ultimate bending moment
- utilization = M / Mult
- status: pass, fail, or review_or_fail
- warnings
- intermediate_values for report protocol

## MVP formulas

Concrete ultimate strain for MVP:

```text
eb2 = 0.0035
```

Limiting relative compression zone height:

```text
xi_R = 0.8 / (1 + (Rs / Es) / eb2)
```

Compression zone height:

```text
x = (Rs * As - Rsc * As_prime) / (Rb * b)
```

If As_prime = 0:

```text
x = Rs * As / (Rb * b)
```

Relative compression zone height:

```text
xi = x / h0
```

Ultimate bending moment:

```text
Mult = Rb * b * x * (h0 - 0.5 * x) + Rsc * As_prime * (h0 - a_prime)
```

## Status rule

```text
status = pass if M <= Mult and x <= xi_R * h0
status = fail if M > Mult and x <= xi_R * h0
status = review_or_fail if x > xi_R * h0
```

If x > xi_R * h0, the MVP must return a warning. The implementation must not
automatically substitute x = xi_R * h0 without a separate flag and explanation.

## Draft golden case 1: pass

`requires_engineer_review = true`

- b = 300 mm
- h = 500 mm
- h0 = 450 mm
- a_prime = 40 mm
- concrete B25
- rebar A500
- Rb = 14.5 MPa
- Rs = 435 MPa
- Rsc = 400 MPa
- Es = 200000 MPa
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

## Draft golden case 2: fail

`requires_engineer_review = true`

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

## Implementation notes

- Validate positive dimensions, resistances, and reinforcement areas.
- Return intermediate values for the calculation protocol.
- Do not accept the result as final until the formula card and golden cases are
  reviewed by the engineering reviewer.
