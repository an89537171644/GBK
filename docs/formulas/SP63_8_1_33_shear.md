# Formula card: shear and inclined sections

`requires_engineer_review = true`

## Normative link

SP 63.13330.2018, clauses 8.1.31-8.1.33.

This card contains MVP formulas for implementation after engineering review.
It does not replace the source code document.

## Scope

Rectangular reinforced concrete bending element checked for shear with vertical
stirrups.

## Units

- b, h0, C, sw: mm
- Asw: mm2
- Rb, Rbt, Rsw: MPa = N/mm2
- Q, Q_strip, Qb, Qsw, Qult: N

## Inputs

- b: section width
- h0: effective depth
- Rb: concrete compression design resistance
- Rbt: concrete tension design resistance
- Rsw: transverse reinforcement design resistance
- Q: design shear force
- Asw: transverse reinforcement area in one stirrup spacing
- sw: stirrup spacing
- C: inclined section projection length, varied in the MVP

## Outputs

- Q_strip: concrete strip capacity between inclined sections
- qsw: transverse reinforcement force per unit length
- Qb: concrete contribution
- Qsw: transverse reinforcement contribution
- Qult = Qb + Qsw
- utilization = Q / Qult
- status: pass or fail
- warnings
- intermediate_values for report protocol

## MVP formulas

Concrete strip check:

```text
phi_b1 = 0.3
Q_strip = phi_b1 * Rb * b * h0
```

Inclined section check:

```text
Q <= Qb + Qsw
```

Concrete contribution:

```text
phi_b2 = 1.5
Qb = phi_b2 * Rbt * b * h0^2 / C
```

Concrete contribution limits:

```text
Qb_min = 0.5 * Rbt * b * h0
Qb_max = 2.5 * Rbt * b * h0
Qb = min(max(Qb, Qb_min), Qb_max)
```

Transverse reinforcement:

```text
qsw = Rsw * Asw / sw
phi_sw = 0.75
Qsw = phi_sw * qsw * C
```

For the MVP, vary C from 1.0*h0 to 2.0*h0. A discrete search over 101 points is
allowed. Use the minimum value of Qb + Qsw as the most dangerous checked value.

## Status rule

```text
status = pass if Q <= Q_strip and Q <= min(Qb + Qsw)
status = fail otherwise
```

## Draft Conditions For Counting Transverse Reinforcement

`requires_engineer_review = true`

K7 adds draft warnings for conditions that affect whether transverse
reinforcement may be counted in the MVP shear result. These warnings do not
change the base formula `Qb + Qsw`.

Maximum spacing for counting transverse reinforcement:

```text
sw_max_by_shear_rule = Rbt * b * h0^2 / Q, if Q > 0
sw_max_by_shear_rule = infinity, if Q = 0
```

Counting status:

```text
transverse_reinforcement_countable = Asw > 0 and sw <= sw_max_by_shear_rule
```

Minimum draft qsw rule:

```text
qsw_min_rule = 0.25 * Rbt * b
qsw_rule_status = pass if qsw >= qsw_min_rule
qsw_rule_status = warning if Asw > 0 and qsw < qsw_min_rule
qsw_rule_status = not_applicable if Asw = 0
```

Warnings:

- `stirrup spacing exceeds shear rule maximum for counting transverse reinforcement`
- `qsw is below draft minimum rule for counting transverse reinforcement`

## Draft golden case 1: pass

`requires_engineer_review = true`

- b = 300 mm
- h0 = 450 mm
- concrete B25
- Rb = 14.5 MPa
- Rbt = 1.05 MPa
- transverse reinforcement A240
- Rsw = 170 MPa
- stirrup D8, two legs
- Asw = 2 * pi * 8^2 / 4 = 100.53 mm2
- sw = 200 mm
- Q = 80000 N

Expected draft values with C varied from h0 to 2*h0:

- qsw ~= 85.45 N/mm
- Q_strip ~= 587.25 kN
- minimum Qb + Qsw is approximately at C = 900 mm
- Qb ~= 106.31 kN
- Qsw ~= 57.68 kN
- Qult ~= 163.99 kN
- status = pass

## Implementation notes

- Validate positive dimensions, resistances, force, Asw, sw, and C range.
- Return intermediate values for the calculation protocol.
- Do not accept the result as final until the formula card and golden case are
  reviewed by the engineering reviewer.
