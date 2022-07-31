from typing import Any, Type, Union, Tuple

import numpy as np

from pyquibbler.path import Path


def nd_working_component(path: Path):
    return path[0].component if len(path) > 0 and path[0].indexed_cls == np.ndarray else True


def path_beyond_working_component(path: Path):
    return path[1:]


def path_beyond_nd_working_component(path: Path):
    if len(path) == 0:
        return []

    first_component = path[0]
    if first_component.indexed_cls == np.ndarray:
        return path[1:]
    return path

