from typing import Any, Type, Union, Tuple

import numpy as np

from pyquibbler.path import Path


def working_component(path: Path):
    """
    Get the first working component value you can from the path- this will always be entirely "squashed", so you will
    get a component that expresses everything possible before needing to go another step "deeper" in

    If no component is found (path is empty), the path expresses getting "everything"- so we give a true value
    """
    return path[0].component if len(path) > 0 else True


def nd_working_component(path: Path):
    return path[0].component if len(path) > 0 and path[0].indexed_cls == np.ndarray else True


def working_component_of_type(path: Path, type_: Union[Type, Tuple[Type, ...]], option_if_not_found: Any):
    return path[0].component if len(path) > 0 and issubclass(path[0].indexed_cls, type_) else option_if_not_found


def path_beyond_working_component(path: Path):
    return path[1:]


def path_beyond_nd_working_component(path: Path):
    if len(path) == 0:
        return []

    first_component = path[0]
    if first_component.indexed_cls == np.ndarray:
        return path[1:]
    return path
