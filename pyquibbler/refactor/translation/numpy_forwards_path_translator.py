from abc import abstractmethod
from typing import Any, List

import numpy as np

from pyquibbler.refactor.quib.assignment import PathComponent
from pyquibbler.refactor.quib.assignment.assignment import path_beyond_working_component, Path, working_component
from pyquibbler.refactor.translation.forwards_path_translator import ForwardsPathTranslator
from pyquibbler.refactor.translation.path_translator import Translator
from pyquibbler.refactor.translation.types import Source


class NumpyForwardsPathTranslator(ForwardsPathTranslator):

    @abstractmethod
    def _forward_translate_indices_to_bool_mask(self, source: Source, indices: Any):
        pass

    def _forward_translate_source(self, source: Source, path: Path) -> List[Path]:
        bool_mask_in_output_array = self._forward_translate_indices_to_bool_mask(source, working_component(path))
        if np.any(bool_mask_in_output_array):
            # If there exist both True's and False's in the boolean mask,
            # this function's quib result must be an ndarray- if it were a single item (say a PyObj, int, dict, list)
            # we'd expect it to be completely True (as it is ONE single object). If it is not a single item, it is by
            # definitely an ndarray
            assert issubclass(self._type, np.ndarray) or np.all(bool_mask_in_output_array)
            assert issubclass(self._type, np.ndarray) or isinstance(bool_mask_in_output_array, np.bool_) \
                   or (bool_mask_in_output_array.shape == () and bool_mask_in_output_array.dtype == np.bool_)

            if not np.all(bool_mask_in_output_array) and issubclass(self._type, np.ndarray):
                return [[PathComponent(self._type, bool_mask_in_output_array),
                         *path_beyond_working_component(path)]]
            return [path_beyond_working_component(path)]
        return []

    def translate(self):
        return {
            # TODO: THIS AUTO RETURNING OF [[]] IS INCORRECT IF PATH IS EMPTY, IN SOME EDGE CASES THIS DOESN'T HOLD
            source: self._forward_translate_source(source, path) if len(path) != 0 else [[]]
            for source, path in self._sources_to_paths.items()
        }

