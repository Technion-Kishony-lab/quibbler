import dataclasses
import ipycytoscape

from typing import Union, Set, List, Tuple, Optional
from .types import Direction
from .. import Quib
from ..utilities.input_validation_utils import validate_user_input, get_enum_by_str

infinity = float('inf')


NETWORK_STYLE = \
    [
        {
            'selector': 'edge',
            'style': {'width': 3, 'line-color': '#909090'}
        },

        {
            'selector': 'edge.directed',
            'style': {'curve-style': 'bezier',
                      'target-arrow-shape': 'triangle',
                      'target-arrow-color': '#909090'}
        },

        {
            'selector': 'node',
            'css': {
                'content': 'data(name)',
                'text-valign': 'center',
                'text-halign': 'right',
                'background-color': '#00D7FF',
                'border-color': 'black',
                'border-width': 0.5,
            }
        },

        {
            'selector': ':selected',
            'css': {
                'background-color': 'black',
                'line-color': 'black',
                'target-arrow-color': 'black',
                'source-arrow-color': 'black',
                'text-outline-color': 'black',
            }
        },

        {
            'selector': 'node.iquib',
            'css': {
                'shape': "diamond",
                'text-valign': 'top',
                'text-halign': 'center',
            }
        },

        {
            'selector': 'node.origin',
            'css': {
                'background-color': '#D61C4E',
                'font-size': 16,
            }
        },

        {
            'selector': 'node.graphics',
            'css': {
                'shape': "hexagon",
            }
        },

        {
            'selector': 'node.overridden',
            'css': {
                'border-color': '#5800FF',
                'border-width': 6,
                'border-style': 'dashed',
            }
        },

    ]

NETWORK_LAYOUT = {
    'name': 'dagre',  # can try: dagre elk
    'spacingFactor': 1.2,
    'nodeSpacing': 2,
    'edgeLengthVal': 0,
}

def get_quib_class(quib: Quib) -> str:
    classes = ''
    if quib.is_iquib:
        classes += ' iquib'
    if quib.is_graphics:
        classes += ' graphics'
    if quib.get_override_list() is not None and len(quib.get_override_list()) > 0:
        classes += ' overridden'
    return classes


class QuibNode(ipycytoscape.Node):
    def __init__(self, id: int, name: str, classes: str = ""):
        super().__init__()
        self.data['id'] = id
        self.data['name'] = name
        self.classes += classes

    @classmethod
    def from_quib(cls, quib: Quib):
        return cls(id(quib), quib.pretty_repr, classes=get_quib_class(quib))


class QuibEdge(ipycytoscape.Edge):
    def __init__(self, source, target):
        super().__init__()
        self.data['source'] = id(source)
        self.data['target'] = id(target)
        self.classes += " directed "

@dataclasses.dataclass
class QuibNetwork:
    origin_quib: Quib
    direction: Union[str, Direction] = Direction.BOTH
    depth: int = infinity
    limit_to_named_quibs: bool = True
    _quibs: Optional[Set[Quib]] = None
    _links: Optional[Set[Tuple[Quib, Quib]]] = None

    def __post_init__(self):
        self.depth = self.depth or infinity
        self.direction = get_enum_by_str(Direction, self.direction, allow_none=True) or Direction.BOTH

    @staticmethod
    def _get_neighbour_quibs(quib: Quib, direction: Direction, limit_to_named_quibs: bool) -> Set[Quib]:
        quibs = set()
        if direction is not Direction.UPSTREAM:
            quibs |= quib.get_children(limit_to_named_quibs=limit_to_named_quibs)
        if direction is not Direction.DOWNSTREAM:
            quibs |= quib.get_parents(limit_to_named_quibs=limit_to_named_quibs)
        return quibs

    def _get_quibs_connected_up_down_or_all(self, direction: Direction) -> Set[Quib]:

        assert direction is not Direction.BOTH
        quibs = set()

        def _get_quibs_recursively(quib: Quib, depth: int):
            nonlocal quibs
            if quib in quibs:
                return
            quibs.add(quib)
            if depth > 0:
                for neighbour_quib in self._get_neighbour_quibs(quib, direction, self.limit_to_named_quibs):
                    _get_quibs_recursively(neighbour_quib, depth - 1)
        _get_quibs_recursively(self.origin_quib, self.depth)
        return quibs

    def get_quibs_connected_to_origin_quib(self) -> Set[Quib]:
        if self.direction is Direction.BOTH:
            quibs = self._get_quibs_connected_up_down_or_all(Direction.UPSTREAM) \
                    | self._get_quibs_connected_up_down_or_all(Direction.DOWNSTREAM)
        else:
            quibs = self._get_quibs_connected_up_down_or_all(self.direction)

        return quibs

    def get_connecting_links(self) -> Set[Tuple[Quib,Quib]]:
        quibs = self.quibs
        links = set()
        for i, quib in enumerate(quibs):
            children = self._get_neighbour_quibs(quib, Direction.DOWNSTREAM, self.limit_to_named_quibs)
            children &= quibs
            links |= {(quib, child) for child in children}
        return links

    @property
    def quibs(self) -> Set[Quib]:
        if self._quibs is None:
            self._quibs = self.get_quibs_connected_to_origin_quib()
        return self._quibs

    @property
    def links(self) -> Set[Tuple[Quib,Quib]]:
        if self._links is None:
            self._links = self.get_connecting_links()
        return self._links

    def create_quib_node(self, quib):
        node = QuibNode.from_quib(quib)
        if quib is self.origin_quib:
            node.classes += ' origin'
        return node

    def get_network_widget(self) -> ipycytoscape.CytoscapeWidget:
        network_widget = ipycytoscape.CytoscapeWidget()
        network_widget.graph.add_nodes([self.create_quib_node(quib) for quib in self.quibs])
        network_widget.graph.add_edges([QuibEdge(source, target) for source, target in self.links], directed=True)
        network_widget.set_style(NETWORK_STYLE)
        network_widget.set_layout(**NETWORK_LAYOUT)
        return network_widget


@validate_user_input(origin_quib=Quib,
                     direction=(type(None), str, Direction),
                     depth=(type(None), int),
                     limit_to_named_quibs=bool)
def quib_network(origin_quib: Quib,
                 direction: Union[None, str, Direction] = None,
                 depth: int = None,
                 limit_to_named_quibs: bool = True) -> ipycytoscape.CytoscapeWidget:
    """
    Draw a network of quibs

    Parameters
    ----------
    origin_quib : Quib
        The focal quib around which to extend the network

    direction : Direction or str
        Direction of network extension, 'upstream', 'downstream', 'both', 'all' (default)

    depth : int or None
        The number of steps of network extension. `None` for infinity (default).

    limit_to_named_quibs : True (default) or False
        indicates whether to limit to named quibs or also include unnamed quibs.
        Unnamed quibs are quibs whose `assigned_name` is `None`, typically representing intermediate calculations.

    See Also
    --------
    Direction, Quib.get_parents, Quib.get_children, Quib.get_ancestors, Quib.get_descendants
    """

    return QuibNetwork(origin_quib, direction, depth, limit_to_named_quibs).get_network_widget()
