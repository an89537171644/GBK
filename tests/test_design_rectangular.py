import pytest

from sp63_core.design import RectangularDesignInput, design_rectangular_element


def mvp_input(**overrides) -> RectangularDesignInput:
    data = {
        "b": 300,
        "h": 500,
        "cover": 32,
        "stirrup_diameter_for_geometry": 8,
        "concrete_class": "B25",
        "longitudinal_rebar_class": "A500",
        "stirrup_rebar_class": "A240",
        "M": 150_000_000,
        "Q": 80_000,
        "local_axes_id": "design-test-local-axes",
        "moment_axis": "local_z",
        "tension_face": "local_y_min",
        "load_duration": "short",
    }
    data.update(overrides)
    return RectangularDesignInput(**data)


def test_design_rectangular_element_blocks_public_pass_while_ed01_is_open():
    result = design_rectangular_element(mvp_input())

    assert result.status == "outside_applicability"
    assert result.strength_status == "outside_applicability"
    assert result.serviceability_status == "not_checked"
    assert result.overall_status == "outside_applicability"
    assert result.selected_longitudinal is not None
    assert result.selected_transverse is not None
    assert result.protocol is not None
    assert result.protocol.status == "outside_applicability"
    assert result.protocol.strength_status == "outside_applicability"
    assert result.protocol.serviceability_status == "not_checked"
    assert result.protocol.overall_status == "outside_applicability"
    assert result.status_scope == "public"
    selected_longitudinal = result.selected_longitudinal
    assert selected_longitudinal.status == "outside_applicability"
    assert selected_longitudinal.utilization is None
    assert selected_longitudinal.diagnostic_status == "pass"
    assert selected_longitudinal.diagnostic_utilization <= 1.0
    bending = selected_longitudinal.bending
    assert bending.status == "outside_applicability"
    assert bending.Mult is None
    assert bending.utilization is None
    assert bending.capacity_applicable is False
    assert bending.public_status == "outside_applicability"
    assert bending.diagnostic_status == "pass"
    assert bending.diagnostic_Mult is not None
    assert bending.diagnostic_utilization is not None
    assert bending.diagnostic_capacity_applicable is True
    assert bending.capacity_publication_allowed is False
    public_bending = result.protocol.checks["bending"]
    assert public_bending["status"] == "outside_applicability"
    assert public_bending["Mult"] is None
    assert public_bending["utilization"] is None
    assert not any(key.startswith("diagnostic_") for key in public_bending)
    assert not any(
        key.startswith("diagnostic_")
        for key in public_bending["intermediate_values"]
    )
    assert result.selected_longitudinal.constructive.status == "pass"
    assert result.selected_transverse.shear.status == "pass"
    assert result.selected_transverse.constructive.status in ("pass", "warning")
    assert result.selected_longitudinal.section.effective_depth() > 0
    assert result.section == result.selected_longitudinal.section
    assert result.selected_transverse.utilization <= 1.0
    assert (
        result.selected_transverse.diameter
        == result.input_data.stirrup_diameter_for_geometry
    )
    assert result.completeness_status == "incomplete"
    assert result.project_use is False


def test_design_diagnostic_scope_is_explicit_and_never_enables_project_use():
    result = design_rectangular_element(mvp_input(), status_scope="diagnostic")

    assert result.status == "pass"
    assert result.status_scope == "diagnostic"
    assert result.protocol is not None
    assert result.protocol.status_scope == "diagnostic"
    assert result.project_use is False


def test_design_rejects_unknown_status_scope():
    with pytest.raises(ValueError, match="status_scope"):
        design_rectangular_element(
            mvp_input(),
            status_scope="unsafe",  # type: ignore[arg-type]
        )


def test_design_rectangular_element_is_outside_when_no_longitudinal_option():
    result = design_rectangular_element(mvp_input(M=2_000_000_000))

    assert result.status == "outside_applicability"
    assert result.strength_status == "outside_applicability"
    assert result.serviceability_status == "not_checked"
    assert result.overall_status == "outside_applicability"
    assert result.selected_longitudinal is None
    assert result.selected_transverse is None
    assert result.protocol is None
    assert any(
        "no passing diagnostic longitudinal reinforcement options" in warning
        for warning in result.warnings
    )


def test_design_rectangular_element_fails_when_no_transverse_option():
    result = design_rectangular_element(mvp_input(M=150_000_000, Q=2_000_000))

    assert result.status == "fail"
    assert result.strength_status == "fail"
    assert result.serviceability_status == "not_checked"
    assert result.overall_status == "fail"
    assert result.selected_longitudinal is not None
    assert result.selected_transverse is None
    assert result.protocol is None
    assert result.section == result.selected_longitudinal.section
    assert "no passing transverse reinforcement options" in result.warnings


def test_design_rectangular_protocol_contains_selected_reinforcement():
    result = design_rectangular_element(mvp_input())

    assert result.selected_longitudinal is not None
    assert result.selected_transverse is not None
    assert result.protocol is not None
    assert result.protocol.reinforcement["main"] == result.selected_longitudinal.scheme
    assert result.protocol.reinforcement["stirrups"] == result.selected_transverse.scheme
    assert result.protocol.reinforcement["longitudinal_constructive_status"] == "pass"
    assert "longitudinal_reinforcement_ratio_percent" in result.protocol.reinforcement
    assert result.protocol.reinforcement["stirrup_constructive_status"] == "pass"
    assert "stirrup_constructive_max_spacing" in result.protocol.reinforcement
    assert "stirrup_sw_max_by_shear_rule" in result.protocol.reinforcement
    assert "stirrup_qsw_rule_status" in result.protocol.reinforcement
    assert "stirrup_transverse_reinforcement_countable" in result.protocol.reinforcement
    assert result.protocol.geometry["h0"] == pytest.approx(
        result.selected_longitudinal.section.effective_depth()
    )
    assert result.protocol.geometry["local_axes_id"] == "design-test-local-axes"
    assert result.protocol.geometry["tension_face"] == "local_y_min"
    assert result.protocol.geometry["cover_reference"] == (
        "concrete_face_to_outer_stirrup_surface"
    )
    assert result.protocol.materials["Rb_base"] == pytest.approx(14.5)
    assert result.protocol.materials["gamma_b1"] == pytest.approx(1.0)
    assert result.protocol.materials["Rb_effective"] == pytest.approx(14.5)


