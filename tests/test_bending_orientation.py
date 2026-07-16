import pytest

from sp63_core.sections import RectangularBendingOrientation


def test_orientation_requires_nonempty_axes_identifier():
    with pytest.raises(ValueError, match="local_axes_id"):
        RectangularBendingOrientation("", "local_z", "local_y_min")


def test_orientation_rejects_unsupported_moment_axis():
    with pytest.raises(ValueError, match="moment_axis"):
        RectangularBendingOrientation("axes-1", "global_x", "local_y_min")


def test_orientation_rejects_unknown_tension_face():
    with pytest.raises(ValueError, match="tension_face"):
        RectangularBendingOrientation("axes-1", "local_z", "automatic")


def test_orientation_exposes_opposite_compression_face():
    minimum_face = RectangularBendingOrientation(
        "axes-1", "local_z", "local_y_min"
    )
    maximum_face = RectangularBendingOrientation(
        "axes-1", "local_z", "local_y_max"
    )

    assert minimum_face.compression_face == "local_y_max"
    assert maximum_face.compression_face == "local_y_min"
