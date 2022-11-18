from dataclasses import dataclass

from pyquibbler.optional_packages.exceptions import MissingPackagesForFunctionException
from typing import Union, Set, Tuple, Optional
from pyquibbler import Quib
from pyquibbler.utilities.input_validation_utils import validate_user_input, get_enum_by_str

from .network_properties import NETWORK_STYLE, NETWORK_LAYOUT
from .types import Direction, reverse_direction


# Verify that we have the required packages installed
# (These are specific packages and hence we do not specify them as official requirements for pyquibbler)
missing_packages = []
try:
    from pyquibbler.optional_packages.get_ipywidgets import ipywidgets  # noqa
except ImportError:
    missing_packages.append('ipywidgets')

try:
    from pyquibbler.optional_packages.get_ipycytoscape import ipycytoscape  # noqa
except ImportError:
    missing_packages.append('ipycytoscape')

if missing_packages:
    raise MissingPackagesForFunctionException('dependency_graph', missing_packages)


infinity = float('inf')


def get_quib_class(quib: Quib) -> str:
    """
    Return a string containing the classes of the quib: 'iquib', 'graphics', 'overridden'.
    """
    classes = ''
    if quib.is_iquib:
        classes += ' iquib'
    if quib.is_graphics:
        classes += ' graphics'
    if quib.get_override_list() is not None and len(quib.get_override_list()) > 0:
        classes += ' overridden'
    return classes


class QuibNode(ipycytoscape.Node):
    """
    A node in a quib network.
    """
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
        tooltip = quib.display_properties().get_html_repr()
        return cls(id(quib), quib.pretty_repr, tooltip, classes=get_quib_class(quib))


class QuibEdge(ipycytoscape.Edge):
    """
    An edge between a source and a target quib nodes.
    """
    def __init__(self, source_id: int, target_id: int, is_data: bool):
        super().__init__()
        self.data['source'] = source_id
        self.data['target'] = target_id
        self.classes += " directed "
        if is_data:
            self.classes += " data_source "


def _get_neighbour_quibs(quib: Quib, direction: Direction, bypass_intermediate_quibs: bool) -> Set[Quib]:
    quibs = set()
    if direction is not Direction.UPSTREAM:
        quibs |= quib.get_children(bypass_intermediate_quibs=bypass_intermediate_quibs)
    if direction is not Direction.DOWNSTREAM:
        quibs |= quib.get_parents(bypass_intermediate_quibs=bypass_intermediate_quibs)
    return quibs


def _get_quibs_connected_up_down_or_all(focal_quib: Quib,
                                        direction: Direction,
                                        depth: int,
                                        bypass_intermediate_quibs: bool,
                                        quibs: Optional[Set[Quib]] = None) -> Set[Quib]:
    """
    Starting from a focal quib, recursively explore the quib network upstream, downstream or in all directions.
    """
    assert direction is not Direction.BOTH
    quibs = set() if quibs is None else quibs

    def _get_quibs_recursively(quib: Quib, depth_: int):
        nonlocal quibs
        if quib in quibs:
            return
        quibs.add(quib)
        if depth_ > 0:
            for neighbour_quib in _get_neighbour_quibs(quib, direction, bypass_intermediate_quibs):
                _get_quibs_recursively(neighbour_quib, depth_ - 1)

    _get_quibs_recursively(focal_quib, depth)
    return quibs


@dataclass
class QuibNetwork:
    """
    A network of quibs extending from a focal quib.
    """
    focal_quib: Quib
    direction: Union[str, Direction] = Direction.BOTH
    depth: int = infinity
    reverse_depth: int = 0
    bypass_intermediate_quibs: bool = True
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
                                                    self.bypass_intermediate_quibs)

        if self.reverse_depth > 0:
            for quib in set(quibs):  # make a copy
                if quib is not self.focal_quib:
                    add_quibs = _get_quibs_connected_up_down_or_all(
                        quib,
                        reverse_direction(direction),
                        self.reverse_depth,
                        self.bypass_intermediate_quibs,
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
                                                       self.bypass_intermediate_quibs)

        return self._get_quibs_connected_to_focal_quib_up_or_down_then_reverse(self.direction)

    def _get_connecting_links(self) -> Set[Tuple[Quib, Quib]]:
        quibs = self.quibs
        links = set()
        for i, quib in enumerate(quibs):
            parents = quib.get_parents(bypass_intermediate_quibs=self.bypass_intermediate_quibs)
            data_parents = quib.get_parents(bypass_intermediate_quibs=self.bypass_intermediate_quibs,
                                            is_data_source=True)
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
        w.box_selection_enabled = False
        w.layout.width = '25%'
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
                     bypass_intermediate_quibs=bool)
def dependency_graph(focal_quib: Quib,
                     direction: Union[None, str, Direction] = None,
                     depth: Optional[int] = None,
                     reverse_depth: Optional[int] = 0,
                     bypass_intermediate_quibs: bool = True) -> ipywidgets.Box:
    """
    Draw a network of quibs

    Trace a focal quib upstream, downstream or in both directions and draw a network of dependent quibs.

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

    bypass_intermediate_quibs : bool, default: True
        Intermediate quibs are defined as unnamed and non-graphics
        quibs (``assigned_name=None`` and ``is_graphics=False``), typically representing
        intermediate calculations.

    Returns
    -------
    ipywidgets.Box
        An ipycytoscape.Box containing the legend and the quib network widgets.

    See Also
    --------
    Direction,
    ~pyquibbler.Quib.get_parents,
    ~pyquibbler.Quib.get_children,
    ~pyquibbler.Quib.get_ancestors,
    ~pyquibbler.Quib.get_descendants
    """

    return QuibNetwork(focal_quib=focal_quib,
                       direction=direction,
                       depth=depth,
                       reverse_depth=reverse_depth,
                       bypass_intermediate_quibs=bypass_intermediate_quibs).get_network_widget_with_legend()
