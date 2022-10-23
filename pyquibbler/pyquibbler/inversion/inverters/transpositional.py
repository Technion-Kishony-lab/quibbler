from typing import Type, Any

from pyquibbler.path import Path
from pyquibbler.function_definitions import SourceLocation
from pyquibbler.path_translation import BackwardsPathTranslator, ForwardsPathTranslator, Source
from pyquibbler.path_translation.translators.transpositional import \
    TranspositionalBackwardsPathTranslator, TranspositionalForwardsPathTranslator

from .numpy import NumpyInverter


class TranspositionalOneToOneInverter(NumpyInverter):
    """
    Inverts assignments to transpositional functions (like `rot90`, `transpose`, `concatenate`, etc).
    Uses the transpositional path translators (based on array index code masks).
    """
    BACKWARDS_TRANSLATOR_TYPE: Type[BackwardsPathTranslator] = TranspositionalBackwardsPathTranslator
    FORWARDS_TRANSLATOR_TYPE: Type[ForwardsPathTranslator] = TranspositionalForwardsPathTranslator
    IS_ONE_TO_MANY_FUNC: bool = False

    def _invert_value(self, source: Source, source_location: SourceLocation, path_in_source: Path,
                      result_value: Any, path_in_result: Path) -> Any:
        return result_value


class TranspositionalOneToManyInverter(TranspositionalOneToOneInverter):
    """
    Inverts assignments to transpositional functions that can create multiple copies of each element.
    (like `full`, `repeat`, etc).
    """
    IS_ONE_TO_MANY_FUNC: bool = True
