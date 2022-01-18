import warnings
from dataclasses import dataclass

import numpy as np
from typing import Callable

from pyquibbler import Assignment
from pyquibbler.env import ASSIGNMENT_RESTRICTIONS
from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.inversion.inverter import Inverter
from pyquibbler.path.utils import working_component
from pyquibbler.utilities.iterators import iter_objects_of_type_in_object_shallowly, \
    iter_objects_of_type_in_object_recursively
from pyquibbler.translation.translate import backwards_translate
from pyquibbler.translation.types import Source, Inversal


@dataclass
class CannotReverseException(PyQuibblerException):
    source: Source
    assignment: Assignment


class CommonAncestorBetweenArgumentsException(CannotReverseException):
    pass


class ElementwiseInverter(Inverter):

    def __init__(self, func_call: FuncCall, assignment, previous_result, inverse_func: Callable):
        super().__init__(func_call, assignment, previous_result)
        self._inverse_func = inverse_func

    def raise_if_multiple_args_have_common_ancestor(self):
        """
        Raise an exception if we have multiple parents with a common ancestor- we do not know how to solve for x if
        x is on both sides of the equation
        """
        all_ancestors = set()
        for arg in iter_objects_of_type_in_object_recursively(Source, self._func_call.args):
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
        source_to_change = list(iter_objects_of_type_in_object_shallowly(Source,
                                                                         self._func_call.get_data_source_argument_values()))[0]

        relevant_path_in_source = backwards_translate(func_call=self._func_call,
                                                      shape=np.shape(self._previous_result),
                                                      type_=type(self._previous_result),
                                                      path=self._assignment.path)[source_to_change]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            new_quib_argument_value = self._inverse_func(self._get_result_with_assignment_set(),
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