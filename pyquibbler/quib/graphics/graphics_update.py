from pyquibbler.utils import StrEnum


class GraphicsUpdateType(StrEnum):
    """
    Options for specifying when to refresh a graphics quib upon upstream assignments.

    ``'drag'``:     refresh immediately as upstream objects are dragged, or when manually assigned to.

    ``'drop'``:     refresh at end of dragging, upon graphic object drop.

    ``'central'``:  do not automatically refresh. Refresh, centrally upon refresh_graphics().

    ``'never'``:    Never refresh.

    See Also
    --------
    Project.refresh_graphics, Quib.graphics_update
    """

    DRAG = 'drag'
    DROP = 'drop'
    CENTRAL = 'central'
    NEVER = 'never'
