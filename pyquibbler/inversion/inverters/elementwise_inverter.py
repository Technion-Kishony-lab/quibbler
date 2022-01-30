import warnings
from dataclasses import dataclass

import numpy as np

from pyquibbler import Assignment
from pyquibbler.env import ASSIGNMENT_RESTRICTIONS
from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.inversion.inverter import Inverter
from pyquibbler.path.utils import working_component
from pyquibbler.utilities.iterators import iter_objects_of_type_in_object_shallowly
from pyquibbler.translation.translate import backwards_translate
from pyquibbler.translation.types import Source, Inversal
from pyquibbler.translation.translators.elementwise.generic_inverse_functions import \
    create_inverse_single_arg_func, create_inverse_func_from_indexes_to_funcs


@dataclass
class CannotReverseException(PyQuibblerException):
    source: Source
    assignment: Assignment


class CommonAncestorBetweenArgumentsException(CannotReverseException):
    pass


class ElementwiseInverter(Inverter):

    def __init__(self, func_call: FuncCall, assignment, previous_result):
        super().__init__(func_call, assignment, previous_result)
        self._inverse_func = func_call.get_func_definition().inverse_func_with_input

    def raise_if_multiple_args_have_common_ancestor(self):
        """
        Raise an exception if we have multiple parents with a common ancestor- we do not know how to solve for x if
        x is on both sides of the equation
        """
        all_ancestors = set()
        for arg in iter_objects_of_type_in_object_shallowly(Source, self._func_call.args):
            arg_and_ancestors = {arg}
            from pyquibbler.quib import Quib
            if isinstance(arg, Quib):
                arg_and_ancestors |= arg.ancestors

            if all_ancestors & arg_and_ancestors:
                raise CommonAncestorBetweenArgumentsException(self, None)

            all_ancestors |= arg_and_ancestors

    def get_inversals(self):
        if ASSIGNMENT_RESTRICTIONS:
            self.raise_if_multiple_args_have_common_ancestor()

        component = working_component(self._assignment.path)
        source_to_change = list(self._func_call.get_data_sources())[0]

        relevant_path_in_source = backwards_translate(func_call=self._func_call,
                                                      shape=np.shape(self._previous_result),
                                                      type_=type(self._previous_result),
                                                      path=self._assignment.path)[source_to_change]

        with warnings.catch_warnings():

            warnings.simplefilter("ignore")
            if isinstance(self._inverse_func, dict):
                actual_inverse_func = create_inverse_func_from_indexes_to_funcs(self._inverse_func)
            else:
                actual_inverse_func = create_inverse_single_arg_func(self._inverse_func)

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
