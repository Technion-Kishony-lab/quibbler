import numpy as np
from abc import abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from typing import Set, Optional, Dict, Callable, List, Any, Union

from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.function_quibs.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.function_quibs import FunctionQuib
from pyquibbler.quib.assignment import PathComponent, QuibWithAssignment
from pyquibbler.quib.utils import iter_objects_of_type_in_object_shallowly

Args = List[Any]
Kwargs = Dict[str, Any]


@dataclass
class SupportedFunction:
    data_source_indices: Union[Set[Union[int, str]],
                               Callable[[Args, Kwargs], List[Any]]]

    def get_data_source_args(self, args: Args, kwargs: Kwargs) -> List[Any]:
        if callable(self.data_source_indices):
            return self.data_source_indices(args, kwargs)
        return [args[i] if isinstance(i, int) else kwargs[i] for i in self.data_source_indices]


class IndicesTranslatorFunctionQuib(FunctionQuib):
    SUPPORTED_FUNCTIONS: Optional[Dict[Callable, SupportedFunction]]

    def _get_source_shaped_bool_mask(self, invalidator_quib: Quib, indices: Any) -> Any:
        """
        Return a boolean mask in the shape of the given quib, in which only the given indices are set to
        True.
        """
        return create_empty_array_with_values_at_indices(
            value=True,
            empty_value=False,
            indices=indices,
            shape=invalidator_quib.get_shape().get_value()
        )

    def _get_representative_result(self, working_component, value):
        return create_empty_array_with_values_at_indices(
                self.get_shape().get_value(),
                indices=working_component,
                value=value,
            )

    @classmethod
    def create_wrapper(cls, func: Callable):
        if cls.SUPPORTED_FUNCTIONS is not None:
            assert func in cls.SUPPORTED_FUNCTIONS, \
                f'Tried to create a wrapper for function {func} which is not supported'
        return super().create_wrapper(func)

    @lru_cache()
    def get_data_source_quibs(self) -> Set:
        if self.SUPPORTED_FUNCTIONS is not None:
            supported_function = self.SUPPORTED_FUNCTIONS[self._func]
            data_source_args = supported_function.get_data_source_args(self.args, self.kwargs)
            return set(iter_objects_of_type_in_object_shallowly(Quib, data_source_args))
        return self.parents

    def _is_quib_a_data_source(self, quib: Quib):
        return quib in self.get_data_source_quibs()

    @abstractmethod
    def _forward_translate_indices_to_bool_mask(self, quib: Quib, indices: Any) -> Any:
        pass

    def _get_quibs_to_paths_in_result(self, filtered_path_in_result):
        return {}

    def _get_quibs_to_relevant_result_values(self, assignment: Assignment):
        return {}

    def _forward_translate_invalidation_path(self, quib: Quib,
                                             path: List[PathComponent]) -> Optional[List[PathComponent]]:
        working_component, *rest_of_path = path
        bool_mask_in_output_array = self._forward_translate_indices_to_bool_mask(quib,
                                                                                 working_component.component)

        if np.any(bool_mask_in_output_array):
            # If there exist both True's and False's in the boolean mask,
            # this function's quib result must be an ndarray- if it were a single item (say a PyObj, int, dict, list)
            # we'd expect it to be completely True (as it is ONE single object). If it is not a single item, it is by
            # definitely an ndarray
            assert issubclass(self.get_type(), np.ndarray) or np.all(bool_mask_in_output_array)
            assert issubclass(self.get_type(), np.ndarray) or isinstance(bool_mask_in_output_array, np.bool_)

            if not np.all(bool_mask_in_output_array) and issubclass(self.get_type(), np.ndarray):
                return [PathComponent(self.get_type(), bool_mask_in_output_array), *rest_of_path]
            return rest_of_path
        return None

    def _get_path_for_children_invalidation(self, invalidator_quib: Quib,
                                            path: List[PathComponent]) -> Optional[List[PathComponent]]:
        if not self._is_quib_a_data_source(invalidator_quib):
            return []
        return self._forward_translate_invalidation_path(invalidator_quib, path)

    def _get_translated_argument_quib_path_at_path(self, quib: Quib, arg_index: int, path: List[PathComponent]):
        if path is None:
            return None
        quibs_to_paths = self._get_quibs_to_paths_in_result(path)
        return quibs_to_paths.get(quib)

    def get_inversions_for_assignment(self, assignment: Assignment):
        components_at_end = assignment.path[1:]
        current_components = assignment.path[0:1]
        if len(assignment.path) > 0 and assignment.path[0].references_field_in_field_array():
            components_at_end = [assignment.path[0], *components_at_end]
            current_components = []

        quibs_to_paths = self._get_quibs_to_paths_in_result(current_components)
        quibs_to_values = self._get_quibs_to_relevant_result_values(assignment)

        return [
            QuibWithAssignment(
                quib=quib,
                assignment=Assignment(
                    path=[*path, *components_at_end],
                    value=quibs_to_values[quib]
                )
            )
            for quib, path in quibs_to_paths.items()
            if quib in quibs_to_values
        ]
