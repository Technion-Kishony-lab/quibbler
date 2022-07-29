import dataclasses
import ipycytoscape

from typing import Union, Set, List, Tuple, Optional

import ipywidgets

from .types import Direction, reverse_direction
from .. import Quib
from ..utilities.input_validation_utils import validate_user_input, get_enum_by_str

infinity = float('inf')

NETWORK_STYLE = \
    [
        {
            'selector': 'edge',
            'style': {
                'width': 3,
                'line-color': '#909090'
            }
        },

        {
            'selector': 'edge.directed',
            'style': {
                'curve-style': 'bezier',
                'target-arrow-shape': 'triangle',
                'target-arrow-color': '#909090'
            }
        },

        {
            'selector': 'edge.data_source',
            'style': {
                'line-color': '#00D7FF',
                'target-arrow-color': '#00D7FF'
            }
        },

        {
            'selector': 'node',
            'css': {
                'content': 'data(name)',
                'text-valign': 'center',
                'text-halign': 'right',
                'background-color': '#00D7FF',
                'border-color': 'black',
                'font-size': 12,
                'border-width': 0.5,
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
            'selector': 'node.focal',
            'css': {
                'background-color': '#D61C4E',
            }
        },

        {
            'selector': 'node.null',
            'css': {
                'background-color': '#C0C0C0',
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

        {
            'selector': 'node.hidden',
            'css': {
                'background-color': '#A0A0A0',
                'width': 10,
                'height': 10,
                'text-valign': 'top',
                'text-halign': 'center',
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
    def __init__(self, id: int, name: str, tooltip: str, classes: str = "", position: Optional[Tuple[int, int]] = None):
        super().__init__()
        self.data['id'] = id
        self.data['name'] = name
        self.data['tooltip'] = tooltip
        self.classes += classes
        if position is not None:
            self.position = {'x': position[0], 'y': position[1]}

    @classmethod
    def from_quib(cls, quib: Quib):
        tooltip = quib.display().get_html_repr()
        return cls(id(quib), quib.pretty_repr, tooltip, classes=get_quib_class(quib))


class QuibEdge(ipycytoscape.Edge):
    def __init__(self, source_id: int, target_id: int, is_data: bool):
        super().__init__()
        self.data['source'] = source_id
        self.data['target'] = target_id
        self.classes += " directed "
        if is_data:
            self.classes += " data_source "


def _get_neighbour_quibs(quib: Quib, direction: Direction, limit_to_named_quibs: bool) -> Set[Quib]:
    quibs = set()
    if direction is not Direction.UPSTREAM:
        quibs |= quib.get_children(limit_to_named_quibs=limit_to_named_quibs)
    if direction is not Direction.DOWNSTREAM:
        quibs |= quib.get_parents(limit_to_named_quibs=limit_to_named_quibs)
    return quibs


def _get_quibs_connected_up_down_or_all(focal_quib: Quib,
                                        direction: Direction,
                                        depth: int,
                                        limit_to_named_quibs: bool,
                                        quibs: Optional[Set[Quib]] = None) -> Set[Quib]:
    assert direction is not Direction.BOTH
    quibs = set() if quibs is None else quibs

    def _get_quibs_recursively(quib: Quib, depth_: int):
        nonlocal quibs
        if quib in quibs:
            return
        quibs.add(quib)
        if depth_ > 0:
            for neighbour_quib in _get_neighbour_quibs(quib, direction, limit_to_named_quibs):
                _get_quibs_recursively(neighbour_quib, depth_ - 1)

    _get_quibs_recursively(focal_quib, depth)
    return quibs


@dataclasses.dataclass
class QuibNetwork:
    focal_quib: Quib
    direction: Union[str, Direction] = Direction.BOTH
    depth: int = infinity
    reverse_depth: int = 0
    limit_to_named_quibs: bool = True
    _quibs: Optional[Set[Quib]] = None
    _links: Optional[Set[Tuple[Quib, Quib]]] = None

    def __post_init__(self):
        self.depth = infinity if self.depth is None else self.depth
        self.reverse_depth = infinity if self.reverse_depth is None else self.reverse_depth
        self.direction = get_enum_by_str(Direction, self.direction, allow_none=True) or Direction.BOTH

    def _get_quibs_connected_to_focal_quib_up_or_down_then_reverse(self, direction: Direction) -> Set[Quib]:
        assert direction in [Direction.DOWNSTREAM, Direction.UPSTREAM]
        quibs = _get_quibs_connected_up_down_or_all(self.focal_quib,
                                                    direction,
                                                    self.depth,
                                                    self.limit_to_named_quibs)

        if self.reverse_depth > 0:
            for quib in set(quibs):  # make a copy
                if quib is not self.focal_quib:
                    add_quibs = _get_quibs_connected_up_down_or_all(
                        quib,
                        reverse_direction(direction),
                        self.reverse_depth,
                        self.limit_to_named_quibs,
                        quibs - {quib})
                    quibs |= add_quibs
        return quibs

    def _get_quibs_connected_to_focal_quib(self) -> Set[Quib]:
        if self.direction is Direction.BOTH:
            return self._get_quibs_connected_to_focal_quib_up_or_down_then_reverse(Direction.UPSTREAM) \
                   | self._get_quibs_connected_to_focal_quib_up_or_down_then_reverse(Direction.DOWNSTREAM)
        elif self.direction is Direction.ALL:
            return _get_quibs_connected_up_down_or_all(self.focal_quib,
                                                       self.direction,
                                                       self.depth,
                                                       self.limit_to_named_quibs)

        return self._get_quibs_connected_to_focal_quib_up_or_down_then_reverse(self.direction)

    def _get_connecting_links(self) -> Set[Tuple[Quib, Quib]]:
        quibs = self.quibs
        links = set()
        for i, quib in enumerate(quibs):
            parents = quib.get_parents(limit_to_named_quibs=self.limit_to_named_quibs)
            data_parents = quib.get_parents(limit_to_named_quibs=self.limit_to_named_quibs, is_data_source=True)
            parents &= quibs
            links |= {(parent, quib, parent in data_parents) for parent in parents}
        return links

    @property
    def quibs(self) -> Set[Quib]:
        if self._quibs is None:
            self._quibs = self._get_quibs_connected_to_focal_quib()
        return self._quibs

    @property
    def links(self) -> Set[Tuple[Quib, Quib]]:
        if self._links is None:
            self._links = self._get_connecting_links()
        return self._links

    def create_quib_node(self, quib):
        node = QuibNode.from_quib(quib)
        if quib is self.focal_quib:
            node.classes += ' focal'
        return node

    def get_legend_widget(self):
        labels_classes = (
            ('input', 'iquib'),
            ('function', ''),
            ('focal', 'focal'),
            ('overridden', 'overridden null'),
            ('graphics', 'graphics'),
        )
        w = ipycytoscape.CytoscapeWidget()
        first_row = 50
        row_space = 50
        x_location1 = 35
        x_location2 = 100
        for index, (label, class_) in enumerate(labels_classes):
            node = QuibNode(index, label, '', class_, (x_location1, first_row + index * row_space))
            w.graph.add_node(node)

        is_data_label = (
            (False, 'Parameter'),
            (True, 'Data'),
        )
        for row, (is_data, label) in enumerate(is_data_label):
            id_left, id_right = 10 + row, 12 + row
            w.graph.add_node(QuibNode(id_left, label, '', 'hidden', (x_location1, first_row + (5 + row) * row_space)))
            w.graph.add_node(QuibNode(id_right, '', '', 'hidden', (x_location2, first_row + (5 + row) * row_space)))
            w.graph.add_edge(QuibEdge(id_left, id_right, is_data))
        w.set_style(NETWORK_STYLE)
        w.zooming_enabled = False
        w.user_zooming_enabled = False
        w.panning_enabled = False
        w.user_panning_enabled = False
        w.set_layout(name='preset')
        return w

    def get_network_widget(self) -> ipycytoscape.CytoscapeWidget:
        w = ipycytoscape.CytoscapeWidget()
        w.graph.add_nodes([self.create_quib_node(quib) for quib in self.quibs])
        w.graph.add_edges([QuibEdge(id(source), id(target), is_data)
                           for source, target, is_data in self.links],
                          directed=True)
        w.set_style(NETWORK_STYLE)
        w.set_layout(**NETWORK_LAYOUT)
        return w

    def get_network_widget_with_legend(self) -> ipywidgets.Box:
        legend_widget = self.get_legend_widget()
        network_widget = self.get_network_widget()
        box = ipywidgets.Box()
        box.children = [legend_widget, network_widget]

        return box

@validate_user_input(focal_quib=Quib,
                     direction=(type(None), str, Direction),
                     depth=(type(None), int),
                     reverse_depth=(type(None), int),
                     limit_to_named_quibs=bool)
def dependency_graph(focal_quib: Quib,
                     direction: Union[None, str, Direction] = None,
                     depth: Optional[int] = None,
                     reverse_depth: Optional[int] = 0,
                     limit_to_named_quibs: bool = True) -> ipywidgets.Box:
    """
    Draw a network of quibs

    Trace a focal quib upstream, downstream or both and draw a network of dependent quibs.

    .. image:: /images/network_tracing.png

    Parameters
    ----------
    focal_quib : Quib
        The focal quib around which to extend the network.

    direction : Direction or {'upstream', 'downstream', 'both', 'all'}

        Determines how to expand the network from the focal_quib

        * ``'upstream'`` : expand upstream to quibs that affect the focal quib.

        * ``'downstream'`` : expand downstream to quibs affected by the focal quib.

        *  ``'both'`` : interdependently expand both upstream and downstream (default)

        * ``'all'`` : expand in both direction simultaneously, returning all the quibs connected to the focal quib.

        See example in the figure above.

    depth : int or None
        The number of steps of network extension. `None` for infinity (default).

    reverse_depth : int or None
        The number of steps to extend network in the reverse direction.

        ``None`` for infinity; ``0`` do not reverse (default).

        When ``direction='downstream'``, setting ``reverse_depth > 0`` is helpful to understand what
        other parameters affect what the focal quib is affecting.

        When ``direction='upstream'``, setting ``reverse_depth > 0`` is helpful to understand what
        other results are affected by the parameters that affect the focal quib.

    limit_to_named_quibs : True or False, default: True
        Indicates whether to limit to named quibs or also include unnamed quibs.
        Unnamed quibs are quibs whose ``assigned_name`` is `None`, typically representing intermediate calculations.

    Returns
    -------
    ipycytoscape.CytoscapeWidget
        An ipycytoscape widget that represents the quib network.

    See Also
    --------
    Direction, Quib.get_parents, Quib.get_children, Quib.get_ancestors, Quib.get_descendants
    """

    return QuibNetwork(focal_quib=focal_quib,
                       direction=direction,
                       depth=depth,
                       reverse_depth=reverse_depth,
                       limit_to_named_quibs=limit_to_named_quibs).get_network_widget_with_legend()
