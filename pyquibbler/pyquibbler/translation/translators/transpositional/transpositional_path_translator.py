import numpy as np
from typing import Any

from pyquibbler.path import deep_get
from pyquibbler.path.path_component import Path, Paths, PathComponent
from pyquibbler.path.utils import working_component_of_type
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices

from pyquibbler.translation.numpy_translator import NumpyForwardsPathTranslator
from pyquibbler.translation.numpy_translator import NumpyBackwardsPathTranslator
from pyquibbler.translation.translators.transpositional.utils \
    import get_data_source_mask, get_data_source_indices, find_all_indices
from pyquibbler.translation.types import Source


class BackwardsTranspositionalTranslator(NumpyBackwardsPathTranslator):

    def _get_path_in_source(self, source: Source):
        result = get_data_source_indices(self._func_call, source)
        result = deep_get(result, [PathComponent(np.ndarray, self._working_component)])

        indices = find_all_indices(result)
        if np.size(indices) == 0:
            return None

        mask = create_bool_mask_with_true_at_indices((np.size(source.value), ), indices)
        mask = mask.reshape(np.shape(source.value))
        if np.array_equal(mask, np.array(True)):
            return []
        else:
            return [PathComponent(np.ndarray, mask)]


class ForwardsTranspositionalTranslator(NumpyForwardsPathTranslator):

    def _forward_translate_indices_to_bool_mask(self, source: Source, indices: Any):
        return np.equal(get_data_source_mask(self._func_call, source,
                                             working_component_of_type(self._path, (list, np.ndarray), True)), True)

    def _forward_translate_source(self, source: Source, path: Path) -> Paths:
        """
        There are two things we can potentially do:
        1. Translate the invalidation path given the current function source (eg if this function source is rotate,
        take the invalidated indices, rotate them and invalidate children with the resulting indices)
        2. Pass on the current path to all our children
        """
        if len(path) > 0 and path[0].references_field_in_field_array():
            # The path at the first component references a field, and therefore we cannot translate it given a
            # normal transpositional function (neither does it make any difference, as transpositional functions
            # don't change fields)
            return [path]

        return super(ForwardsTranspositionalTranslator, self)._forward_translate_source(source, path)
