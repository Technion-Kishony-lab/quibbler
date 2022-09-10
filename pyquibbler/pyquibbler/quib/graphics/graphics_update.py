from pyquibbler.utilities.basic_types import StrEnum


class GraphicsUpdateType(StrEnum):
    """
    Options for specifying when to refresh a graphics quib.

    See Also
    --------
    pyquibbler.refresh_graphics, Quib.graphics_update
    """

    DRAG = 'drag'
    "Refresh immediately as graphics object are dragged (``'drag'``)."

    DROP = 'drop'
    "Refresh at end of dragging, upon mouse drop (``'drop'``)."

    CENTRAL = 'central'
    "Do not refresh automatically; only refresh upon explicit `refresh_graphics` command (``'central'``)."

    NEVER = 'never'
    "Do not refresh (``'never'``)."
