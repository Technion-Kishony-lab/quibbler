from abc import ABC, abstractmethod
from typing import Type, Dict, Any, List

import numpy as np

from pyquibbler.utilities.numpy_original_functions import np_logical_and, np_all
from pyquibbler.utilities.missing_value import missing
from pyquibbler.function_definitions import SourceLocation
from pyquibbler.path import Path, PathComponent, deep_get
from pyquibbler.assignment.assignment import create_assignment_from_nominal_down_up_values

from pyquibbler.path_translation import Source, BackwardsPathTranslator, ForwardsPathTranslator, Inversal
from pyquibbler.path_translation.translators.numpy import \
    NumpyBackwardsPathTranslator, NumpyForwardsPathTranslator

from ..inverter import Inverter


class NumpyInverter(Inverter, ABC):
    """
    Basic assignment inversion functionality for numpy functions.
    """
    # subclasses should specify their own backwards/forwards translators
    # the forward inverter must return a bool mask of the size of the target as first component (or empty)
    BACKWARDS_TRANSLATOR_TYPE: Type[BackwardsPathTranslator] = NumpyBackwardsPathTranslator
    FORWARDS_TRANSLATOR_TYPE: Type[ForwardsPathTranslator] = NumpyForwardsPathTranslator

    # can one element in the argument affect multiple elements in the result
    IS_ONE_TO_MANY_FUNC: bool = False

    def _get_data_sources_to_locations(self) -> Dict[Source, SourceLocation]:
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
            bool_mask_paths_in_result = forwards_translator._forward_translate()
            assert len(bool_mask_paths_in_result) == 1
            sources_to_bool_mask_path_in_result[source] = bool_mask_paths_in_result[0]
        return sources_to_bool_mask_path_in_result

    def get_inversals(self) -> List[Inversal]:
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
        sources_to_path_in_source = backwards_translator._backwards_translate()

        # (2) forward translate:
        sources_to_bool_mask_path_in_result = \
            self._forward_translate_paths_in_sources_to_bool_mask_paths_in_results(sources_to_path_in_source)

        # (3) intersect with the boolean mask with the target:
        boolean_mask, path_in_array, remaining_path = backwards_translator.get_result_bool_mask_and_split_path()

        if self.IS_ONE_TO_MANY_FUNC:
            for source, path in sources_to_bool_mask_path_in_result.items():
                if not np_all(boolean_mask):
                    if len(path) > 0:
                        path[0] = PathComponent(np_logical_and(path[0].component, boolean_mask))
                    else:
                        path.insert(0, PathComponent(boolean_mask))

        return self._create_inversals_from_source_paths(sources_to_path_in_source, sources_to_bool_mask_path_in_result)

    def _create_inversals_from_source_paths(self,
                                            sources_to_path_in_source: Dict[Source, Path],
                                            sources_to_path_in_result: Dict[Source, Path]
                                            ) -> List[Inversal]:

        result_with_assignment_nominal_down_up = self._get_result_with_assignment_nominal_down_up()
        sources_to_locations = self._get_data_sources_to_locations()
        inversals = []
        for source, path_in_source in sources_to_path_in_source.items():
            if source not in sources_to_path_in_result:
                continue

            # (4) get value from the result with the new assignment, at path matching the current source:
            path_in_result = sources_to_path_in_result[source]
            target_value_nominal_down_up = tuple(deep_get(result_with_assignment, path_in_result)
                                                 for result_with_assignment in result_with_assignment_nominal_down_up)

            location = sources_to_locations[source]
            inverted_value_nominal_down_up = \
                tuple(
                    self._get_invert_value_or_raise_if_nan(source, location, path_in_source,
                                                           target_value, path_in_result)
                    for target_value in target_value_nominal_down_up
                )
            if inverted_value_nominal_down_up[0] is not missing:
                new_assignment = create_assignment_from_nominal_down_up_values(
                    nominal_down_up_values=inverted_value_nominal_down_up, path=path_in_source)
                inversals.append(Inversal(source=source, assignment=new_assignment))

        return inversals

    def _get_invert_value_or_raise_if_nan(self, source: Source, source_location: SourceLocation, path_in_source: Path,
                                          result_value: Any, path_in_result: Path) -> Any:
        previous_err = np.seterr(all='raise')
        try:
            value = self._invert_value(source, source_location, path_in_source, result_value, path_in_result)
        except (RuntimeError, FloatingPointError):
            self._raise_run_failed_exception()
        finally:
            np.seterr(**previous_err)
        if isinstance(value, np.ndarray) \
                and (value.dtype.type is np.float64 or value.dtype.type is np.float32) \
                and np.any(np.isnan(value)):
            self._raise_run_failed_exception()
        return value

    @abstractmethod
    def _invert_value(self, source: Source, source_location: SourceLocation, path_in_source: Path,
                      result_value: Any, path_in_result: Path) -> Any:
        """
        Apply the inverse function of the numeric value to assign
        Returns `missing` if cannot invert
        """
        pass
