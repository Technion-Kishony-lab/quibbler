from __future__ import annotations
from typing import List

from pyquibbler.assignment import Assignment, default
from pyquibbler.path.data_accessing import deep_get
from pyquibbler.path_translation.source_func_call import SourceFuncCall
from pyquibbler.path_translation.types import Inversal
from pyquibbler.utilities.multiple_instance_runner import MultipleInstanceRunner


def invert(func_call: SourceFuncCall, assignment: Assignment, previous_result) -> List[Inversal]:
    """
    Get all the inversions for a given assignment on the result of a funccall
    """

    is_default = assignment.is_default()
    if is_default:
        actual_assignment = Assignment(value=deep_get(previous_result, assignment.path),
                                       path=assignment.path)
    else:
        actual_assignment = assignment

    inversals = MultipleInstanceRunner(run_condition=None, runner_types=func_call.func_definition.inverters,
                                       func_call=func_call, assignment=actual_assignment,
                                       previous_result=previous_result).run()

    for inversal in inversals:
        if is_default:
            inversal.assignment.value = default
        else:
            inversal.cast_assigned_value_by_source_value()

    return inversals
