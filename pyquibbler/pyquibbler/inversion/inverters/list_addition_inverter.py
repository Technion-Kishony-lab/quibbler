from typing import Type, Any

from pyquibbler.path import Path
from pyquibbler.function_definitions import SourceLocation
from pyquibbler.path_translation import BackwardsPathTranslator, ForwardsPathTranslator, Source

from .numpy_inverter import NumpyInverter
from pyquibbler.path_translation.translators.list_addition_translator import \
    ListAdditionBackwardsPathTranslator, ListAdditionForwardsPathTranslator


class ListAdditionInverter(NumpyInverter):

    def can_try(self) -> bool:
        return isinstance(self._previous_result, list)

    BACKWARDS_TRANSLATOR_TYPE: Type[BackwardsPathTranslator] = ListAdditionBackwardsPathTranslator
    FORWARDS_TRANSLATOR_TYPE: Type[ForwardsPathTranslator] = ListAdditionForwardsPathTranslator

    def _invert_value(self, source: Source, source_location: SourceLocation, path_in_source: Path,
                      result_value: Any, path_in_result: Path) -> Any:
        return result_value
