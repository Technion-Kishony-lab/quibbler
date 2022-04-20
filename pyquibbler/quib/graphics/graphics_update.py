from pyquibbler.utils import StrEnum


class GraphicsUpdateType(StrEnum):
    """
    Options for specifying when to refresh a graphics quib upon upstream assignments.

    See Also
    --------
    pyquibbler.refresh_graphics, Quib.graphics_update
    """

    DRAG = 'drag'
    "Refresh immediately as graphics object are dragged (``'drag'``)."

    DROP = 'drop'
    "refresh at end of dragging, upon graphic object drop (``'drop'``)."

    CENTRAL = 'central'
    "Do not refresh automaitcally; only refresh upon explicit ``refresh_graphics`` command (``'central'``)."

    NEVER = 'never'
    "Do not refresh (``'never'``)."
