from abc import abstractmethod
from typing import Dict, Optional, Tuple, Type

from pyquibbler.function_definitions import FuncCall
from pyquibbler.path.path_component import Path, Paths

from pyquibbler.utilities.general_utils import Shape
from .types import Source


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
                 func_call: Type[FuncCall], sources_to_paths: Dict[Source, Path],
                 shape: Optional[Shape],
                 type_: Optional[Type]):
        self._func_call = func_call
        self._sources_to_paths = sources_to_paths
        self._shape = shape
        self._type = type_

    @abstractmethod
    def _forward_translate_source(self, source: Source, path: Path) -> Paths:
        pass

    def forward_translate(self) -> Dict[Source, Paths]:
        return {
            source: self._forward_translate_source(source, path)
            for source, path in self._sources_to_paths.items()
        }
