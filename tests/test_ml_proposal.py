from sp63_core.ml import proposal_from_prediction


def test_proposal_from_prediction_creates_valid_proposal():
    proposal, warnings = proposal_from_prediction(
        {
            "main_bar_count": 3,
            "main_bar_diameter": 20,
            "stirrup_legs": 2,
            "stirrup_spacing": 200,
        },
        geometry_stirrup_diameter=8,
    )

    assert proposal.main_bar_count == 3
    assert proposal.main_bar_diameter == 20
    assert proposal.stirrup_diameter == 8
    assert proposal.stirrup_legs == 2
    assert proposal.stirrup_spacing == 200
    assert proposal.requires_deterministic_check is True
    assert warnings == ()


def test_proposal_from_prediction_snaps_non_catalog_values():
    proposal, warnings = proposal_from_prediction(
        {
            "main_bar_count": 3.2,
            "main_bar_diameter": 21,
            "stirrup_legs": 3,
            "stirrup_spacing": 240,
        },
        geometry_stirrup_diameter=9,
    )

    assert proposal.main_bar_count == 3
    assert proposal.main_bar_diameter == 20
    assert proposal.stirrup_diameter == 8
    assert proposal.stirrup_legs == 2
    assert proposal.stirrup_spacing == 250
    assert warnings


def test_proposal_from_prediction_uses_geometry_stirrup_diameter():
    proposal, warnings = proposal_from_prediction(
        {
            "main_bar_count": 3,
            "main_bar_diameter": 20,
            "stirrup_legs": 2,
            "stirrup_spacing": 200,
        },
        geometry_stirrup_diameter=8,
    )

    assert proposal.stirrup_diameter == 8
    assert warnings == ()


def test_proposal_from_prediction_warns_when_prediction_contains_stirrup_diameter():
    proposal, warnings = proposal_from_prediction(
        {
            "main_bar_count": 3,
            "main_bar_diameter": 20,
            "stirrup_diameter": 8,
            "stirrup_legs": 2,
            "stirrup_spacing": 200,
        },
        geometry_stirrup_diameter=10,
    )

    assert proposal.stirrup_diameter == 8
    assert any("stirrup_diameter from prediction is deprecated" in warning for warning in warnings)


def test_proposal_from_prediction_requires_geometry_stirrup_when_missing():
    try:
        proposal_from_prediction(
            {
                "main_bar_count": 3,
                "main_bar_diameter": 20,
                "stirrup_legs": 2,
                "stirrup_spacing": 200,
            }
        )
    except ValueError as exc:
        assert "geometry_stirrup_diameter is required" in str(exc)
    else:
        raise AssertionError("ValueError was not raised")


def test_main_bar_count_snaps_to_default_bar_counts():
    proposal, warnings = proposal_from_prediction(
        {
            "main_bar_count": 9,
            "main_bar_diameter": 20,
            "stirrup_legs": 2,
            "stirrup_spacing": 200,
        },
        geometry_stirrup_diameter=8,
    )

    assert proposal.main_bar_count == 8
    assert any("main_bar_count=9 snapped to supported value 8" in warning for warning in warnings)
