from typing import List

import numpy as np
from numpy.typing import NDArray

from pyquibbler.function_definitions import SourceLocation, FuncArgsKwargs
from pyquibbler.path import deep_get
from pyquibbler.path.path_component import PathComponent
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices

from pyquibbler.translation.types import Source
from pyquibbler.translation.translators.numpy_translator import NumpyBackwardsPathTranslator, \
    NumpyForwardsPathTranslator
from pyquibbler.translation.array_index_codes import IndexCode, is_focal_element
from pyquibbler.translation.array_translation_utils import ArrayPathTranslator, \
    run_func_call_with_new_args_kwargs


class BackwardsTranspositionalTranslator(NumpyBackwardsPathTranslator):

    def _get_path_in_source(self, source: Source, location: SourceLocation):
        func_args_kwargs = ArrayPathTranslator(func_call=self._func_call, focal_source=source,
                                               focal_source_location=location).get_func_args_kwargs()
        result = run_func_call_with_new_args_kwargs(self._func_call, func_args_kwargs)
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


class ForwardsTranspositionalTranslator(NumpyForwardsPathTranslator):
    """
    Forward translate numpy transpositional functions (like array, rot90, flip).
    Works by applying the function to the data args replaced with bool mask
    """
    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        # We simply apply the quib function to the boolean-transformed arguments
        masked_func_args_kwargs = data_argument_to_mask_converter.get_func_args_kwargs()
        return run_func_call_with_new_args_kwargs(self._func_call, masked_func_args_kwargs)
