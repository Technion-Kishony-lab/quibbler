from pyquibbler.utils import StrEnum


class Direction(StrEnum):
    """
    Define upstream, downstream directions in quib graph:

    See Also
    --------
    quib_network
    """

    UPSTREAM = 'upstream'
    "``'upstream'``;  towards quibs affecting current quib"

    DOWNSTREAM = 'downstream'
    "``'downstream'``;  towards quibs affected by current quib"

    BOTH = 'both'
    "``'both'``;  towards upstream and downstream"

    ALL = 'all'
    "``'all'``;  fully explore the network from the current quib"


def reverse_direction(direction: Direction) -> Direction:
    if direction is Direction.UPSTREAM:
        return Direction.DOWNSTREAM
    if direction is Direction.DOWNSTREAM:
        return Direction.UPSTREAM
    return direction
