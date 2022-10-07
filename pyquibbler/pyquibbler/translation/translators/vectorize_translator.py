from __future__ import annotations
from typing import Dict, Any, Set, Optional, Type

import numpy as np

from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices, unbroadcast_bool_mask, Shape, \
    create_bool_mask_with_true_at_path
from pyquibbler.path import PathComponent
from pyquibbler.path.path_component import Path, Paths
from pyquibbler.quib.func_calling.func_calls.vectorize.utils import get_core_axes
from pyquibbler.function_definitions.types import iter_arg_ids_and_values
from pyquibbler.function_definitions import FuncCall, SourceLocation

from ..exceptions import FailedToTranslateException
from ..base_translators import BackwardsPathTranslator, ForwardsPathTranslator
from ..types import Source

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.func_calling.func_calls.vectorize.vectorize_metadata import ArgId


def _get_arg_ids_for_source(source: Source, args, kwargs) -> Set[ArgId]:
    """
    Given a parent quib, get all arg_ids it is given with.
    For example, in the call `f(q, x=q)`, `_get_arg_ids_for_quib(q)` will return `{0, 'x'}`
    """
    return {arg_id for arg_id, arg in iter_arg_ids_and_values(args[1:], kwargs) if source is arg}


class VectorizeBackwardsPathTranslator(BackwardsPathTranslator):

    SHOULD_ATTEMPT_WITHOUT_SHAPE_AND_TYPE = False

    def __init__(self, func_call, shape: Optional[Shape], type_: Optional[Type], path,
                 vectorize_metadata=None):
        super().__init__(func_call, shape, type_, path)
        self._vectorize_metadata = vectorize_metadata

    def _backwards_translate_indices_to_bool_mask(self, source: Source, indices: Any) -> Any:
        """
        Translate indices in result backwards to indices in a data source, by calling any on result
        core dimensions and un-broadcasting the loop dimensions into the argument loop dimension.
        """
        vectorize_metadata = self._vectorize_metadata
        quib_arg_id = _get_arg_ids_for_source(source, self._func_call.args, self._func_call.kwargs).pop()
        quib_loop_shape = vectorize_metadata.args_metadata[quib_arg_id].loop_shape
        result_bool_mask = create_bool_mask_with_true_at_indices(self._shape, indices)
        result_core_axes = vectorize_metadata.result_core_axes
        # Reduce result core dimensions
        reduced_bool_mask = np.any(result_bool_mask, axis=result_core_axes)
        return unbroadcast_bool_mask(reduced_bool_mask, quib_loop_shape)

    def _get_source_path_in_source(self, source: Source, filtered_path_in_result: Path) -> Path:
        """
        Given a path in the result, return the path in the given quib on which the result path depends.
        """
        if len(filtered_path_in_result) == 0:
            return []

        # TODO: if the result is a tuple, we should better translate the rest of the path, path[1:]
        if self._vectorize_metadata.is_result_a_tuple:
            return []

        if self._shape is None:
            raise FailedToTranslateException()

        working_component, *rest_of_path = filtered_path_in_result
        indices_in_data_source = self._backwards_translate_indices_to_bool_mask(source, working_component.component)
        return [PathComponent(indices_in_data_source)]

    def backwards_translate(self) -> Dict[Source, Path]:
        return {source: self._get_source_path_in_source(source, self._path)
                for source in self._func_call.get_data_sources()}


class VectorizeForwardsPathTranslator(ForwardsPathTranslator):

    def __init__(self,
                 func_call: Type[FuncCall],
                 source: Source,
                 source_location: SourceLocation,
                 path: Path,
                 shape: Optional[Shape],
                 type_: Optional[Type],
                 vectorize_metadata):
        super().__init__(func_call, source, source_location, path, shape, type_)
        self._vectorize_metadata = vectorize_metadata

    def forward_translate_initial_path_to_bool_mask(self, path: Path):
        source_bool_mask = create_bool_mask_with_true_at_path(np.shape(self._source.value), path)
        core_ndim = max(self._vectorize_metadata.args_metadata[arg_id].core_ndim
                        for arg_id in
                        _get_arg_ids_for_source(self._source, self._func_call.args, self._func_call.kwargs))
        source_bool_mask = np.any(source_bool_mask, axis=get_core_axes(core_ndim))
        return np.broadcast_to(source_bool_mask, self._vectorize_metadata.result_loop_shape)

    def forward_translate(self) -> Paths:
        path = self._path
        if len(path) == 0:
            return [[]]

        working_path = path[:1]
        rest_of_path = path[1:]
        bool_mask_in_output_array = \
            self.forward_translate_initial_path_to_bool_mask(working_path)
        if not np.any(bool_mask_in_output_array):
            return []
        starting_path = [PathComponent(bool_mask_in_output_array), *rest_of_path]

        if self._vectorize_metadata.is_result_a_tuple:
            return [[PathComponent(i), *starting_path] for i in range(self._vectorize_metadata.tuple_length)]
        else:
            return [starting_path]
