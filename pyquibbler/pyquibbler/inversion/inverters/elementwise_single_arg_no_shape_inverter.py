import numpy as np

from pyquibbler.assignment import Assignment
from pyquibbler.translation.types import Source, Inversal
from .elementwise_inverter import BaseUnaryElementWiseInverter


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

    def can_inverse(self):
        return isinstance(self.source_to_change, Source) \
            and np.size(self._assignment.value) == 1 \
            and not self.inverse_func_requires_input

    def get_inversals(self):
        if not self.can_inverse():
            raise self._raise_faile_to_invert_exception()
        value = self._assignment.value
        value_to_set = self.inverse_func(value)
        return [
            Inversal(
                source=self.source_to_change,
                assignment=Assignment(
                    path=self._assignment.path,
                    value=value_to_set
                )
            )
        ]
