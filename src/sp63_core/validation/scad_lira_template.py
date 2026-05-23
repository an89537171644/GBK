"""Manual SCAD/LIRA comparison template helpers."""


def build_scad_lira_comparison_template() -> list[dict[str, str]]:
    """Return blank rows for manual comparison against SCAD/LIRA results."""
    fields = (
        "case_id",
        "b",
        "h",
        "concrete_class",
        "rebar_class",
        "M",
        "Q",
        "program_As",
        "program_stirrups",
        "scad_As",
        "lira_As",
        "delta_As_percent",
        "program_Mult",
        "scad_Mult",
        "lira_Mult",
        "delta_Mult_percent",
        "engineer_comment",
        "accepted",
    )
    return [{field: "" for field in fields}]
