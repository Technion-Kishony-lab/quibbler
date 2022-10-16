from typing import Type, Any

from pyquibbler.utilities.missing_value import missing
from pyquibbler.path import Path
from pyquibbler.function_definitions import SourceLocation

from pyquibbler.path_translation import BackwardsPathTranslator, ForwardsPathTranslator, Source
from pyquibbler.path_translation.translators.list_operators import \
    ListOperatorBackwardsPathTranslator, ListOperatorForwardsPathTranslator, ListOperatorPathTranslator

from .numpy import NumpyInverter


class ListOperatorInverter(NumpyInverter, ListOperatorPathTranslator):
    """
    Invert list addition and multiplication operators.
    We use the numpy inverter, converting the list to object array using the
    ListOperatorBackwardsPathTranslator and ListOperatorForwardsPathTranslator.
    """
    IS_ONE_TO_MANY_FUNC = True

    def can_try(self) -> bool:
        return isinstance(self._previous_result, list)

    BACKWARDS_TRANSLATOR_TYPE: Type[BackwardsPathTranslator] = ListOperatorBackwardsPathTranslator
    FORWARDS_TRANSLATOR_TYPE: Type[ForwardsPathTranslator] = ListOperatorForwardsPathTranslator

    def _invert_value(self, source: Source, source_location: SourceLocation, path_in_source: Path,
                      result_value: Any, path_in_result: Path) -> Any:
        # If we are multiplying `n * list`, we cannot invert into `n`
        if source_location.argument.index not in self.get_indices_of_data_args_which_are_lists():
            return missing
        return result_value
