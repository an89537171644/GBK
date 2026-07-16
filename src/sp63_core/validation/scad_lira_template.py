"""Manual SCAD/LIRA comparison template helpers."""


def build_scad_lira_comparison_template() -> list[dict[str, str]]:
    """Return blank rows for manual comparison against SCAD/LIRA results."""
    fields = (
        "case_id",
        "b",
        "h",
        "concrete_class",
        "rebar_class",
        "local_axes_id",
        "moment_axis",
        "tension_face",
        "load_duration",
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
        "completeness_status",
        "evidence_status",
        "project_use_status",
        "project_use",
        "requires_engineer_review",
    )
    row = {field: "" for field in fields}
    row.update(
        completeness_status="incomplete",
        evidence_status="needs_engineer_review",
        project_use_status="prohibited",
        project_use="false",
        requires_engineer_review="true",
    )
    return [row]
