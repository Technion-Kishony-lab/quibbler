import contextlib
from abc import ABC, abstractmethod
from typing import List, Any, Callable, Optional, Type

from pyquibbler.refactor.function_definitions import CannotFindDefinitionForFunctionException
from pyquibbler.refactor.function_definitions.func_call import FuncCall
from pyquibbler.refactor.function_definitions.function_definition import FunctionDefinition


class MultipleInstanceRunner(ABC):
    expected_runner_exception: Optional[Type[Exception]] = None
    exception_to_raise_on_none_found: Type[Exception] = NotImplemented

    def __init__(self, func_call: FuncCall):
        self._func_call = func_call

    def _get_definition(self):
        try:
            return self._func_call.get_func_definition()
        except CannotFindDefinitionForFunctionException:
            raise self.exception_to_raise_on_none_found(self._func_call.func)

    @abstractmethod
    def _get_runners_from_definition(self, definition: FunctionDefinition) -> List:
        pass

    @abstractmethod
    def _run_runner(self, runner: Any):
        pass

    @contextlib.contextmanager
    def exception_context(self):
        if self.expected_runner_exception is not None:
            try:
                yield
            except self.expected_runner_exception:
                pass
        else:
            yield

    def run(self):
        try:
            definition = self._get_definition()
        except CannotFindDefinitionForFunctionException:
            raise self.exception_to_raise_on_none_found(self._func_call.func)

        runners = list(self._get_runners_from_definition(definition=definition))
        while True:
            if len(runners) == 0:
                raise self.exception_to_raise_on_none_found(self._func_call.func)
            runner = runners.pop()
            with self.exception_context():
                return self._run_runner(runner)
