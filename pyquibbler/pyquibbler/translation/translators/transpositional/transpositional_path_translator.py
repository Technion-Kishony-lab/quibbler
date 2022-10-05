import numpy as np

from pyquibbler.function_definitions import SourceLocation
from pyquibbler.path import deep_get
from pyquibbler.path.path_component import Path, Paths, PathComponent
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices

from pyquibbler.translation.types import Source
from pyquibbler.translation.numpy_translator import NumpyForwardsPathTranslator, NumpyBackwardsPathTranslator
from .types import IndexCode, is_focal_element
from .utils import convert_args_kwargs_to_source_index_codes, run_func_call_with_new_args_kwargs
from ... import ForwardsPathTranslator


class BackwardsTranspositionalTranslator(NumpyBackwardsPathTranslator):

    def _get_path_in_source(self, source: Source, location: SourceLocation):
        args, kwargs, _, _, _ = convert_args_kwargs_to_source_index_codes(self._func_call, source, location)
        result = run_func_call_with_new_args_kwargs(self._func_call, args, kwargs)
        result = deep_get(result, self._working_path)

        result = np.array(result)

        indices = result[is_focal_element(result)]

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


class ForwardsTranspositionalTranslator(ForwardsPathTranslator):

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

        args, kwargs, remaining_path_to_source, within_array_path, within_element_path = \
            convert_args_kwargs_to_source_index_codes(self._func_call, self._source, self._source_location, self._path)
        is_scalar_result = not isinstance(deep_get(np.array(self._source.value), within_array_path), np.ndarray)
        result_index_code = run_func_call_with_new_args_kwargs(self._func_call, args, kwargs)
        result_mask = is_focal_element(result_index_code)

        translated_path = [PathComponent(result_mask, extract_element_out_of_array=is_scalar_result),
                           *remaining_path_to_source]
        if np.any(result_index_code[result_mask] == IndexCode.SCALAR_CONTAINING_FOCAL_SOURCE):
            translated_path = translated_path + self._path
        else:
            translated_path = translated_path + within_element_path
        return [translated_path]
