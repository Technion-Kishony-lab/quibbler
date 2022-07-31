import warnings

import numpy as np

from pyquibbler import Assignment
from pyquibbler.translation.source_func_call import SourceFuncCall
from pyquibbler.inversion.inverter import Inverter
from pyquibbler.path.utils import working_component
from pyquibbler.translation.translate import backwards_translate
from pyquibbler.translation.types import Inversal
from pyquibbler.translation.translators.elementwise.generic_inverse_functions import \
    create_inverse_single_arg_func, create_inverse_func_from_indexes_to_funcs


class ElementwiseInverter(Inverter):

    def __init__(self, func_call: SourceFuncCall, assignment, previous_result):
        super().__init__(func_call, assignment, previous_result)

    def get_inversals(self):
        component = working_component(self._assignment.path)
        source_to_change = list(self._func_call.get_data_sources())[0]

        relevant_path_in_source = backwards_translate(func_call=self._func_call,
                                                      shape=np.shape(self._previous_result),
                                                      type_=type(self._previous_result),
                                                      path=self._assignment.path)[source_to_change]

        inverse_func = self._func_call.func_definition.inverse_func_with_input
        with warnings.catch_warnings():

            warnings.simplefilter("ignore")
            if isinstance(inverse_func, dict):
                actual_inverse_func = create_inverse_func_from_indexes_to_funcs(inverse_func)
            else:
                actual_inverse_func = create_inverse_single_arg_func(inverse_func)

            new_quib_argument_value = actual_inverse_func(self._get_result_with_assignment_set(),
                                                          self._func_call.args,
                                                          self._func_call.kwargs,
                                                          source_to_change,
                                                          relevant_path_in_source)
        value_to_set = new_quib_argument_value \
            if component is True \
            else new_quib_argument_value[component]
        return [
            Inversal(
                source=source_to_change,
                assignment=Assignment(
                    path=relevant_path_in_source,
                    value=value_to_set
                )
            )
        ]
