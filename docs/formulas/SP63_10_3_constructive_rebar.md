# SP63 10.3 - constructive reinforcement checks draft

requires_engineer_review = true

## Scope

Draft-MVP constructive checks for rectangular beams and ribs.

## Longitudinal Reinforcement

- Minimum tensile longitudinal reinforcement ratio: `0.1 %`.
- For `b > 150 mm`, use at least two working tensile bars.

## Transverse Reinforcement

- Minimum stirrup diameter: `6 mm`.
- When stirrups are required by calculation: spacing not more than `0.5 * h0`
  and not more than `300 mm`.
- When shear is carried by concrete: for beams and ribs with `h >= 150 mm`,
  spacing not more than `0.75 * h0` and not more than `500 mm`.

## Limitations

Not implemented yet:

- anchorage;
- bar curtailment;
- support zones;
- torsion;
- punching;
- cracks;
- deflections.
