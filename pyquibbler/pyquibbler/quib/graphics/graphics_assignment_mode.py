from contextlib import contextmanager
from typing import Optional

from matplotlib.axes import Axes

GRAPHICS_ASSIGNMENT_MODE_AXES: Optional[Axes] = None


def reset_all_graphics_assignment_mode():
    """
    Resets the graphics assignment mode to its initial state.
    """
    global GRAPHICS_ASSIGNMENT_MODE_AXES
    GRAPHICS_ASSIGNMENT_MODE_AXES = None


def is_reset_all_graphics_assignment_mode() -> bool:
    """
    Checks if the graphics assignment mode is in its initial state.
    """
    return GRAPHICS_ASSIGNMENT_MODE_AXES is None


@contextmanager
def graphics_assignment_mode(axes: Axes):
    """
    In graphics assignment mode. Indicating the axes invoking the assignment.
    """

    global GRAPHICS_ASSIGNMENT_MODE_AXES
    GRAPHICS_ASSIGNMENT_MODE_AXES = axes
    try:
        yield
    finally:
        GRAPHICS_ASSIGNMENT_MODE_AXES = None


def get_graphics_assignment_mode_axes() -> Optional[Axes]:
    return GRAPHICS_ASSIGNMENT_MODE_AXES


def is_within_graphics_assignment_mode() -> bool:
    return GRAPHICS_ASSIGNMENT_MODE_AXES is not None
