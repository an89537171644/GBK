# Implementation status

| module | status | tests | requires_engineer_review | next_action |
|---|---|---|---|---|
| `units.py` | done | yes | no | keep stable |
| `materials/concrete.py` | draft | yes | yes | engineer review of material values |
| `materials/rebar.py` | implemented draft with `Rsc_short`/`Rsc_long` | yes | yes | engineer review of material values |
| `sections/rectangular.py` | implemented with `h0_override` validation | yes | no | keep geometry checks covered |
| `checks/bending.py` | implemented with `load_duration` support | yes | yes | engineer review of formula card and golden cases |
| `checks/shear.py` | implemented | yes | yes | engineer review of formula card and golden cases |
| `rebar/longitudinal.py` | implemented with h0 recalculation and draft single-layer layout check | yes | yes | engineer review of layout assumptions |
| `report/protocol.py` | draft | yes | yes | keep protocol structure stable |
| `dataset/generator.py` | draft; includes `load_duration` and selected option section `h0` | yes | yes | engineer review dataset ranges |
| transverse reinforcement selection | not started | no | yes | separate approved step |
| ML | not started | no | yes | separate approved step |
| UI | not started | no | yes | separate approved step |
