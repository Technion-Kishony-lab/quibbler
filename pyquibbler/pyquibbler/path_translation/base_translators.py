from abc import abstractmethod

from typing import Dict, Optional, Type

from pyquibbler.utilities.general_utils import Shape
from pyquibbler.path import Path, Paths
from pyquibbler.function_definitions import FuncCall, SourceLocation

from .source_func_call import SourceFuncCall
from .types import Source


class BackwardsPathTranslator:
    """
    A backwards path translator knows how to translate a path in a FuncCall's result back into paths of the FuncCall's
    sources.
    Normally, you will create a backwardspathtranslator for a specific set of functions and then add it as the
    translator in the `function_overriding.third_party_overriding` package.
    """

    # Override this in your translator if you have the ability to translate without needing shape + type. If you can
    # only work without shape and type in specific situations,
    # raise `FailedToTranslateException` if you fail in order to attempt WITH shape + type
    SHOULD_ATTEMPT_WITHOUT_SHAPE_AND_TYPE = False

    def __init__(self, func_call: SourceFuncCall, shape: Optional[Shape], type_: Optional[Type], path: Path):
        self._func_call = func_call
        self._shape = shape
        self._path = path
        self._type = type_

    @abstractmethod
    def backwards_translate(self) -> Dict[Source, Path]:
        """
        Translate the path back to a mapping between sources and their respective paths which have an equivalence to
        self._path
        """
        pass


class ForwardsPathTranslator:
    """
    A forwardspathtranslator knows how to translate a path forwards from a given mapping of sources to paths to a
    mapping between each source and where that path will be in the result (a list of paths).
    Normally, you will create a forwardspathtranslator for a specific set of functions and then add it as the
    translator in the `function_overriding.third_party_overriding` package.
    """

    # Override this in your translator if you have the ability to translate without needing shape + type. If you can
    # only work without shape and type in specific situations,
    # raise `FailedToTranslateException` if you fail in order to attempt WITH shape + type
    SHOULD_ATTEMPT_WITHOUT_SHAPE_AND_TYPE = False

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
    def forward_translate(self) -> Paths:
        pass

    def _source_type(self):
        return type(self._source.value)
