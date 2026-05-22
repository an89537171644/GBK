import pytest

from sp63_core.rebar import check_single_layer_layout
from sp63_core.sections import RectangularSection


def mvp_section() -> RectangularSection:
    return RectangularSection(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )


def test_single_layer_layout_returns_feasible_result():
    layout = check_single_layer_layout(mvp_section(), bar_count=3, diameter=20)

    assert layout.scheme == "3D20"
    assert layout.area > 0
    assert layout.clear_width == pytest.approx(220)
    assert layout.required_width == pytest.approx(110)
    assert layout.layout_feasible is True
    assert layout.warnings == ()
    assert layout.requires_engineer_review is True


def test_single_layer_layout_reports_infeasible_result():
    layout = check_single_layer_layout(mvp_section(), bar_count=8, diameter=32)

    assert layout.layout_feasible is False
    assert layout.warnings == ("single-layer layout is not feasible",)


def test_single_layer_layout_rejects_invalid_inputs():
    with pytest.raises(ValueError, match="bar_count must be positive"):
        check_single_layer_layout(mvp_section(), bar_count=0, diameter=20)

    with pytest.raises(ValueError, match="diameter must be positive"):
        check_single_layer_layout(mvp_section(), bar_count=3, diameter=0)

    with pytest.raises(ValueError, match="min_clear_spacing must be non-negative"):
        check_single_layer_layout(mvp_section(), bar_count=3, diameter=20, min_clear_spacing=-1)
