import numpy as np
from contextlib import contextmanager
from copy import deepcopy
from typing import Any, Optional, List

from pyquibbler import CacheBehavior, Assignment
from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.overrider import get_sub_data_from_object_in_path, deep_assign_data_with_paths
from pyquibbler.quib.input_quib import InputQuib

from .utils import PathBuilder


class MockQuib(InputQuib):
    def __init__(self, value: Any):
        super().__init__(value)
        self._valid_paths = []

    def get_value_valid_at_path(self, path: Optional[List[PathComponent]]) -> Any:
        if path is not None:
            self._valid_paths.append(path)
        return super().get_value_valid_at_path(path)

    @contextmanager
    def collect_valid_paths(self):
        self._valid_paths.clear()
        yield self._valid_paths
        self._valid_paths = []


def get_indices_at_path(shape, path):
    assert len(path) <= 1
    all_indices = np.moveaxis(np.indices(shape), 0, -1)
    return get_sub_data_from_object_in_path(all_indices, path).reshape(-1, len(shape))


def is_field_index(index):
    return isinstance(index, str) or \
           (np.iterable(index) and all(isinstance(sub_index, str) for sub_index in index))


def breakdown_component(shape, path_component: PathComponent):
    component = path_component.component
    field_index = is_field_index(component)
    components = component
    if isinstance(component, str):
        components = [component]
    if not field_index:
        components = get_indices_at_path(shape, [path_component])
    return components, field_index


def breakdown_path(data: Any, path: List[PathComponent]):
    """
    Given a path pointing to a slice of data inside a quib,
    return paths to all cells in the slice.
    """
    assert isinstance(data, np.ndarray)
    is_field_array = data.dtype.names is not None
    if is_field_array:
        assert 1 <= len(path) <= 2
        first_components, first_is_field = breakdown_component(data.shape, path[0])
        if len(path) == 2:
            second_components, second_is_field = breakdown_component(data.shape, path[1])
            assert second_is_field != first_is_field
        else:
            second_components = get_indices_at_path(data.shape, []) if first_is_field else data.dtype.names
        return [[PathComponent(np.ndarray, tuple(first_component)), PathComponent(np.ndarray, second_component)]
                for first_component in first_components
                for second_component in second_components]
    return [[PathComponent(np.ndarray, tuple(index))] for index in get_indices_at_path(data.shape, path)]


def equals_at_path(data1, data2, path):
    return np.array_equal(get_sub_data_from_object_in_path(data1, path),
                          get_sub_data_from_object_in_path(data2, path))


def check_get_value_valid_at_path(func, data, path_to_get_value_at):
    """
    To make sure reverse path translation was done correctly, we need to verify two things:
    1. No other changed path in the input data can change the path in the result
    2. Any change in the requested input data will change the path in the result
    """
    input_quib = MockQuib(data)
    result_quib = func(input_quib)
    result_quib.set_cache_behavior(CacheBehavior.OFF)

    result = result_quib.get_value()

    with input_quib.collect_valid_paths() as requested_paths:
        result_quib.get_value_valid_at_path(path_to_get_value_at)

    faulty_sub_paths = []
    for path in requested_paths:
        for sub_path in breakdown_path(data, path):
            changed_data = deep_assign_data_with_paths(deepcopy(data), sub_path, 999)
            result_with_change = func(changed_data)
            if equals_at_path(result_with_change, result, path_to_get_value_at):
                faulty_sub_paths.append(sub_path)
    assert not faulty_sub_paths, faulty_sub_paths

    input_quib.assign(Assignment(999, PathBuilder(input_quib)[...].path))
    for path in requested_paths:
        value = get_sub_data_from_object_in_path(data, path)
        input_quib.assign(Assignment(value, path))
    result_with_everything_else_changed = result_quib.get_value()
    assert equals_at_path(result_with_everything_else_changed, result, path_to_get_value_at)
