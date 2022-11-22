from __future__ import annotations
from typing import Optional, Type, Tuple

import numpy as np
from numpy.typing import NDArray

from pyquibbler.utilities.general_utils import unbroadcast_or_broadcast_bool_mask, Shape
from pyquibbler.path import PathComponent
from pyquibbler.path.path_component import Path, Paths
from pyquibbler.quib.func_calling.func_calls.vectorize.utils import get_core_axes
from pyquibbler.function_definitions import FuncCall, SourceLocation

from .numpy import NumpyForwardsPathTranslator, NumpyBackwardsPathTranslator
from ..array_translation_utils import ArrayPathTranslator
from ..types import Source
from ..array_index_codes import INDEX_TYPE


class VectorizeBackwardsPathTranslator(NumpyBackwardsPathTranslator):

    def __init__(self, func_call, shape: Optional[Shape], type_: Optional[Type], path,
                 vectorize_metadata=None):
        super().__init__(func_call, shape, type_, path)
        self._vectorize_metadata = vectorize_metadata

    def _get_indices_in_source(self,
                               data_argument_to_source_index_code_converter: ArrayPathTranslator,
                               result_bool_mask: NDArray[bool]) -> Tuple[NDArray[INDEX_TYPE], NDArray[bool]]:
        data_arg_source_index_code = data_argument_to_source_index_code_converter.get_masked_data_argument_of_source()
        vectorize_metadata = self._vectorize_metadata
        result_core_axes = vectorize_metadata.result_core_axes
        # Reduce result core dimensions:
        reduced_bool_mask = np.any(result_bool_mask, axis=result_core_axes, keepdims=True)
        reduced_bool_mask = unbroadcast_or_broadcast_bool_mask(reduced_bool_mask, np.shape(data_arg_source_index_code))
        return data_arg_source_index_code, reduced_bool_mask

    def _get_source_path(self, source: Source, location: SourceLocation) -> Path:
        """
        Given a path in the result, return the path in the given quib on which the result path depends.
        """
        if len(self._path) == 0:
            return []

        # TODO: if the result is a tuple, we should better translate the rest of the path, path[1:]
        if self._vectorize_metadata.is_result_a_tuple:
            return []

        if self._shape is None:
            self._raise_run_failed_exception()

        return super()._get_source_path(source, location)


class VectorizeForwardsPathTranslator(NumpyForwardsPathTranslator):

    def __init__(self,
                 func_call: FuncCall,
                 source: Source,
                 source_location: SourceLocation,
                 path: Path,
                 shape: Optional[Shape],
                 type_: Optional[Type],
                 vectorize_metadata):
        super().__init__(func_call, source, source_location, path, shape, type_)
        self._vectorize_metadata = vectorize_metadata

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        data_arg_bool_mask = data_argument_to_mask_converter.get_masked_data_argument_of_source()

        arg_id = data_argument_to_mask_converter.focal_source_location.argument.get_arg_id()
        if isinstance(arg_id, int):
            arg_id = arg_id - 1  # accounting for the func at position 0
        core_ndim = self._vectorize_metadata.args_metadata[arg_id].core_ndim

        data_arg_bool_mask = np.any(data_arg_bool_mask, axis=get_core_axes(core_ndim))
        return np.broadcast_to(data_arg_bool_mask, self._vectorize_metadata.result_loop_shape)

    def _forward_translate(self) -> Paths:

        paths = super()._forward_translate()

        if len(paths) == 0 or not self._vectorize_metadata.is_result_a_tuple:
            return paths

        return [[PathComponent(i)] + paths[0] for i in range(self._vectorize_metadata.tuple_length)]
