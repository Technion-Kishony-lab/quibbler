from __future__ import annotations
from typing import Dict, Any, Set, TYPE_CHECKING, Optional, Tuple, Type

import numpy as np

from pyquibbler.quib import PathComponent
from pyquibbler.quib.assignment import Path
from pyquibbler.quib.function_quibs.utils import unbroadcast_bool_mask, create_empty_array_with_values_at_indices
from pyquibbler.refactor.quib.function_runners.vectorize.utils import iter_arg_ids_and_values
from pyquibbler.refactor.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.refactor.translation.types import Source

if TYPE_CHECKING:
    from pyquibbler.refactor.quib.function_runners.vectorize.vectorize_metadata import ArgId


def _get_arg_ids_for_source(source: Source, args, kwargs) -> Set[ArgId]:
    """
    Given a parent quib, get all arg_ids it is given with.
    For example, in the call `f(q, x=q)`, `_get_arg_ids_for_quib(q)` will return `{0, 'x'}`
    """
    return {arg_id for arg_id, arg in iter_arg_ids_and_values(args[1:], kwargs) if source is arg}


class VectorizeBackwardsPathTranslator(BackwardsPathTranslator):

    def __init__(self, func_call, shape: Optional[Tuple[int, ...]], type_: Optional[Type], path,
                 vectorize_metadata):
        super().__init__(func_call, shape, type_, path)
        self._vectorize_metadata = vectorize_metadata

    def _backwards_translate_indices_to_bool_mask(self, source: Source, indices: Any) -> Any:
        """
        Translate indices in result backwards to indices in a data source quib, by calling any on result
        core dimensions and un-broadcasting the loop dimensions into the argument loop dimension.
        """
        vectorize_metadata = self._vectorize_metadata
        quib_arg_id = _get_arg_ids_for_source(source, self._func_call.args, self._func_call.kwargs).pop()
        quib_loop_shape = vectorize_metadata.args_metadata[quib_arg_id].loop_shape
        result_bool_mask = create_empty_array_with_values_at_indices(self._shape, indices=indices, value=True,
                                                                     empty_value=False)
        result_core_axes = vectorize_metadata.result_core_axes
        # Reduce result core dimensions
        reduced_bool_mask = np.any(result_bool_mask, axis=result_core_axes)
        return unbroadcast_bool_mask(reduced_bool_mask, quib_loop_shape)

    def _get_source_path_in_source(self, source: Source, filtered_path_in_result: Path):
        """
        Given a path in the result, return the path in the given quib on which the result path depends.
        """
        if len(filtered_path_in_result) == 0 or filtered_path_in_result[0].indexed_cls is tuple:
            return []
        working_component, *rest_of_path = filtered_path_in_result
        indices_in_data_source = self._backwards_translate_indices_to_bool_mask(source, working_component.component)
        return [PathComponent(self._type, indices_in_data_source)]

    def translate_in_order(self) -> Dict[Source, Path]:
        return {source: self._get_source_path_in_source(source, self._path)
                for source in self.get_data_sources()}

