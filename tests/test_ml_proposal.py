from sp63_core.ml import proposal_from_prediction


def test_proposal_from_prediction_creates_valid_proposal():
    proposal, warnings = proposal_from_prediction(
        {
            "main_bar_count": 3,
            "main_bar_diameter": 20,
            "stirrup_diameter": 8,
            "stirrup_legs": 2,
            "stirrup_spacing": 200,
        }
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
            "stirrup_diameter": 9,
            "stirrup_legs": 3,
            "stirrup_spacing": 240,
        }
    )

    assert proposal.main_bar_count == 3
    assert proposal.main_bar_diameter == 20
    assert proposal.stirrup_diameter == 8
    assert proposal.stirrup_legs == 2
    assert proposal.stirrup_spacing == 250
    assert warnings
