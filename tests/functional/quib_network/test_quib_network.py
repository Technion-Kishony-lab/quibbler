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

