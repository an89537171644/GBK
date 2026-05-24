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

K15 adds a draft normal crack width check for rectangular reinforced concrete
beams. The check uses a simplified elastic cracked estimate for reinforcement
stress, strain, and bounded crack spacing.

- deterministic crack width calculation;
- reinforcement strain and crack spacing model;
- golden case included for engineer review.

Implemented scope:

- rectangular beam section;
- bending only;
- no axial force;
- no prestress;
- heavy concrete B15-B40;
- normal crack width only.

This remains a draft-MVP check. Refined crack spacing, tension stiffening,
long-term effects, nonlinear deformation, and transformed-section behavior are
not implemented.

## K16 Curvature And Deflection

Planned later step:

- curvature calculation;
- short-term and long-term deflection;
- comparison with engineer-reviewed references.

This is not implemented in K15.

## Limitations

- no deflection;
- no prestress;
- no axial force;
- no T-sections;
- no slabs, columns, or punching;
- no nonlinear deformation model;
- no refined crack spacing or tension stiffening model;
- no transformed-section crack model yet.

## ML Boundary

ML must not predict serviceability behavior as a design result unless the
corresponding deterministic checks exist and are validated by engineer-reviewed
golden cases and external comparison.
