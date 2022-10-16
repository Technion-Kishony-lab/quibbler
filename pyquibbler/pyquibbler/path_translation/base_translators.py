from abc import abstractmethod

from typing import Dict, Optional, Type

from pyquibbler.utilities.general_utils import Shape
from pyquibbler.path import Path, Paths
from pyquibbler.function_definitions import FuncCall, SourceLocation

from .source_func_call import SourceFuncCall
from .types import Source
from ..utilities.multiple_instance_runner import ConditionalRunner, RunCondition


class BackwardsTranslationRunCondition(RunCondition):
    NO_SHAPE_AND_TYPE = 1
    WITH_SHAPE_AND_TYPE = 2


class BackwardsPathTranslator(ConditionalRunner):
    """
    A BackwardsPathTranslator translates a path in a FuncCall's result back into paths of the FuncCall's
    sources.
    We create a specialized BackwardsPathTranslator for a specific type of functions, and add it to
    their FuncDefinition in the `function_overriding.third_party_overriding` package.
    """
    # Specified whether the translator needs shape and type of the function result and the sources.
    RUN_CONDITIONS = [BackwardsTranslationRunCondition.WITH_SHAPE_AND_TYPE]

    def __init__(self, func_call: SourceFuncCall, shape: Optional[Shape], type_: Optional[Type], path: Path):
        self._func_call = func_call
        self._shape = shape
        self._path = path
        self._type = type_

    @abstractmethod
    def _backwards_translate(self) -> Dict[Source, Path]:
        """
        Translate the path back to a mapping between sources and their respective paths which have an equivalence to
        self._path
        """
        pass

    def try_run(self):
        return self._backwards_translate()


class ForwardsPathTranslator(ConditionalRunner):
    """
    A ForwardsPathTranslator translates a path forwards from a given path of the sources to a
    mapping between each source and where that path will be in the result (a list of paths).
    Normally, we create a ForwardsPathTranslator for a specific type of functions and then add it as the
    translator in the `function_overriding.third_party_overriding` package.
    """
    def __init__(self,
                 func_call: FuncCall,
                 source: Source,
                 source_location: SourceLocation,
                 path: Path,
                 shape: Optional[Shape],
                 type_: Optional[Type]):
        self._func_call = func_call
        self._source = source
        self._source_location = source_location
        self._path = path
        self._shape = shape
        self._type = type_

    @abstractmethod
    def _forward_translate(self) -> Paths:
        pass

    def try_run(self):
        return self._forward_translate()

    def _get_source_type(self):
        return type(self._source.value)
