import contextlib
from abc import ABC, abstractmethod
from typing import List, Any, Optional, Type

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.function_definitions.func_definition import FuncDefinition


class MultipleInstanceRunner(ABC):
    expected_runner_exception: Optional[Type[PyQuibblerException]] = None
    exception_to_raise_on_none_found: Type[PyQuibblerException] = NotImplemented

    def __init__(self, func_definition: FuncDefinition):
        self._func_definition = func_definition

    @abstractmethod
    def _get_runners_from_definition(self, definition: FuncDefinition) -> List:
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
        definition = self._func_definition
        for runner in self._get_runners_from_definition(definition=definition):
            with self.exception_context():
                return self._run_runner(runner)
        raise self.exception_to_raise_on_none_found(self._func_definition.func)


class MultipleFuncCallInstanceRunner(MultipleInstanceRunner, ABC):

    def __init__(self, func_call: FuncCall):
        super().__init__(func_definition=func_call.func_definition)
        self._func_call = func_call
