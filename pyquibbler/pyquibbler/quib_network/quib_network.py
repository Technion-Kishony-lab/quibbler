from typing import Union

import ipycytoscape
import ipywidgets as widgets
import networkx as nx

from .types import Direction, QuibNode
from .. import Quib
from ..utilities.input_validation_utils import validate_user_input, get_enum_by_str


NETWORK_STYLE = [
    {
        'selector': 'node.iquib',
        'css': {
            'background-color': 'red'
        }
    },
    {
        'selector': 'node.fquib',
        'css': {
            'background-color': 'green'
        }
    }]


def quib_class(quib: Quib) -> str:
    if quib.is_iquib:
        return 'iquib'
    else:
        return 'fquib'


def quib_node(quib: Quib) -> QuibNode:
    return QuibNode(quib.name, classes=quib_class(quib))


# @validate_user_input(quib=Quib,
#                      direction=(type(None), str, Direction),
#                      depth=(type(None), int),
#                      include_unnamed_quibs=bool)
def quib_network(quib: Quib,
                 direction: Union[None, str, Direction] = None,
                 depth: int = None,
                 include_unnamed_quibs: bool = False):
    """
    Draw a network of quibs

    Parameters
    ----------
    quib : Quib
        The focal quib around which to extend the network

    direction : Direction or str
        Direction of network extension, 'upstream', 'downstream', 'both' (default)

    depth : int or None
        The number of steps of network extension. `None` for infinity (default).

    include_unnamed_quibs : True, False (default)
        Whether to include also quibs with no name (whose `assigned_named` is `None`).

    See Also
    --------
    Direction, Quib.get_parents, Quib.get_children, Quib.get_ancestors, Quib.get_descendants
    """
    direction = get_enum_by_str(Direction, direction, allow_none=True)
    direction = direction or Direction.BOTH

    graph = nx.Graph()
    graph.add_node(quib_node(quib))
    if direction is Direction.UPSTREAM or direction is Direction.BOTH:
        if include_unnamed_quibs:
            parents = quib.parents
        else:
            parents = quib.named_parents
        for parent in parents:
            graph.add_node(quib_node(parent))
            graph.add_edge(quib_node(parent), quib_node(quib))

    if direction is Direction.DOWNSTREAM or direction is Direction.BOTH:
        if include_unnamed_quibs:
            children = quib.children
        else:
            children = quib.named_children
        for child in children:
            graph.add_node(quib_node(child))
            graph.add_edge(quib_node(quib), quib_node(child))

    network_widget = ipycytoscape.CytoscapeWidget()
    network_widget.graph.add_graph_from_networkx(graph, directed=True)
    # network_widget.set_style(NETWORK_STYLE)
    return network_widget
