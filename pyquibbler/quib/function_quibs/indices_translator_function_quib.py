import numpy as np
from abc import abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from typing import Set, Optional, Dict, Callable, List, Any, Union

from pyquibbler.env import DEBUG
from pyquibbler.quib.assignment.inverse_assignment.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.function_quibs import FunctionQuib
from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.utils import iter_objects_of_type_in_object_shallowly


@dataclass
class SupportedFunction:
    # None means that all args are data sources
    data_source_indices: Union[Set[int], slice]

    def get_data_source_args(self, args: List[Any]) -> List[Any]:
        if isinstance(self.data_source_indices, slice):
            return args[self.data_source_indices]
        return [args[i] for i in self.data_source_indices]


class IndicesTranslatorFunctionQuib(FunctionQuib):
    SUPPORTED_FUNCTIONS: Optional[Dict[Callable, SupportedFunction]]

    def _get_source_shaped_bool_mask(self, invalidator_quib: Quib, indices: Any) -> Any:
        """
        Return a boolean mask in the shape of the given invalidator_quib, in which only the given indices are set to
        True.
        """
        return create_empty_array_with_values_at_indices(
            value=True,
            empty_value=False,
            indices=indices,
            shape=invalidator_quib.get_shape().get_value()
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
            data_source_args = supported_function.get_data_source_args(self._get_arg_values_by_position())
            return set(iter_objects_of_type_in_object_shallowly(Quib, data_source_args))
        return self.parents

    def _is_quib_a_data_source(self, quib: Quib):
        return quib in self.get_data_source_quibs()

    @abstractmethod
    def _forward_translate_indices_to_bool_mask(self, invalidator_quib: Quib, indices: Any) -> Any:
        pass

    def _forward_translate_invalidation_path(self, invalidator_quib: Quib,
                                             path: List[PathComponent]) -> Optional[List[PathComponent]]:
        working_component, *rest_of_path = path
        bool_mask_in_output_array = self._forward_translate_indices_to_bool_mask(invalidator_quib,
                                                                                 working_component.component)
        if DEBUG:
            # Make sure the bool mask fits our result shape
            if issubclass(self.get_type(), np.ndarray):
                try:
                    self.get_value()[bool_mask_in_output_array]
                except IndexError as e:
                    raise IndexError(f'Value: {self.get_value()}\nMask: {bool_mask_in_output_array}'
                                     f'\nShapes: {self.get_shape().get_value()}, {bool_mask_in_output_array.shape}') from e
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
