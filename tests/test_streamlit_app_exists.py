from pathlib import Path


def test_streamlit_app_file_exists_and_uses_design_service():
    app_path = Path("apps/streamlit_app.py")
    content = app_path.read_text(encoding="utf-8")

    assert app_path.exists()
    assert "design_rectangular_element" in content
    assert "инженерной проверки" in content
    assert "kNm_to_Nmm" in content
    assert "kN_to_N" in content
