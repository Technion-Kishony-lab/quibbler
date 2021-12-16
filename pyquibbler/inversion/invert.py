from __future__ import annotations
from typing import Callable, Tuple, Any, Mapping, TYPE_CHECKING

from pyquibbler.translation.exceptions import NoInvertersFoundException, CannotInvertException
from pyquibbler.inversion import INVERTERS
from pyquibbler.quib.function_quibs.utils import FuncWithArgsValues

if TYPE_CHECKING:
    from pyquibbler import Assignment


def invert(func: Callable, args: Tuple[Any, ...], kwargs: Mapping[str, Any], assignment: Assignment, previous_result):
    print(f"Inverting func {func}")
    # TODO test multiple scenarios with choosing inverters
    potential_inverter_classes = [cls for cls in INVERTERS if func in cls.SUPPORTING_FUNCS]
    potential_inverter_classes = list(sorted(potential_inverter_classes, key=lambda c: c.PRIORITY))
    if len(potential_inverter_classes) == 0:
        raise NoInvertersFoundException(func)
    while True:
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
            pass
