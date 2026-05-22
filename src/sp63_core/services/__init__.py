"""High-level deterministic design services for SP 63 MVP workflows."""

from sp63_core.services.rectangular_design import (
    RectangularDesignResult,
    design_rectangular_element,
)

__all__ = [
    "RectangularDesignResult",
    "design_rectangular_element",
]
