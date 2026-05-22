# SCAD/LIRA comparison template

Use this table for every independent software comparison. Rows are draft until
`approved_by_engineer` is set by a responsible engineer outside automated tests.

| case_id | software | model_description | input_geometry | materials | loads | software_result | sp63_core_result | difference_percent | comment | approved_by_engineer |
|---|---|---|---|---|---|---|---|---|---|---|
| example_case | SCAD or LIRA | rectangular beam/slab assumptions | b, h, cover, h0 | concrete and rebar classes | M, Q | value and units | value and units | 0.0 | draft comparison | false |

Required notes for each case:

- Software name and version.
- Design code settings.
- Material tables and reduction factors.
- Geometry, reinforcement layout, and load units.
- Whether the comparison is for bending, shear, selection, or full design.
- Engineer review status.
