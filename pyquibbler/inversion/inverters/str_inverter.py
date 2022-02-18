import warnings

import numpy as np

from pyquibbler import Assignment
from pyquibbler.inversion.inverter import Inverter
from pyquibbler.translation.types import Source, Inversal
from pyquibbler.inversion.exceptions import FailedToInvertException


class StrInverter(Inverter):

    def get_inversals(self):
        if len(self._func_call.args) != 1 \
                or not isinstance(self._func_call.args[0], Source) \
                or len(self._assignment.path) > 0:
            raise FailedToInvertException(self._func_call)

        source_to_change = self._func_call.args[0]

        assignment_path = []

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            source_to_change_type = type(source_to_change.value)
            if source_to_change_type is list or source_to_change_type is np.ndarray:
                value_to_set = eval(self._assignment.value)
                if type(value_to_set) is not list:
                    raise FailedToInvertException(self._func_call)
                if source_to_change_type is np.ndarray:
                    try:
                        value_to_set = np.array(value_to_set)
                    except Exception:
                        raise FailedToInvertException(self._func_call)
            else:
                try:
                    value_to_set = source_to_change_type(self._assignment.value)
                except Exception:
                    raise FailedToInvertException(self._func_call)
        return [
            Inversal(
                source=source_to_change,
                assignment=Assignment(
                    path=assignment_path,
                    value=value_to_set
                )
            )
        ]
