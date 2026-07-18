import math

import pytest

from sp63_core.standalone import StandaloneBeamInput, adapt_standalone_beam_input


def beam_input(**overrides) -> StandaloneBeamInput:
    values = {
        "case_id": "beam-001",
        "b_mm": 300,
        "h_mm": 500,
        "cover_mm": 32,
        "stirrup_diameter_mm": 8,
        "concrete_class": "B25",
        "longitudinal_rebar_class": "A500",
        "stirrup_rebar_class": "A240",
        "moment_kNm": 150,
        "shear_kN": 80,
        "tension_face": "local_y_min",
    }
    values.update(overrides)
    return StandaloneBeamInput(**values)


def test_adapter_converts_manual_units_and_locks_safe_scope():
    result = adapt_standalone_beam_input(beam_input())

    assert result.M == 150_000_000
    assert result.Q == 80_000
    assert result.load_duration == "short"
    assert result.moment_axis == "local_z"
    assert result.tension_face == "local_y_min"
    assert result.local_axes_id == "standalone-rectangular-beam-v1:beam-001"
    assert result.check_cracks is False
    assert result.check_crack_width is False
    assert result.check_deflection is False


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("b_mm", math.nan),
        ("h_mm", math.inf),
        ("cover_mm", -math.inf),
        ("stirrup_diameter_mm", math.nan),
        ("moment_kNm", math.inf),
        ("shear_kN", math.nan),
    ),
)
def test_adapter_rejects_non_finite_values(field, value):
    with pytest.raises(ValueError, match="must be finite"):
        adapt_standalone_beam_input(beam_input(**{field: value}))


@pytest.mark.parametrize("field", ("moment_kNm", "shear_kN"))
def test_adapter_rejects_finite_values_that_overflow_unit_conversion(field):
    with pytest.raises(ValueError, match="unit conversion must remain finite"):
        adapt_standalone_beam_input(beam_input(**{field: 1e308}))


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"case_id": ""}, "case_id"),
        ({"b_mm": 0}, "b_mm must be positive"),
        ({"cover_mm": 500}, "cover_mm must be less"),
        ({"stirrup_diameter_mm": 7}, "must be one of: 6, 8, 10, 12"),
        ({"stirrup_diameter_mm": 8.1}, "must be one of: 6, 8, 10, 12"),
        ({"moment_kNm": -1}, "moment_kNm must be non-negative"),
        ({"shear_kN": -1}, "shear_kN must be non-negative"),
        ({"concrete_class": "B60"}, "concrete_class must be one of"),
        ({"longitudinal_rebar_class": "A240"}, "longitudinal_rebar_class"),
        ({"stirrup_rebar_class": "A600"}, "stirrup_rebar_class"),
        ({"tension_face": "automatic"}, "tension_face"),
    ),
)
def test_adapter_rejects_inputs_outside_beam_preview_scope(overrides, message):
    with pytest.raises((TypeError, ValueError), match=message):
        adapt_standalone_beam_input(beam_input(**overrides))


def test_adapter_normalizes_material_class_spelling():
    result = adapt_standalone_beam_input(
        beam_input(
            concrete_class=" b25 ",
            longitudinal_rebar_class=" a500 ",
            stirrup_rebar_class=" a240 ",
        )
    )

    assert result.concrete_class == "B25"
    assert result.longitudinal_rebar_class == "A500"
    assert result.stirrup_rebar_class == "A240"
