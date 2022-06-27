from __future__ import annotations
from typing import Any, List

from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.inversion.exceptions import NoInvertersFoundException, FailedToInvertException
from pyquibbler.path import deep_get
from pyquibbler.translation.source_func_call import SourceFuncCall
from pyquibbler.utilities.multiple_instance_runner import MultipleInstanceRunner

from pyquibbler import Assignment, default


class MultipleInverterRunner(MultipleInstanceRunner):

    exception_to_raise_on_none_found = NoInvertersFoundException
    expected_runner_exception = FailedToInvertException

    def __init__(self, func_call: SourceFuncCall, assignment: Assignment, previous_result: Any):
        super().__init__(func_call)
        self._assignment = assignment
        self._previous_result = previous_result

    def _get_runners_from_definition(self, definition: FuncDefinition) -> List:
        return definition.inverters

    def _run_runner(self, runner: Any):
        inverter = runner(
            func_call=self._func_call,
            assignment=self._assignment,
            previous_result=self._previous_result
        )
        return inverter.get_inversals()


def invert(func_call: SourceFuncCall, assignment: Assignment, previous_result):
    """
    Get all the inversions for a given assignment on the result of a funccall
    """

    is_default = assignment.is_default()
    if is_default:
        actual_assignment = Assignment(value=deep_get(previous_result, assignment.path),
                                       path=assignment.path)
    else:
        actual_assignment = assignment

    inversals = MultipleInverterRunner(func_call, actual_assignment, previous_result).run()

    for inversal in inversals:
        if is_default:
            inversal.assignment.value = default
        else:
            inversal.cast_assigned_value_by_source_value()

    return inversals