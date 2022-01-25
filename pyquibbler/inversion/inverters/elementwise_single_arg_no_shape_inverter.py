import warnings
from typing import Callable

import numpy as np

from pyquibbler import Assignment
from pyquibbler.path.path_component import PathComponent
from pyquibbler.path.data_accessing import deep_get
from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.inversion.inverter import Inverter
from pyquibbler.translation.types import Source, Inversal
from pyquibbler.inversion.exceptions import FailedToInvertException


def is_path_component_open_ended(component: PathComponent):
    def is_sub_component_open_ended(sub_component) -> bool:
        return isinstance(sub_component, slice) and ((sub_component.stop is None) or (sub_component.stop < 0))

    component = component.component

    if isinstance(component, tuple):
        return any(map(is_sub_component_open_ended, component))

    return is_sub_component_open_ended(component)


class ElementwiseNoShapeInverter(Inverter):

    def __init__(self, func_call: FuncCall, assignment, previous_result,
                 inverse_func: Callable, raw_inverse_func: Callable):
        super().__init__(func_call, assignment, previous_result)
        self._inverse_func = inverse_func
        self._raw_inverse_func = raw_inverse_func

    def get_inversals(self):
        if len(self._func_call.args) != 1 \
                or not isinstance(self._func_call.args[0], Source) \
                or len(self._assignment.path) > 1:
            raise FailedToInvertException(self._func_call)

        source_to_change = self._func_call.args[0]

        assignment_path = self._assignment.path

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if len(assignment_path) and is_path_component_open_ended(assignment_path[0]) \
                    or np.shape(self._assignment.value) != np.shape(deep_get(self._previous_result, assignment_path)):
                # assignment is open-ended (e.g., quib[:,1] = value, or quib[0:-1] = val), or is broadcasted
                # Under these conditions, if we want to keep the shape of the assigned value, we cannot adjust the
                # value at each element based on the value of the args.
                value_to_set = self._raw_inverse_func(self._assignment.value)
            else:
                source_to_change_at_value_shape = Source(deep_get(source_to_change.value, assignment_path))
                value_to_set = self._inverse_func(self._assignment.value,
                                                  self._func_call.args,
                                                  self._func_call.kwargs,
                                                  source_to_change_at_value_shape,
                                                  assignment_path)
        return [
            Inversal(
                source=source_to_change,
                assignment=Assignment(
                    path=assignment_path,
                    value=value_to_set
                )
            )
        ]
