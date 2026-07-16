from dataclasses import FrozenInstanceError

import pytest

from sp63_core.materials import (
    NORMATIVE_PROFILE_ID,
    UnsupportedULSMaterialProfileError,
    get_concrete,
    get_rebar,
    resolve_uls_material_context,
)


def test_short_context_uses_full_base_concrete_resistance():
    context = resolve_uls_material_context(
        get_concrete("B25"),
        get_rebar("A500"),
        "short",
    )

    assert context.load_combination == "permanent_long_short"
    assert context.normative_profile_id == NORMATIVE_PROFILE_ID
    assert context.Rb_base == pytest.approx(14.5)
    assert context.gamma_b1 == pytest.approx(1.0)
    assert context.Rb_effective == pytest.approx(14.5)
    assert context.Rsc == pytest.approx(400)
    assert context.source_clauses
    assert context.requires_engineer_review is True


def test_long_context_applies_gamma_b1_to_concrete_resistance():
    context = resolve_uls_material_context(
        get_concrete("B25"),
        get_rebar("A500"),
        "long",
    )

    assert context.load_combination == "permanent_long"
    assert context.Rb_base == pytest.approx(14.5)
    assert context.gamma_b1 == pytest.approx(0.9)
    assert context.Rb_effective == pytest.approx(13.05)
    assert context.Rsc == pytest.approx(435)


def test_context_uses_updated_a400_compression_resistance():
    short_context = resolve_uls_material_context(
        get_concrete("B30"),
        get_rebar("A400"),
        "short",
    )
    long_context = resolve_uls_material_context(
        get_concrete("B30"),
        get_rebar("A400"),
        "long",
    )

    assert short_context.Rsc == pytest.approx(340)
    assert long_context.Rsc == pytest.approx(340)


def test_context_rejects_unspecified_load_duration():
    with pytest.raises(ValueError, match="load_duration must be 'short' or 'long'"):
        resolve_uls_material_context(
            get_concrete("B25"),
            get_rebar("A500"),
            "invalid",  # type: ignore[arg-type]
        )


def test_context_is_immutable():
    context = resolve_uls_material_context(
        get_concrete("B25"),
        get_rebar("A500"),
        "short",
    )

    with pytest.raises(FrozenInstanceError):
        context.gamma_b1 = 0.9  # type: ignore[misc]


def test_context_rejects_rebar_outside_scoped_longitudinal_profile():
    with pytest.raises(UnsupportedULSMaterialProfileError, match="longitudinal rebar"):
        resolve_uls_material_context(
            get_concrete("B25"),
            get_rebar("A240"),
            "short",
        )


def test_context_rejects_custom_values_with_catalog_class_name():
    custom_concrete = get_concrete("B25").model_copy(update={"Rb": 99.0})
    custom_rebar = get_rebar("A500").model_copy(update={"Rs": 100.0})

    with pytest.raises(UnsupportedULSMaterialProfileError, match="concrete values"):
        resolve_uls_material_context(custom_concrete, get_rebar("A500"), "short")
    with pytest.raises(UnsupportedULSMaterialProfileError, match="rebar values"):
        resolve_uls_material_context(get_concrete("B25"), custom_rebar, "short")
