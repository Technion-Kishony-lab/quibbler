from abc import abstractmethod
from typing import Any, List, Dict, Optional, Type, Tuple

import numpy as np

from pyquibbler.path.path_component import PathComponent, Path
from pyquibbler.path import working_component, translate_bool_vector_to_slice_if_possible
from pyquibbler.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.translation.exceptions import FailedToTranslateException
from pyquibbler.translation.forwards_path_translator import ForwardsPathTranslator
from pyquibbler.translation.types import Source, NoMetadataSource


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

    SHOULD_ATTEMPT_WITHOUT_SHAPE_AND_TYPE = True

    def __init__(self, func_call, sources_to_paths: Dict[Source, Path], shape: Optional[Tuple[int, ...]],
                 type_: Optional[Type], should_forward_empty_paths_to_empty_paths: bool = True):
        super().__init__(func_call, sources_to_paths, shape, type_)
        self._should_forward_empty_paths_to_empty_paths = should_forward_empty_paths_to_empty_paths

    @abstractmethod
    def _forward_translate_indices_to_bool_mask(self, source: Source, indices: Any) -> np.ndarray:
        pass

    def _forward_translate_source(self, source: Source, path: Path) -> List[Path]:
        # TODO: THIS AUTO RETURNING OF [[]] IS INCORRECT IF PATH IS EMPTY, IN SOME EDGE CASES THIS DOESN'T HOLD
        if len(path) == 0 and self._should_forward_empty_paths_to_empty_paths:
            return [[]]

        if isinstance(source, NoMetadataSource):
            raise FailedToTranslateException()

        bool_mask_in_output_array = self._forward_translate_indices_to_bool_mask(source, working_component(path))
        if np.any(bool_mask_in_output_array):
            # If there exist both True's and False's in the boolean mask,
            # this function's quib result must be an ndarray- if it were a single item (say a PyObj, int, dict, list)
            # we'd expect it to be completely True (as it is ONE single object). If it is not a single item, it is by
            # definition an ndarray
            assert issubclass(self._type, (np.ndarray, list)) or np.all(bool_mask_in_output_array)
            assert issubclass(self._type, (np.ndarray, list)) or isinstance(bool_mask_in_output_array, np.bool_) \
                   or (bool_mask_in_output_array.shape == () and bool_mask_in_output_array.dtype == np.bool_)

            if not issubclass(self._type, (np.ndarray, list)) and np.all(bool_mask_in_output_array):
                return [path[1:]]

            if len(path) > 0 and issubclass(path[0].indexed_cls, (list, np.ndarray)):
                # If we are in a situation in which the first component is a referencing an ndarray or list, then the
                # `bool_mask_in_output_array` is already a combination of the first component with the
                # self._func_call.func- therefore, we are going to replace the first component with the
                # bool_mask_in_output_array
                rest_of_path = path[1:]
            else:
                rest_of_path = path

            if len(path) > 0 and issubclass(path[0].indexed_cls, list) and issubclass(self._type, list):
                assert np.ndim(bool_mask_in_output_array) == 1
                slice_index = translate_bool_vector_to_slice_if_possible(bool_mask_in_output_array)
                if slice_index:
                    return [[PathComponent(self._type, slice_index),
                             *rest_of_path]]
                return [[]] # TODO: may need to treat as list of paths

            return [[PathComponent(self._type, bool_mask_in_output_array),
                     *rest_of_path]]

        return []
