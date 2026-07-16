"""Resolve first-limit-state material values for a declared load combination."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from sp63_core.materials.concrete import Concrete
    from sp63_core.materials.rebar import Rebar

LoadDuration = Literal["short", "long"]
LoadCombination = Literal["permanent_long_short", "permanent_long"]

NORMATIVE_PROFILE_ID = "SP63-2018-AMD1-AMD2-PROVISIONAL@2026-07-15"
SUPPORTED_ULS_CONCRETE_CLASSES = frozenset(("B15", "B20", "B25", "B30", "B35", "B40"))
SUPPORTED_ULS_LONGITUDINAL_REBAR_CLASSES = frozenset(("A400", "A500"))

_LOAD_CONTEXT: dict[LoadDuration, tuple[LoadCombination, float]] = {
    "short": ("permanent_long_short", 1.0),
    "long": ("permanent_long", 0.9),
}


@dataclass(frozen=True, slots=True)
class ULSMaterialContext:
    """Resolved provisional ULS resistances with load/source provenance."""

    load_duration: LoadDuration
    load_combination: LoadCombination
    normative_profile_id: str
    Rb_base: float
    gamma_b1: float
    Rb_effective: float
    Rsc: float
    source_clauses: tuple[str, ...]
    requires_engineer_review: bool = True


class UnsupportedULSMaterialProfileError(ValueError):
    """Raised when inputs cannot be matched to the scoped provisional catalog."""


def resolve_uls_material_context(
    concrete: Concrete,
    rebar: Rebar,
    load_duration: LoadDuration,
) -> ULSMaterialContext:
    """Return the provisional context for one supported ULS load combination.

    ``short`` identifies a combination containing short-term loads.
    ``long`` identifies a combination containing only permanent and long-term
    loads. The closed vocabulary prevents an unspecified combination from
    silently selecting a concrete working-condition factor.
    """
    try:
        load_combination, gamma_b1 = _LOAD_CONTEXT[load_duration]
    except KeyError as exc:
        raise ValueError("load_duration must be 'short' or 'long'") from exc

    _validate_catalog_profile(concrete=concrete, rebar=rebar)

    Rb_base = concrete.Rb
    return ULSMaterialContext(
        load_duration=load_duration,
        load_combination=load_combination,
        normative_profile_id=NORMATIVE_PROFILE_ID,
        Rb_base=Rb_base,
        gamma_b1=gamma_b1,
        Rb_effective=Rb_base * gamma_b1,
        Rsc=rebar.get_Rsc(load_duration),
        source_clauses=(
            "SP 63.13330.2018 clause 6.1.11, tables 6.8-6.9 "
            "(base concrete strengths)",
            "SP 63.13330.2018 clause 6.1.12(a) "
            "(gamma_b1 by load duration)",
            "SP 63.13330.2018 clauses 6.2.7-6.2.8, tables 6.13-6.14; "
            "provisional A400 Amendment 1 values require source evidence",
        ),
    )


def _validate_catalog_profile(*, concrete: Concrete, rebar: Rebar) -> None:
    """Fail closed unless both objects exactly match the scoped catalog rows."""
    # Local imports avoid the dependency cycle created by Rebar importing the
    # closed LoadDuration vocabulary from this module.
    from sp63_core.materials.concrete import CONCRETE_CATALOG
    from sp63_core.materials.rebar import REBAR_CATALOG

    if concrete.class_name not in SUPPORTED_ULS_CONCRETE_CLASSES:
        raise UnsupportedULSMaterialProfileError(
            f"unsupported ULS concrete class {concrete.class_name!r}"
        )
    if rebar.class_name not in SUPPORTED_ULS_LONGITUDINAL_REBAR_CLASSES:
        raise UnsupportedULSMaterialProfileError(
            f"unsupported ULS longitudinal rebar class {rebar.class_name!r}"
        )

    catalog_concrete = CONCRETE_CATALOG.get(concrete.class_name)
    catalog_rebar = REBAR_CATALOG.get(rebar.class_name)
    if catalog_concrete is None or concrete.model_dump() != catalog_concrete.model_dump():
        raise UnsupportedULSMaterialProfileError(
            "concrete values do not match the scoped catalog profile"
        )
    if catalog_rebar is None or rebar.model_dump() != catalog_rebar.model_dump():
        raise UnsupportedULSMaterialProfileError(
            "rebar values do not match the scoped catalog profile"
        )
