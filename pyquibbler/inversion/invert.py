from __future__ import annotations
from typing import Callable, Tuple, Any, Mapping, TYPE_CHECKING

from pyquibbler.overriding import get_definition_for_function
from pyquibbler.translation.exceptions import NoInvertersFoundException, CannotInvertException
from pyquibbler.inversion import INVERTERS
from pyquibbler.quib.function_quibs.utils import FuncWithArgsValues

if TYPE_CHECKING:
    from pyquibbler import Assignment


def invert(func: Callable, args: Tuple[Any, ...], kwargs: Mapping[str, Any], assignment: Assignment, previous_result):
    print(f"Inverting func {func}")
    # TODO test multiple scenarios with choosing inverters
    definition = get_definition_for_function(func)
    potential_inverter_classes = list(definition.inverters)
    while True:
        if potential_inverter_classes is None or len(potential_inverter_classes) == 0:
            raise NoInvertersFoundException(func)
        cls = potential_inverter_classes.pop()
        inverter = cls(
            func_with_args_values=FuncWithArgsValues.from_function_call(
                func=func,
                args=args,
                kwargs=kwargs,
                include_defaults=True
            ),
            assignment=assignment,
            previous_result=previous_result
        )
        try:
            return inverter.get_inversals()
        except CannotInvertException:
            # TODO: don't raise
            raise
