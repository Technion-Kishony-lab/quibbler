from typing import Type, Dict, List, Optional

from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.utilities.multiple_instance_runner import MultipleFuncCallInstanceRunner
from pyquibbler.path import Path, Paths
from pyquibbler.function_definitions.func_call import FuncCall

from .base_translators import BackwardsPathTranslator, ForwardsPathTranslator
from .exceptions import FailedToTranslateException, NoTranslatorsWorkedException
from .types import Source
from ..function_definitions import SourceLocation
from ..utilities.general_utils import Shape


class MultipleBackwardsTranslatorRunner(MultipleFuncCallInstanceRunner):
    expected_runner_exception = FailedToTranslateException
    exception_to_raise_on_none_found = NoTranslatorsWorkedException

    def __init__(self, func_call: FuncCall, path: Path, shape, type_: Type,
                 extra_kwargs_for_translator):
        super().__init__(func_call)
        self._path = path
        self._shape = shape
        self._type = type_
        self._extra_kwargs_for_translator = extra_kwargs_for_translator

    def _get_runners_from_definition(self, definition: FuncDefinition) -> List[Type[BackwardsPathTranslator]]:
        return definition.backwards_path_translators

    def _run_runner(self, runner: Type[BackwardsPathTranslator]):
        if not runner.SHOULD_ATTEMPT_WITHOUT_SHAPE_AND_TYPE and self._type is None:
            raise FailedToTranslateException()
        translator = runner(
            func_call=self._func_call,
            path=self._path,
            shape=self._shape,
            type_=self._type,
            **self._extra_kwargs_for_translator
        )
        return translator.backwards_translate()


class MultipleForwardsTranslatorRunner(MultipleFuncCallInstanceRunner):

    expected_runner_exception = FailedToTranslateException
    exception_to_raise_on_none_found = NoTranslatorsWorkedException

    def __init__(self, func_call: FuncCall,
                 source: Source,
                 source_location: SourceLocation,
                 path: Path,
                 shape: Optional[Shape] = None,
                 type_: Optional[Type] = None,
                 extra_kwargs_for_translator: Dict = None):
        super().__init__(func_call)
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

    def _get_runners_from_definition(self, definition: FuncDefinition) -> List[Type[ForwardsPathTranslator]]:
        return definition.forwards_path_translators


def backwards_translate(func_call: FuncCall, path: Path,
                        shape: Optional[Shape] = None, type_: Optional[Type] = None, **kwargs) -> Dict[Source, Path]:
    """
    Backwards translate a path given a func_call
    This gives a mapping of sources to paths that were referenced in given path in the result of the function
    """
    return MultipleBackwardsTranslatorRunner(func_call=func_call, path=path, shape=shape, type_=type_,
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
