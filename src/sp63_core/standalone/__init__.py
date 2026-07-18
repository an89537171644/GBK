"""Research-only standalone rectangular-beam workflow facade.

The standalone layer adapts human-facing manual force units to the existing
public engineering workflow.  It does not implement calculation formulas and
does not authorize project use.
"""

from sp63_core.standalone.controller import (
    adapt_standalone_beam_input,
    run_standalone_beam_case,
)
from sp63_core.standalone.model import (
    STANDALONE_ELEMENT_TYPE,
    STANDALONE_LOAD_DURATION,
    StandaloneBeamInput,
    StandaloneRunResult,
)

__all__ = [
    "STANDALONE_ELEMENT_TYPE",
    "STANDALONE_LOAD_DURATION",
    "StandaloneBeamInput",
    "StandaloneRunResult",
    "adapt_standalone_beam_input",
    "run_standalone_beam_case",
]
