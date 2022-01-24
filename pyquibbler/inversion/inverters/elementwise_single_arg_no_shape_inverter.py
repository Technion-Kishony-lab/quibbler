import warnings
from typing import Callable
from pyquibbler import Assignment
from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.inversion.inverter import Inverter
from pyquibbler.translation.types import Source, Inversal
from pyquibbler.inversion.exceptions import FailedToInvertException


class ElementwiseNoShapeInverter(Inverter):

    def __init__(self, func_call: FuncCall, assignment, previous_result, inverse_func: Callable):
        super().__init__(func_call, assignment, previous_result)
        self._inverse_func = inverse_func

    def get_inversals(self):
        if len(self._func_call.args) != 1 \
                or not isinstance(self._func_call.args[0], Source) \
                or len(self._assignment.path) > 1:
            raise FailedToInvertException(self._func_call)

        source_to_change = self._func_call.args[0]

        relevant_path_in_source = self._assignment.path

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            value_to_set = self._inverse_func(self._assignment.value,
                                              self._func_call.args,
                                              self._func_call.kwargs,
                                              source_to_change,
                                              relevant_path_in_source)
        return [
            Inversal(
                source=source_to_change,
                assignment=Assignment(
                    path=relevant_path_in_source,
                    value=value_to_set
                )
            )
        ]
