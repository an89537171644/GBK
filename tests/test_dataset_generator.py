import csv
from dataclasses import replace

import pytest

from sp63_core.dataset import (
    DATASET_COLUMNS,
    DATASET_VERSION,
    export_dataset_csv,
    generate_dataset_cases,
)


def test_generate_dataset_cases_matches_schema_and_uses_safe_results():
    cases = generate_dataset_cases(limit=5, load_duration="short")

    assert len(cases) == 5
    assert cases[0].case_id == "case_000001"
    assert tuple(cases[0].as_row()) == DATASET_COLUMNS
    assert all(case.group_key for case in cases)
    assert all(case.element_type == "beam" for case in cases)
    assert all(case.cover == 32.0 for case in cases)
    assert all(case.geometry_stirrup_diameter == 8 for case in cases)
    assert all(case.status == "pass" for case in cases)
    assert all(case.As_required == pytest.approx(case.As_provided) for case in cases)
    assert all(case.bending_utilization <= 1.0 for case in cases)
    assert all(case.shear_utilization <= 1.0 for case in cases)
    assert all(case.main_bar_count > 0 for case in cases)
    assert all(case.main_bar_diameter > 0 for case in cases)
    assert all(case.main_rebar_constructive_status == "pass" for case in cases)
    assert all(case.main_rebar_ratio_percent >= 0.1 for case in cases)
    assert all(case.main_rebar_layout_feasible is True for case in cases)
    assert all(case.stirrup_diameter > 0 for case in cases)
    assert all(case.stirrup_legs > 0 for case in cases)
    assert all(case.stirrup_spacing > 0 for case in cases)
    assert all(case.stirrup_Asw > 0 for case in cases)
    assert all(case.stirrup_steel_consumption > 0 for case in cases)
    assert all(case.stirrup_constructive_status in ("pass", "warning") for case in cases)
    assert all(case.stirrup_constructive_max_spacing > 0 for case in cases)
    assert all(case.stirrup_sw_max_by_shear_rule > 0 for case in cases)
    assert all(case.stirrup_qsw_rule_status == "pass" for case in cases)
    assert all(case.stirrup_transverse_reinforcement_countable is True for case in cases)
    assert all(case.section_b_mm == case.b for case in cases)
    assert all(case.section_h_mm == case.h for case in cases)
    assert all(case.effective_depth_mm == pytest.approx(case.h0) for case in cases)
    assert all(case.cover_mm == pytest.approx(case.cover) for case in cases)
    assert all(case.main_bar_diameter_mm == case.main_bar_diameter for case in cases)
    assert all(case.stirrup_diameter_mm == case.stirrup_diameter for case in cases)
    assert all(case.stirrup_spacing_mm == case.stirrup_spacing for case in cases)
    assert all(case.main_rebar_class == case.rebar_class for case in cases)
    assert all(case.stirrup_rebar_class == case.stirrup_class for case in cases)
    assert all(case.moment_nmm == pytest.approx(case.M) for case in cases)
    assert all(case.shear_n == pytest.approx(case.Q) for case in cases)
    assert all(case.moment_service_nmm >= 0 for case in cases)
    assert all(case.span_mm > 0 for case in cases)
    assert all(case.longitudinal_as_mm2 == pytest.approx(case.As_provided) for case in cases)
    assert all(case.transverse_asw_mm2 == pytest.approx(case.stirrup_Asw) for case in cases)
    assert all(case.bending_mult_nmm == pytest.approx(case.Mult) for case in cases)
    assert all(case.shear_qult_n == pytest.approx(case.Qult) for case in cases)
    assert all(case.mcrc_nmm > 0 for case in cases)
    assert all(case.crack_width_mm >= 0 for case in cases)
    assert all(case.deflection_mm >= 0 for case in cases)
    assert all(case.bending_status == "pass" for case in cases)
    assert all(case.shear_status == "pass" for case in cases)
    assert all(case.crack_formation_status in ("no_crack", "crack") for case in cases)
    assert all(case.crack_width_status in ("not_required", "pass") for case in cases)
    assert all(case.deflection_status == "pass" for case in cases)
    assert all(case.strength_status == "pass" for case in cases)
    assert all(case.serviceability_status == "pass" for case in cases)
    assert all(case.overall_status == "pass" for case in cases)
    assert all(case.warnings_count >= 0 for case in cases)
    assert all(case.requires_engineer_review is True for case in cases)
    assert all(case.unsafe_row is False for case in cases)
    assert all(case.dataset_source == "diagnostic_regression_sp63_core" for case in cases)
    assert all(case.status_scope == "diagnostic" for case in cases)
    assert all(case.dataset_version == "0.3" == DATASET_VERSION for case in cases)
    assert all(case.local_axes_id == "synthetic-dataset-local-axes" for case in cases)
    assert all(case.moment_axis == "local_z" for case in cases)
    assert all(case.tension_face == "local_y_min" for case in cases)
    assert all(case.load_duration == "short" for case in cases)
    assert all(case.completeness_status == "incomplete" for case in cases)
    assert all(case.evidence_status == "needs_engineer_review" for case in cases)
    assert all(case.project_use_status == "prohibited" for case in cases)
    assert all(case.project_use is False for case in cases)


def test_generate_dataset_cases_respects_limit():
    cases = generate_dataset_cases(limit=3, load_duration="short")

    assert [case.case_id for case in cases] == ["case_000001", "case_000002", "case_000003"]


