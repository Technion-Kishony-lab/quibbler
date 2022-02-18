import warnings

import numpy as np

from pyquibbler import Assignment
from pyquibbler.path.path_component import PathComponent
from pyquibbler.path.data_accessing import deep_get
from pyquibbler.translation.source_func_call import SourceFuncCall
from pyquibbler.inversion.inverter import Inverter
from pyquibbler.translation.types import Source, Inversal
from pyquibbler.inversion.exceptions import FailedToInvertException
from pyquibbler.translation.translators.elementwise.generic_inverse_functions import \
    create_inverse_single_arg_func


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
            if source_to_change_type is list:
                value_to_set = eval(self._assignment.value)
                if type(value_to_set) is not list:
                    raise FailedToInvertException(self._func_call)
            else:
                try:
                    value_to_set = source_to_change_type(self._assignment.value)
                except:
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
