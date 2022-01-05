from __future__ import annotations
from typing import TYPE_CHECKING


from pyquibbler.refactor.translation.exceptions import NoInvertersFoundException, CannotInvertException
from pyquibbler.refactor.func_call import FuncCall

if TYPE_CHECKING:
    from pyquibbler import Assignment


def invert(func_call: FuncCall, assignment: Assignment, previous_result):
    from pyquibbler.refactor.function_definitions import get_definition_for_function
    definition = get_definition_for_function(func_call.func)

    potential_inverter_classes = list(definition.inverters)
    while True:
        if potential_inverter_classes is None or len(potential_inverter_classes) == 0:
            raise NoInvertersFoundException(func_call.func)
        cls = potential_inverter_classes.pop()
        inverter = cls(
            func_call=func_call,
            assignment=assignment,
            previous_result=previous_result
        )
        try:
            return inverter.get_inversals()
        except CannotInvertException:
            # TODO: don't raise
            pass
