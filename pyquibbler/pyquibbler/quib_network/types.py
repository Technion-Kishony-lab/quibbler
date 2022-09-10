from pyquibbler.utilities.basic_types import StrEnum


class Direction(StrEnum):
    """
    Define upstream/downstream directions in quib dependency graph.

    See Also
    --------
    dependency_graph
    """

    UPSTREAM = 'upstream'
    "Towards quibs affecting current quib (``'upstream'``)."

    DOWNSTREAM = 'downstream'
    "Towards quibs affected by current quib (``'downstream'``)."

    BOTH = 'both'
    "Towards both upstream and downstream directions (``'both'``)."

    ALL = 'all'
    "Fully explore the network from the current quib (``'all'``)."


def reverse_direction(direction: Direction) -> Direction:
    if direction is Direction.UPSTREAM:
        return Direction.DOWNSTREAM
    if direction is Direction.DOWNSTREAM:
        return Direction.UPSTREAM
    return direction
