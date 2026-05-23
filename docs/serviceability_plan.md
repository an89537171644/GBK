# Serviceability Plan

requires_engineer_review = true

## K14 Normal Crack Formation Mcrc

K14 adds a draft normal crack formation check for rectangular reinforced concrete beams.
The check uses service concrete property Rbtser and a gross elastic concrete section:
Mcrc = Rbtser * W.

Implemented scope:

- rectangular beam section;
- bending only;
- no axial force;
- no prestress;
- heavy concrete B15-B40;
- normal crack formation only.

## K15 Crack Width acrc

Planned next serviceability step:

- deterministic crack width calculation;
- reinforcement strain and crack spacing model;
- golden cases reviewed by an engineer.

This is not implemented in K14.

## K16 Curvature And Deflection

Planned later step:

- curvature calculation;
- short-term and long-term deflection;
- comparison with engineer-reviewed references.

This is not implemented in K14.

## Limitations

- no crack width;
- no deflection;
- no prestress;
- no axial force;
- no T-sections;
- no slabs, columns, or punching;
- no nonlinear deformation model;
- no transformed-section crack model yet.

## ML Boundary

ML must not predict crack formation, crack width, or deflection as a design result until
deterministic serviceability checks exist and are validated by engineer-reviewed golden
cases and external comparison.