def test_design_rectangular_forwards_load_duration():
    result = design_rectangular_element(mvp_input(load_duration="long"))

    assert result.status == "outside_applicability"
    assert result.strength_status == "outside_applicability"
    assert result.overall_status == "outside_applicability"
    assert result.selected_longitudinal is None
    assert result.selected_transverse is None
    assert result.protocol is None
    assert any("long load context" in warning and "shear" in warning for warning in result.warnings)
    assert result.project_use is False


def test_design_rejects_invalid_load_context_before_empty_enumeration():
    with pytest.raises(ValueError, match="load_duration"):
        design_rectangular_element(
            mvp_input(load_duration="bogus", main_bar_counts=())  # type: ignore[arg-type]
        )


def test_design_unsupported_longitudinal_material_is_outside_applicability():
    result = design_rectangular_element(mvp_input(longitudinal_rebar_class="A240"))

    assert result.status == "outside_applicability"
    assert result.strength_status == "outside_applicability"
    assert result.selected_longitudinal is None
    assert result.protocol is None
    assert result.project_use is False


def test_design_never_changes_stirrup_diameter_after_h0_is_derived():
    result = design_rectangular_element(
        mvp_input(
            b=150,
            h=300,
            cover=25,
            stirrup_diameter_for_geometry=6,
            concrete_class="B40",
            M=50_000_000,
            Q=80_000,
        )
    )

    assert result.status == "outside_applicability"
    assert result.selected_longitudinal is not None
    assert result.selected_transverse is not None
    assert result.selected_transverse.diameter == 6
    assert result.selected_longitudinal.section.stirrup_diameter == 6
    assert result.selected_transverse.section.effective_depth() == pytest.approx(
        result.selected_longitudinal.section.effective_depth()
    )


def test_design_fails_closed_when_geometry_stirrup_is_not_a_candidate():
    result = design_rectangular_element(
        mvp_input(
            stirrup_diameter_for_geometry=8,
            stirrup_diameters=(6, 10, 12),
        )
    )

    assert result.status == "outside_applicability"
    assert result.selected_transverse is None
    assert result.project_use is False
    assert any("h0 cannot be kept consistent" in warning for warning in result.warnings)


def test_design_rectangular_with_crack_check():
    result = design_rectangular_element(mvp_input(check_cracks=True, Mser=30_000_000))

    assert result.status == "outside_applicability"
    assert result.strength_status == "outside_applicability"
    assert result.serviceability_status == "review_or_fail"
    assert result.overall_status == "outside_applicability"
    assert result.crack_formation is not None
    assert result.crack_formation.status == "crack"
    assert result.crack_formation.requires_engineer_review is True
    assert result.protocol is not None
    assert result.protocol.serviceability_status == "review_or_fail"
    assert result.protocol.overall_status == "outside_applicability"
    assert "crack_formation" in result.protocol.checks
    assert any("crack width check is required" in warning for warning in result.warnings)


def test_design_rectangular_with_crack_width_check():
    result = design_rectangular_element(
        mvp_input(check_crack_width=True, Mser=30_000_000, acrc_limit=0.3)
    )

    assert result.status == "outside_applicability"
    assert result.strength_status == "outside_applicability"
    assert result.serviceability_status == "pass"
    assert result.overall_status == "outside_applicability"
    assert result.crack_formation is not None
    assert result.crack_width is not None
    assert result.crack_width.acrc >= 0
    assert result.protocol is not None
    assert result.protocol.serviceability_status == "pass"
    assert "crack_width" in result.protocol.checks


def test_design_rectangular_with_deflection_check():
    result = design_rectangular_element(
        mvp_input(check_deflection=True, Mser=10_000_000, span=6000)
    )

    assert result.status == "outside_applicability"
    assert result.strength_status == "outside_applicability"
    assert result.serviceability_status == "pass"
    assert result.overall_status == "outside_applicability"
    assert result.crack_formation is not None
    assert result.deflection is not None
    assert result.deflection.requires_engineer_review is True
    assert result.protocol is not None
    assert result.protocol.serviceability_status == "pass"
    assert "deflection" in result.protocol.checks


def test_design_rectangular_with_deflection_fail_warning():
    result = design_rectangular_element(
        mvp_input(
            check_deflection=True,
            Mser=150_000_000,
            span=12_000,
            deflection_limit=1.0,
        )
    )

    assert result.status == "fail"
    assert result.strength_status == "outside_applicability"
    assert result.serviceability_status == "fail"
    assert result.overall_status == "fail"
    assert result.deflection is not None
    assert result.deflection.status == "fail"
    assert result.protocol is not None
    assert result.protocol.serviceability_status == "fail"
    assert result.protocol.overall_status == "fail"
    assert any("deflection exceeds draft limit" in warning for warning in result.warnings)
