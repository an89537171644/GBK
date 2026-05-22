# Changelog

## 0.1.0 MVP draft

Implemented draft MVP blocks:

- project scaffold with Python package metadata;
- unit conversion helpers;
- draft material catalogs for heavy concrete B15-B40 and A240/A400/A500 rebar;
- rectangular section geometry;
- bending check for rectangular sections;
- shear check for rectangular sections;
- longitudinal reinforcement selection with single-layer layout check;
- transverse reinforcement selection;
- end-to-end rectangular design service;
- calculation protocol assembly;
- JSON and HTML report export;
- deterministic dataset generator with train/validation/test split;
- CLI subcommands for demo, checks, selection, design, and dataset generation;
- baseline RandomForest model for `As_required` prediction;
- neural MLPRegressor surrogate for `As_required` prediction;
- safe ML suggestion guard returning only deterministic-pass options;
- Streamlit draft prototype;
- draft golden cases and validation documentation;
- release documentation package.

Notes:

- All engineering values and golden cases require engineer review.
- ML is not a final calculator.
- Formulas are limited to approved MVP formula cards.