def test_generate_dataset_cases_uses_selected_option_section_h0():
    case = generate_dataset_cases(limit=1, load_duration="short")[0]
    selected_diameter = float(case.main_rebar_scheme.split("D", maxsplit=1)[1])

    assert case.h0 == pytest.approx(case.h - 32.0 - 8.0 - selected_diameter / 2.0)


def test_generate_dataset_cases_requires_explicit_load_duration():
    with pytest.raises(TypeError, match="load_duration"):
        generate_dataset_cases(limit=1)


def test_generate_dataset_cases_rejects_long_until_shear_context_is_supported():
    with pytest.raises(ValueError, match="shear load-combination context"):
        generate_dataset_cases(limit=1, load_duration="long")


def test_dataset_case_rejects_removed_review_gate_or_unknown_source():
    case = generate_dataset_cases(limit=1, load_duration="short")[0]

    with pytest.raises(ValueError, match="unsupported dataset_version"):
        replace(case, dataset_version="0.2")
    with pytest.raises(ValueError, match="requires_engineer_review"):
        replace(case, requires_engineer_review=False)
    with pytest.raises(ValueError, match="dataset_source"):
        replace(case, dataset_source="legacy_import")


def test_generate_dataset_cases_writes_service_inputs():
    case = generate_dataset_cases(
        limit=1,
        load_duration="short",
        moments=(100_000_000,),
        span=7500,
    )[0]

    assert case.moment_nmm == pytest.approx(100_000_000)
    assert case.moment_service_nmm == pytest.approx(20_000_000)
    assert case.span_mm == pytest.approx(7500)


def test_generate_dataset_cases_rejects_invalid_service_inputs():
    with pytest.raises(ValueError, match="service_moment_ratio must be non-negative"):
        generate_dataset_cases(
            limit=1,
            load_duration="short",
            service_moment_ratio=-0.1,
        )
    with pytest.raises(ValueError, match="span must be positive"):
        generate_dataset_cases(limit=1, load_duration="short", span=0)


def test_generate_dataset_cases_rejects_invalid_limit():
    with pytest.raises(ValueError, match="limit must be positive"):
        generate_dataset_cases(limit=0, load_duration="short")


def test_generate_dataset_cases_rejects_unsupported_element_type():
    with pytest.raises(ValueError, match="only beam element_type is supported"):
        generate_dataset_cases(
            limit=1,
            load_duration="short",
            element_types=("slab",),
        )


def test_generate_dataset_cases_geometry_stirrup_matches_selected_stirrup():
    cases = generate_dataset_cases(limit=10, load_duration="short")

    assert all(case.geometry_stirrup_diameter == case.stirrup_diameter for case in cases)


def test_generate_dataset_cases_rejects_unsupported_geometry_stirrup_diameter():
    with pytest.raises(ValueError, match="section_stirrup_diameter must be one of supported"):
        generate_dataset_cases(
            limit=1,
            load_duration="short",
            section_stirrup_diameter=7,
        )


def test_generate_dataset_cases_shuffle_reproducible():
    cases_a = generate_dataset_cases(limit=20, load_duration="short", seed=42)
    cases_b = generate_dataset_cases(limit=20, load_duration="short", seed=42)

    assert [_case_signature(case) for case in cases_a] == [
        _case_signature(case) for case in cases_b
    ]


def test_generate_dataset_cases_shuffle_changes_order_for_different_seed():
    cases_a = generate_dataset_cases(limit=20, load_duration="short", seed=42)
    cases_b = generate_dataset_cases(limit=20, load_duration="short", seed=43)

    assert [_case_signature(case) for case in cases_a] != [
        _case_signature(case) for case in cases_b
    ]


def test_generate_dataset_cases_assigns_case_ids_after_selection():
    cases = generate_dataset_cases(limit=7, load_duration="short")

    assert [case.case_id for case in cases] == [
        f"case_{index:06d}" for index in range(1, 8)
    ]


def test_export_dataset_csv(tmp_path):
    cases = generate_dataset_cases(limit=2, load_duration="short")
    output_path = export_dataset_csv(cases, tmp_path / "generated" / "dataset.csv")

    with output_path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    assert reader.fieldnames == list(DATASET_COLUMNS)
    assert len(rows) == 2
    assert rows[0]["case_id"] == "case_000001"
    assert rows[0]["cover"] == "32.0"
    assert rows[0]["status"] == "pass"
    assert rows[0]["dataset_source"] == "diagnostic_regression_sp63_core"
    assert rows[0]["status_scope"] == "diagnostic"
    assert rows[0]["strength_status"] == "pass"
    assert rows[0]["serviceability_status"] == "pass"
    assert rows[0]["overall_status"] == "pass"
    assert rows[0]["dataset_version"] == "0.3"
    assert rows[0]["local_axes_id"] == "synthetic-dataset-local-axes"
    assert rows[0]["moment_axis"] == "local_z"
    assert rows[0]["tension_face"] == "local_y_min"
    assert rows[0]["completeness_status"] == "incomplete"
    assert rows[0]["evidence_status"] == "needs_engineer_review"
    assert rows[0]["project_use_status"] == "prohibited"
    assert rows[0]["project_use"] == "False"


def _case_signature(case) -> tuple[object, ...]:
    return (
        case.group_key,
        case.M,
        case.Q,
        case.main_rebar_scheme,
        case.stirrup_scheme,
    )
