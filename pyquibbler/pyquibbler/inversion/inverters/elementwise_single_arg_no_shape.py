from typing import List

import numpy as np

from pyquibbler.assignment.assignment import create_assignment_from_nominal_down_up_values
from pyquibbler.path_translation.types import Source, Inversal

from .elementwise import BaseUnaryElementWiseInverter


class UnaryElementwiseNoShapeInverter(BaseUnaryElementWiseInverter):
    """
    An inverter of functions like np.exp(quib) = scalar. Simply invert the scalar keep the path unchanged.
    Such assignment are valid even if the shape of the quib changes.
    For example, if
    a = iquib([1, 2, 3])
    b = np.exp2(a)  # -> [2, 4, 8]
    then
    b[:] = 16
    will translate into a[:] = 4 which golds valid even if the shape of a changes
    This can only be done if the function does not depend on the input and when we are assigning
    a scalar (or size=1 array)
    """
    @property
    def source_to_change(self):
        return self._func_call.args[0]

    def can_try(self) -> bool:
        return isinstance(self.source_to_change, Source) \
            and np.size(self._assignment.value) == 1

    def get_inversals(self) -> List[Inversal]:
        inverse_func = self.get_inverse_func_and_raise_if_none(0)
        if inverse_func.requires_previous_input:
            self._raise_run_failed_exception()
        value_nominal_down_up = self._get_assignment_nominal_down_up_values()
        nominal_down_up_values_to_set = [inverse_func.inv_func(value) for value in value_nominal_down_up]
        new_assignment = create_assignment_from_nominal_down_up_values(
            nominal_down_up_values=nominal_down_up_values_to_set,
            path=self._assignment.path)
        return [Inversal(source=self.source_to_change, assignment=new_assignment)]
