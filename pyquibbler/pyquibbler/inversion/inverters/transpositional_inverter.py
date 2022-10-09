from typing import Type, Dict, Any

import numpy as np

from pyquibbler.function_definitions import SourceLocation
from pyquibbler.path.data_accessing import deep_get
from pyquibbler.inversion.inverter import Inverter
from pyquibbler.assignment import Assignment
from pyquibbler.translation import BackwardsPathTranslator, ForwardsPathTranslator
from pyquibbler.translation.translators import BackwardsTranspositionalTranslator, ForwardsTranspositionalTranslator
from pyquibbler.translation.translators.numpy_translator import NumpyBackwardsPathTranslator, \
    NumpyForwardsPathTranslator
from pyquibbler.translation.types import Inversal, Source
from pyquibbler.path.path_component import PathComponent, Path
from pyquibbler.utilities.numpy_original_functions import np_logical_and


class NumpyInverter(Inverter):

    # subclasses should specify their own backwards/forwards translators
    BACKWARDS_TRANSLATOR_TYPE: Type[BackwardsPathTranslator] = NumpyBackwardsPathTranslator
    FORWARDS_TRANSLATOR_TYPE: Type[ForwardsPathTranslator] = NumpyForwardsPathTranslator

    def _get_data_sources_to_locations(self):
        return {source: location for source, location
                in zip(self._func_call.get_data_sources(), self._func_call.data_source_locations)}

    def _create_backwards_translator(self):
        return self.BACKWARDS_TRANSLATOR_TYPE(
            func_call=self._func_call,
            path=self._assignment.path,
            shape=np.shape(self._previous_result),
            type_=type(self._previous_result)
        )

    def _create_forwards_translator(self, source: Source, source_location: SourceLocation, path_in_source: Path):
        return self.FORWARDS_TRANSLATOR_TYPE(
            func_call=self._func_call,
            source=source,
            source_location=source_location,
            path=path_in_source,
            shape=np.shape(self._previous_result),
            type_=type(self._previous_result),
        )

    def _forward_translate_paths_in_sources_to_bool_mask_paths_in_results(
            self, sources_to_paths_in_sources: Dict[Source, Path]) -> Dict[Source, Path]:

        sources_to_locations = self._get_data_sources_to_locations()
        sources_to_bool_mask_path_in_result = dict()
        for source, path_in_source in sources_to_paths_in_sources.items():
            forwards_translator = self._create_forwards_translator(source, sources_to_locations[source], path_in_source)
            bool_mask_paths_in_result = forwards_translator.forward_translate()
            assert len(bool_mask_paths_in_result) == 1
            sources_to_bool_mask_path_in_result[source] = bool_mask_paths_in_result[0]
        return sources_to_bool_mask_path_in_result


class TranspositionalInverter(NumpyInverter):

    BACKWARDS_TRANSLATOR_TYPE: Type[BackwardsPathTranslator] = BackwardsTranspositionalTranslator
    FORWARDS_TRANSLATOR_TYPE: Type[ForwardsPathTranslator] = ForwardsTranspositionalTranslator

    def _create_inversals_from_paths(self,
                                     sources_to_path_in_source: Dict[Source, Path],
                                     sources_to_assignment_value: Dict[Source, Any]):
        return [
            Inversal(
                source=source,
                assignment=Assignment(
                    path=path,
                    value=sources_to_assignment_value[source]
                )
            ) for source, path in sources_to_path_in_source.items() if source in sources_to_assignment_value]

    def get_inversals(self):
        """
        The strategy is to assign to the result and then use deep_get to get the right value for each source.
        To figure out the path and value for each source, we follow 4 steps (for each source):

        1. backward translate the result path to the source path (this is our assignment path)

        2. forward translate the source path back to a boolean path in the target

        3. intersect the boolean mask with the target path boolean mask
            (because the source could have replicated to multiple elements in the target array,
            not only those assigned to)

        4. deep_get the assignment-set target with the path to get the value (this is our assignment value)
        """
        # (1) backward translate:
        backwards_translator = self._create_backwards_translator()
        sources_to_path_in_source = backwards_translator.backwards_translate()

        # (2) forward translate:
        sources_to_bool_mask_path_in_result = \
            self._forward_translate_paths_in_sources_to_bool_mask_paths_in_results(sources_to_path_in_source)

        # (3) intersect with the boolean mask with the target:
        boolean_mask, path_in_array, remaining_path = backwards_translator.get_result_bool_mask_and_split_path()

        for source, path in sources_to_bool_mask_path_in_result.items():
            if len(path) > 0:
                path[0] = PathComponent(np_logical_and(path[0].component, boolean_mask))
            else:
                path.insert(0, PathComponent(boolean_mask))

        # (4) get value from the result with the new assignment:
        result_with_assignment_set = self._get_result_with_assignment_set()
        sources_to_assignment_value = {source: deep_get(result_with_assignment_set, path)
                                       for source, path in sources_to_bool_mask_path_in_result.items()}
        return self._create_inversals_from_paths(sources_to_path_in_source, sources_to_assignment_value)
