from dataclasses import dataclass

import numpy as np

from pyquibbler.path import Path


@dataclass(frozen=True)
class FrozenSlice:
    start: int
    step: int
    stop: int


def _hash_component_value(inner_component):
    if isinstance(inner_component, list):
        return tuple([_hash_component_value(x) for x in inner_component])
    elif isinstance(inner_component, np.ndarray):
        return inner_component.tobytes()
    elif isinstance(inner_component, slice):
        return FrozenSlice(inner_component.start, inner_component.step, inner_component.stop)
    elif isinstance(inner_component, tuple):
        return tuple([_hash_component_value(x) for x in inner_component])
    return inner_component


def get_hashable_path(path: Path):
    """
    Get a hashable path (list of pathcomponents)- this supports known indexing methods
    """
    return tuple([
        _hash_component_value(p.component) for p in path
    ])
