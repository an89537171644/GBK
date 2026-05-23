# SP63 normal crack formation for rectangular section

requires_engineer_review = true

## Purpose

Draft-MVP check for normal crack formation in a rectangular reinforced concrete beam.
SP 63 reference: section 8.2, normal cracks. This card contains only a short
project algorithm description, not normative text.

## Scope

- rectangular section;
- bending only;
- no axial force;
- no prestress;
- heavy concrete B15-B40;
- service limit-state material property `Concrete.Rbtser`;
- normal cracks only.

## Units

- b, h, h0 - mm;
- Mser, Mcrc - N*mm;
- Rbtser - MPa = N/mm2;
- area - mm2;
- inertia - mm4.

## Draft formula

For the first MVP use elastic gross concrete section:

A = b * h

I = b * h^3 / 12

yt = h / 2

W = I / yt

Mcrc = Rbtser * W

crack_utilization = Mser / Mcrc

status:

- "no_crack" if Mser <= Mcrc
- "crack" if Mser > Mcrc

Important:
This is a conservative draft-MVP simplification.
It does not yet include transformed section with reinforcement.
It does not yet include nonlinear deformation model.
It does not yet include long-term effects.
It does not calculate crack width.
It does not use `Eb` in K14.

## Outputs

- Mcrc
- Mser
- utilization
- status
- warnings
- intermediate_values
- requires_engineer_review = true

## Limitations

- no crack width;
- no deflection;
- no prestress;
- no axial force;
- no T-section;
- no slab logic;
- no nonlinear deformation model;
- no transformed section yet.
