import numpy as np
from typing import Any

from pyquibbler.function_definitions import SourceLocation
from pyquibbler.path import deep_get
from pyquibbler.path.path_component import Path, Paths, PathComponent
from pyquibbler.path.utils import working_component_of_type
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices

from pyquibbler.translation.types import Source
from pyquibbler.translation.numpy_translator import NumpyForwardsPathTranslator, NumpyBackwardsPathTranslator
from .types import IndexCode, MAXIMAL_NON_FOCAL_SOURCE
from .utils import convert_args_kwargs_to_source_index_codes, run_func_call_with_new_args_kwargs


class BackwardsTranspositionalTranslator(NumpyBackwardsPathTranslator):

    def _get_path_in_source(self, source: Source, location: SourceLocation):
        args, kwargs, _ = convert_args_kwargs_to_source_index_codes(self._func_call, source, location)
        result = run_func_call_with_new_args_kwargs(self._func_call, args, kwargs)
        result = deep_get(result, self._working_path)

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
            return [PathComponent(mask)]


class ForwardsTranspositionalTranslator(NumpyForwardsPathTranslator):

    def forward_translate_initial_path_to_bool_mask(self, path: Path):
        working_component, _ = working_component_of_type(self._path, isinstance(self._source.value, (list, np.ndarray)))
        args, kwargs, _ = convert_args_kwargs_to_source_index_codes(self._func_call, self._source,
                                                                    self._source_location, working_component)
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
        if len(path) > 0 and path[0].referencing_field_in_field_array(self._source_type()):
            # The path at the first component references a field, and therefore we cannot translate it given a
            # normal transpositional function (neither does it make any difference, as transpositional functions
            # don't change fields)
            return [path]

        working_component, rest_of_path = working_component_of_type(self._path,
                                                                    isinstance(self._source.value, (list, np.ndarray)))
        is_scalar_result = \
            not isinstance(deep_get(np.array(self._source.value), [PathComponent(working_component)]), np.ndarray)
        args, kwargs, remaining_path = \
            convert_args_kwargs_to_source_index_codes(self._func_call, self._source, self._source_location,
                                                      working_component)
        result_index_code = run_func_call_with_new_args_kwargs(self._func_call, args, kwargs)
        result_mask = result_index_code > MAXIMAL_NON_FOCAL_SOURCE

        translated_path = [PathComponent(result_mask, extract_element_out_of_array=is_scalar_result),
                           *remaining_path]
        if np.any(result_index_code[result_mask] == IndexCode.SCALAR_CONTAINING_FOCAL_SOURCE):
            translated_path = translated_path + self._path
        else:
            translated_path = translated_path + rest_of_path
        return [translated_path]
