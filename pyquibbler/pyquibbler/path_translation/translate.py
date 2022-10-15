from abc import ABC
from typing import Type, Dict, List, Optional

from pyquibbler.utilities.multiple_instance_runner import RunCondition, MultipleInstanceRunner
from pyquibbler.path import Path, Paths
from pyquibbler.function_definitions.func_call import FuncCall

from .base_translators import BackwardsPathTranslator, ForwardsPathTranslator, BackwardsTranslationRunCondition
from .exceptions import FailedToTranslateException
from .types import Source
from ..function_definitions import SourceLocation
from ..utilities.general_utils import Shape


class MultipleFuncCallInstanceRunner(MultipleInstanceRunner, ABC):

    def __init__(self, run_condition: Optional[RunCondition], func_call: FuncCall):
        super().__init__(run_condition=run_condition)
        self._func_call = func_call

    def _get_exception_message(self):
        return self._func_call


class MultipleBackwardsTranslatorRunner(MultipleFuncCallInstanceRunner):

    def __init__(self,
                 run_condition: BackwardsTranslationRunCondition,
                 func_call: FuncCall,
                 path: Path,
                 shape: Optional[Shape],
                 type_: Optional[Type],
                 extra_kwargs_for_translator):
        super().__init__(run_condition, func_call)
        self._path = path
        self._shape = shape
        self._type = type_
        self._extra_kwargs_for_translator = extra_kwargs_for_translator

    def _get_all_runners(self) -> List[Type[BackwardsPathTranslator]]:
        return self._func_call.func_definition.backwards_path_translators

    def _run_runner(self, runner: Type[BackwardsPathTranslator]):
        translator = runner(
            func_call=self._func_call,
            path=self._path,
            shape=self._shape,
            type_=self._type,
            **self._extra_kwargs_for_translator
        )
        return translator.backwards_translate()


class MultipleForwardsTranslatorRunner(MultipleFuncCallInstanceRunner):

    def __init__(self,
                 func_call: FuncCall,
                 source: Source,
                 source_location: SourceLocation,
                 path: Path,
                 shape: Shape,
                 type_: Type,
                 extra_kwargs_for_translator: Dict = None):
        super().__init__(None, func_call)
        self._source = source
        self._source_location = source_location
        self._path = path
        self._shape = shape
        self._type = type_
        self._extra_kwargs_for_translator = extra_kwargs_for_translator

    def _run_runner(self, runner: Type[ForwardsPathTranslator]):
        return runner(
            func_call=self._func_call,
            shape=self._shape,
            type_=self._type,
            source=self._source,
            source_location=self._source_location,
            path=self._path,
            **self._extra_kwargs_for_translator
        ).forward_translate()

    def _get_all_runners(self) -> List[Type[ForwardsPathTranslator]]:
        return self._func_call.func_definition.forwards_path_translators


def backwards_translate(run_condition:BackwardsTranslationRunCondition,
                        func_call: FuncCall,
                        path: Path,
                        shape: Optional[Shape] = None,
                        type_: Optional[Type] = None,
                        **kwargs) -> Dict[Source, Path]:
    """
    Backwards translate a path given a func_call
    This gives a mapping of sources to paths that were referenced in given path in the result of the function
    """
    return MultipleBackwardsTranslatorRunner(run_condition=run_condition, func_call=func_call,
                                             path=path, shape=shape, type_=type_,
                                             extra_kwargs_for_translator=kwargs).run()


def forwards_translate(func_call: FuncCall, source: Source, source_location: SourceLocation,
                       path: Path, shape: Optional[Shape] = None, type_: Optional[Type] = None,
                       **kwargs) -> Paths:
    """
    Forwards translate a mapping of sources to paths through a function, giving for each source a list of paths that
    were affected by the given path for the source
    """
    return MultipleForwardsTranslatorRunner(func_call=func_call,
                                            source=source,
                                            source_location=source_location,
                                            path=path,
                                            shape=shape,
                                            type_=type_,
                                            extra_kwargs_for_translator=kwargs).run()
