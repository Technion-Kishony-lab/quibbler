import pytest
from dataclasses import dataclass, field

from typing import Set
from unittest.mock import Mock

from pyquibbler import iquib
from pyquibbler.optional_packages.emulate_missing_packages import EMULATE_MISSING_PACKAGES


# @pytest.fixture(autouse=True, scope='module')
# def setup_no_missing_packages():
#     with EMULATE_MISSING_PACKAGES.temporary_set([]):
#         yield


@dataclass
class MockQuib:
    pretty_repr: str
    children: Set['MockQuib'] = field(default_factory=set)
    parents: Set['MockQuib'] = field(default_factory=set)
    is_iquib: bool = False
    is_graphics: bool = False

    def __hash__(self):
        return id(self)

    def get_override_list(self):
        return []

    def get_children(self, *args, **kwargs):
        return self.children

    def get_parents(self, *args, **kwargs):
        return self.parents

    def display_properties(self, *args, **kwargs):
        return Mock()

    def __repr__(self):
        return self.pretty_repr


def connect_quibs(parent: MockQuib, child: MockQuib):
    parent.children.add(child)
    child.parents.add(parent)


@pytest.fixture()
def nodes():
    """
              4
               \
    0  -  1   -  2  -  5  -  6
           \      \
            3      7

    ---- downstream --->

    """

    nodes = [MockQuib(str(num)) for num in range(8)]

    links = (
        (0, 1),
        (1, 3),
        (1, 2),
        (4, 2),
        (2, 7),
        (2, 5),
        (5, 6),
    )

    for num_parent, num_child in links:
        connect_quibs(nodes[num_parent], nodes[num_child])

    return nodes


@pytest.mark.parametrize(['origin_num', 'direction', 'depth', 'reverse_depth', 'expected_node_nums'], [
    (2, 'downstream', None, 0, [2, 5, 6, 7]),
    (2, 'upstream', None, 0, [0, 1, 2, 4]),
    (2, 'both', None, 0, [0, 1, 2, 4, 5, 6, 7]),
    (2, 'all', None, 0, [0, 1, 2, 3, 4, 5, 6, 7]),
    (0, 'downstream', 0, 0, [0]),
    (0, 'downstream', 2, 0, [0, 1, 2, 3]),
    (1, 'downstream', 1, 0, [1, 2, 3]),
    (1, 'downstream', 1, 1, [1, 2, 3, 4]),
    (1, 'both', 1, 1, [0, 1, 2, 3, 4]),
])
def test_network_gets_correct_quibs_and_links(nodes, origin_num, direction, depth, reverse_depth, expected_node_nums):
    from pyquibbler.quib_network.quib_network import QuibNetwork
    network = QuibNetwork(focal_quib=nodes[origin_num], direction=direction, depth=depth, reverse_depth=reverse_depth)
    expected_nodes = {nodes[num] for num in expected_node_nums}
    expected_links = set()
    for node in expected_nodes:
        for child in node.get_children():
            if child in expected_nodes:
                expected_links.add((node, child, True))
    print(expected_nodes)
    assert network.quibs == expected_nodes
    assert network.links == expected_links
    network.get_network_widget()


def test_network_widget_is_created():
    from pyquibbler.quib_network.quib_network import dependency_graph
    a = iquib(1)
    b = a + 2
    w = dependency_graph(a, bypass_intermediate_quibs=False)
    assert {w.children[1].graph.nodes[0].data['id'], w.children[1].graph.nodes[1].data['id']} == {id(a), id(b)}
