from __future__ import annotations
from typing import TYPE_CHECKING, Any, List

from pyquibbler.function_definitions.function_definition import FunctionDefinition
from pyquibbler.inversion.exceptions import NoInvertersFoundException
from pyquibbler.utilities.multiple_instance_runner import MultipleInstanceRunner
from pyquibbler.function_definitions.func_call import FuncCall

if TYPE_CHECKING:
    from pyquibbler import Assignment


class MultipleInverterRunner(MultipleInstanceRunner):
    exception_to_raise_on_none_found = NoInvertersFoundException

    def __init__(self, func_call: FuncCall, assignment: Assignment, previous_result: Any):
        super().__init__(func_call)
        self._assignment = assignment
        self._previous_result = previous_result

    def _get_runners_from_definition(self, definition: FunctionDefinition) -> List:
        return definition.inverters

    def _run_runner(self, runner: Any):
        inverter = runner(
            func_call=self._func_call,
            assignment=self._assignment,
            previous_result=self._previous_result
        )
        return inverter.get_inversals()


def invert(func_call: FuncCall, assignment: Assignment, previous_result):
    return MultipleInverterRunner(func_call, assignment, previous_result).run()
