import dataclasses
from typing import Set

import pytest
from pyquibbler.quib_network.quib_network import QuibNetwork


@dataclasses.dataclass
class MockQuib:
    pretty_repr: str
    is_iquib: bool = True
    children: Set['MockQuib'] = dataclasses.field(default_factory=set)
    parents: Set['MockQuib'] = dataclasses.field(default_factory=set)

    def __hash__(self):
        return id(self)

    def get_children(self, *args, **kwargs):
        return self.children

    def get_parents(self, *args, **kwargs):
        return self.parents

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


@pytest.mark.parametrize(['origin_num', 'direction', 'depth', 'expected_nodes_num'], [
    (2, 'downstream', None, [2, 5, 6, 7]),
    (2, 'upstream', None, [0, 1, 2, 4]),
    (2, 'both', None, [0, 1, 2, 4, 5, 6, 7]),
    (2, 'all', None, [0, 1, 2, 3, 4, 5, 6, 7]),
])
def test_network_gets_correct_quibs_and_links(nodes, origin_num, direction, depth, expected_nodes_num):
    network = QuibNetwork(origin_quib=nodes[origin_num], direction=direction, depth=10)
    expected_nodes = {nodes[num] for num in expected_nodes_num}
    expected_links = set()
    for node in expected_nodes:
        for child in node.get_children():
            if child in expected_nodes:
                expected_links.add((node, child))
    print(expected_nodes)
    assert network.quibs == expected_nodes
    assert network.links == expected_links
    network.get_network_widget()
