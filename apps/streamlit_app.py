"""Streamlit prototype for deterministic rectangular element design."""

import streamlit as st

from sp63_core.materials import get_concrete, get_rebar
from sp63_core.sections import RectangularSection
from sp63_core.services import design_rectangular_element
from sp63_core.units import kN_to_N, kNm_to_Nmm

SAFETY_WARNING = (
    "Прототип предназначен для предварительного анализа. "
    "Результаты требуют инженерной проверки и не являются самостоятельной "
    "проектной документацией."
)


def main() -> None:
    """Run the Streamlit MVP interface."""
    st.set_page_config(page_title="SP63 rectangular design", layout="wide")
    st.title("SP63 rectangular element design")
    st.warning(SAFETY_WARNING)

    with st.sidebar:
        st.header("Geometry")
        b = st.number_input("b, mm", min_value=1.0, value=300.0, step=10.0)
        h = st.number_input("h, mm", min_value=1.0, value=500.0, step=10.0)
        cover = st.number_input("cover, mm", min_value=1.0, value=32.0, step=1.0)
        stirrup_diameter = st.number_input(
            "stirrup_diameter, mm",
            min_value=1.0,
            value=8.0,
            step=1.0,
        )
        main_bar_diameter = st.number_input(
            "main_bar_diameter, mm",
            min_value=1.0,
            value=20.0,
            step=1.0,
        )

        st.header("Materials")
        concrete_class = st.selectbox(
            "concrete_class",
            ("B15", "B20", "B25", "B30", "B35", "B40"),
            index=2,
        )
        longitudinal_rebar_class = st.selectbox(
            "longitudinal_rebar_class",
            ("A400", "A500"),
            index=1,
        )
        transverse_rebar_class = st.selectbox(
            "transverse_rebar_class",
            ("A240", "A400", "A500"),
            index=0,
        )

        st.header("Loads")
        M_kNm = st.number_input("M_kNm", min_value=0.0, value=150.0, step=10.0)
        Q_kN = st.number_input("Q_kN", min_value=0.0, value=80.0, step=5.0)

    if st.button("Рассчитать", type="primary"):
        _run_design(
            b=b,
            h=h,
            cover=cover,
            stirrup_diameter=stirrup_diameter,
            main_bar_diameter=main_bar_diameter,
            concrete_class=concrete_class,
            longitudinal_rebar_class=longitudinal_rebar_class,
            transverse_rebar_class=transverse_rebar_class,
            M_kNm=M_kNm,
            Q_kN=Q_kN,
        )


def _run_design(
    *,
    b: float,
    h: float,
    cover: float,
    stirrup_diameter: float,
    main_bar_diameter: float,
    concrete_class: str,
    longitudinal_rebar_class: str,
    transverse_rebar_class: str,
    M_kNm: float,
    Q_kN: float,
) -> None:
    try:
        section = RectangularSection(
            b=b,
            h=h,
            cover=cover,
            stirrup_diameter=stirrup_diameter,
            main_bar_diameter=main_bar_diameter,
        )
        result = design_rectangular_element(
            section=section,
            concrete=get_concrete(concrete_class),
            longitudinal_rebar=get_rebar(longitudinal_rebar_class),
            transverse_rebar=get_rebar(transverse_rebar_class),
            M=kNm_to_Nmm(M_kNm),
            Q=kN_to_N(Q_kN),
        )
    except ValueError as exc:
        st.error(str(exc))
        return

    st.subheader("Result")
    col1, col2, col3 = st.columns(3)
    col1.metric("Overall status", result.status)
    col2.metric("M, N*mm", f"{kNm_to_Nmm(M_kNm):,.0f}")
    col3.metric("Q, N", f"{kN_to_N(Q_kN):,.0f}")

    if result.selected_longitudinal is None:
        st.error("Selected longitudinal reinforcement: none")
    else:
        option = result.selected_longitudinal
        st.write("Selected longitudinal reinforcement")
        st.table(
            {
                "scheme": [option.scheme],
                "As, mm2": [round(option.As, 2)],
                "h0, mm": [round(option.section.effective_depth(), 2)],
                "utilization": [round(option.utilization, 3)],
                "status": [option.status],
            }
        )

    if result.selected_transverse is None:
        st.error("Selected transverse reinforcement: none")
    else:
        option = result.selected_transverse
        st.write("Selected transverse reinforcement")
        st.table(
            {
                "scheme": [option.scheme],
                "Asw, mm2": [round(option.Asw, 2)],
                "spacing, mm": [round(option.spacing, 2)],
                "steel_per_meter": [round(option.steel_per_meter, 2)],
                "utilization": [round(option.utilization, 3)],
                "status": [option.status],
            }
        )

    if result.warnings:
        st.warning("\n".join(result.warnings))
    st.write(f"requires_engineer_review: {result.requires_engineer_review}")


if __name__ == "__main__":
    main()
