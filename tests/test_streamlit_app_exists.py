from pathlib import Path


def test_streamlit_app_file_exists_and_uses_design_service():
    app_path = Path("apps/streamlit_app.py")
    content = app_path.read_text(encoding="utf-8")

    assert app_path.exists()
    assert "design_rectangular_element" in content
    assert "инженерной проверки" in content
    assert "kNm_to_Nmm" in content
    assert "kN_to_N" in content


def test_streamlit_app_has_required_inputs_and_no_ml_dependency():
    content = Path("apps/streamlit_app.py").read_text(encoding="utf-8")

    required_snippets = (
        "b, mm",
        "h, mm",
        "cover, mm",
        "stirrup_diameter, mm",
        "main_bar_diameter, mm",
        "concrete_class",
        "longitudinal_rebar_class",
        "transverse_rebar_class",
        "M_kNm",
        "Q_kN",
        "requires_engineer_review",
    )

    for snippet in required_snippets:
        assert snippet in content
    assert "sp63_core.ml" not in content
