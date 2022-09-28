import numpy as np
from typing import Any

from pyquibbler.function_definitions import SourceLocation
from pyquibbler.path import deep_get
from pyquibbler.path.path_component import Path, Paths, PathComponent, OutFromArray
from pyquibbler.path.utils import working_component_of_type
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices

from pyquibbler.translation.types import Source
from pyquibbler.translation.numpy_translator import NumpyForwardsPathTranslator, NumpyBackwardsPathTranslator
from .types import IndexCode, MAXIMAL_NON_FOCAL_SOURCE
from .utils import get_data_source_indices, run_func_call_with_new_args_kwargs


class BackwardsTranspositionalTranslator(NumpyBackwardsPathTranslator):

    def _get_path_in_source(self, source: Source, location: SourceLocation):
        args, kwargs, _ = get_data_source_indices(self._func_call, source, location)
        result = run_func_call_with_new_args_kwargs(self._func_call, args, kwargs)
        result = deep_get(result, [PathComponent(np.ndarray, self._working_component)])

        result = np.array(result)

        indices = result[result > MAXIMAL_NON_FOCAL_SOURCE]

        if np.size(indices) == 0:
            # Source not part of result
            return None

        if np.any(indices == IndexCode.SCALAR_CONTAINING_FOCAL_SOURCE):
            # The entire source is needed, contained in one element of the array (minor-source)
            return []

        if np.any(indices == IndexCode.FOCAL_SOURCE_SCALAR):
            # The entire source is needed as one element of the array (uni-source)
            return []

        mask = create_bool_mask_with_true_at_indices((np.size(source.value), ), indices)
        mask = mask.reshape(np.shape(source.value))
        if np.array_equal(mask, np.array(True)):
            return []
        else:
            return [PathComponent(np.ndarray, mask)]


class ForwardsTranspositionalTranslator(NumpyForwardsPathTranslator):

    def _forward_translate_indices_to_bool_mask(self, indices: Any):
        working_component, _ = working_component_of_type(self._path, (list, np.ndarray))
        args, kwargs, _ = get_data_source_indices(self._func_call, self._source, self._source_location,
                                                  working_component)
        result_index_code = run_func_call_with_new_args_kwargs(self._func_call, args, kwargs)
        return np.equal(result_index_code > MAXIMAL_NON_FOCAL_SOURCE, True)

    def forward_translate(self) -> Paths:
        """
        There are two things we can potentially do:
        1. Translate the invalidation path given the current function source (eg if this function source is rotate,
        take the invalidated indices, rotate them and invalidate children with the resulting indices)
        2. Pass on the current path to all our children
        """
        path = self._path
        if len(path) > 0 and path[0].references_field_in_field_array():
            # The path at the first component references a field, and therefore we cannot translate it given a
            # normal transpositional function (neither does it make any difference, as transpositional functions
            # don't change fields)
            return [path]

        working_component, rest_of_path = working_component_of_type(self._path, (list, np.ndarray))
        is_scalar_result = not isinstance(np.array(self._source.value)[working_component], np.ndarray)
        args, kwargs, remaining_path = \
            get_data_source_indices(self._func_call, self._source, self._source_location, working_component)
        result_index_code = run_func_call_with_new_args_kwargs(self._func_call, args, kwargs)
        result_mask = result_index_code > MAXIMAL_NON_FOCAL_SOURCE

        translated_path = [PathComponent(OutFromArray if is_scalar_result else np.ndarray, result_mask),
                           *remaining_path]
        if np.any(result_index_code[result_mask] == IndexCode.SCALAR_CONTAINING_FOCAL_SOURCE):
            translated_path = translated_path + self._path
        else:
            translated_path = translated_path + rest_of_path
        return [translated_path]
