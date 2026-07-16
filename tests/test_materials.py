import pytest

from sp63_core.materials import (
    LONGITUDINAL_DIAMETERS,
    STIRRUP_DIAMETERS,
    area_by_diameter,
    get_concrete,
    get_rebar,
)
from sp63_core.materials.concrete import CONCRETE_CATALOG


def test_get_concrete_b25_draft_values():
    concrete = get_concrete("B25")

    assert concrete.Rb == 14.5
    assert concrete.Rbt == 1.05
    assert concrete.Rbser == 18.5
    assert concrete.Rbtser == 1.55
    assert concrete.Eb == 30_000
    assert concrete.draft_requires_engineer_review is True


def test_get_concrete_b15_uses_base_pdf_service_tension_value():
    concrete = get_concrete("B15")

    assert concrete.Rbtser == pytest.approx(1.10)


def test_concrete_service_properties_b25():
    concrete = get_concrete("B25")

    assert concrete.Rb == pytest.approx(14.5)
    assert concrete.Rbt == pytest.approx(1.05)
    assert concrete.Rbser == pytest.approx(18.5)
    assert concrete.Rbtser == pytest.approx(1.55)
    assert concrete.Eb == pytest.approx(30_000)


def test_all_concrete_classes_have_service_properties():
    for concrete in CONCRETE_CATALOG.values():
        assert concrete.Rbser > concrete.Rb
        assert concrete.Rbtser > concrete.Rbt
        assert concrete.Eb > 0


def test_unknown_concrete_class_raises():
    with pytest.raises(ValueError, match="unsupported concrete class"):
        get_concrete("B45")


def test_get_rebar_a500_draft_values():
    rebar = get_rebar("A500")

    assert rebar.Rs == 435
    assert rebar.Rsser == 500
    assert rebar.Rsc == 400
    assert rebar.Rsc_short == 400
    assert rebar.Rsc_long == 435
    assert rebar.Rsw == 300
    assert rebar.draft_requires_engineer_review is True


def test_get_rebar_a500_rsc_by_load_duration():
    rebar = get_rebar("A500")

    assert rebar.Rsc_short == 400
    assert rebar.Rsc_long == 435
    assert rebar.Rsc == 400
    assert rebar.get_Rsc("short") == 400
    assert rebar.get_Rsc("long") == 435


def test_get_rebar_a400_rsc_same_for_short_and_long():
    rebar = get_rebar("A400")

    assert rebar.Rsn == 390
    assert rebar.Rs == 340
    assert rebar.Rsser == 390
    assert rebar.get_Rsc("short") == 340
    assert rebar.get_Rsc("long") == 340


def test_get_Rsc_rejects_unknown_load_duration():
    with pytest.raises(ValueError, match="load_duration must be 'short' or 'long'"):
        get_rebar("A500").get_Rsc("invalid")


def test_rebar_service_properties():
    a240 = get_rebar("A240")
    a400 = get_rebar("A400")
    a500 = get_rebar("A500")

    assert a240.Rsser == pytest.approx(240)
    assert a400.Rsser == pytest.approx(390)
    assert a500.Rsser == pytest.approx(500)
    assert a400.Rsser > a400.Rs
    assert a500.Rsser > a500.Rs
    assert all(rebar.Es > 0 for rebar in (a240, a400, a500))


def test_area_by_diameter():
    assert area_by_diameter(8) == pytest.approx(50.265, rel=1e-4)


def test_area_by_diameter_rejects_non_positive_values():
    with pytest.raises(ValueError, match="diameter must be positive"):
        area_by_diameter(0)


def test_mvp_diameter_catalogs():
    assert LONGITUDINAL_DIAMETERS == (10, 12, 14, 16, 18, 20, 22, 25, 28, 32)
    assert STIRRUP_DIAMETERS == (6, 8, 10, 12)
