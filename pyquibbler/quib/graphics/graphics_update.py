from pyquibbler.utils import StrEnum


class GraphicsUpdateType(StrEnum):
    """
    Options for specifying when to refresh a graphics quib upon upstream assignments.

    Options are:
    "drag":     refresh immediately as upstream objects are dragged, or when manually assigned to.
    "drop":     refresh at end of dragging, upon graphic object drop.
    "central":  do not automatically refresh. Refresh, centrally upon refresh_graphics().
    "never":    Never refresh.

    Returns
    -------
    "drag", "drop", "central", "never", or None

    See Also
    --------
    GraphicsUpdateType, Project.refresh_graphics
    """

    DRAG = 'drag'
    DROP = 'drop'
    CENTRAL = 'central'
    NEVER = 'never'
