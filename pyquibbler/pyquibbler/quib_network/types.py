import ipycytoscape

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


class QuibNode(ipycytoscape.Node):
    def __init__(self, name, classes=''):
        super().__init__()
        self.data['id'] = name
        self.classes = classes
