from abc import abstractmethod
from typing import Any, List, Dict

import numpy as np

from pyquibbler.path.path_component import PathComponent, Path
from pyquibbler.path.utils import working_component, path_beyond_working_component
from pyquibbler.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.translation.forwards_path_translator import ForwardsPathTranslator
from pyquibbler.translation.types import Source


class NumpyBackwardsPathTranslator(BackwardsPathTranslator):
    """
    Holds basic logic for how to backwards translate a path for numpy functions- subclass this for any translator of a
    numpy function.
    Mainly concerns surrounding logic with deep paths
    """

    @abstractmethod
    def _get_path_in_source(self, source: Source):
        pass

    def _split_path(self):
        components_at_end = self._path[1:]
        current_components = self._path[0:1]
        if len(self._path) > 0 and self._path[0].references_field_in_field_array():
            components_at_end = [self._path[0], *components_at_end]
            current_components = []
        return current_components, components_at_end

    def translate(self) -> Dict[Source, Path]:
        sources_to_paths = {}
        working, rest = self._split_path()
        for source in self._func_call.get_data_sources():
            new_path = self._get_path_in_source(source)
            if new_path is not None:
                sources_to_paths[source] = [*new_path, *rest]
        return sources_to_paths


class NumpyForwardsPathTranslator(ForwardsPathTranslator):
    """
    Holds basic logic for how to forwards translate a path for numpy functions- subclass this for any translator of a
    numpy function.
    """

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
