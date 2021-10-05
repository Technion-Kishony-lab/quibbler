from __future__ import annotations
import math
import numpy as np
from operator import __add__, __pow__, __sub__
from typing import Any, List, Dict, Callable, TYPE_CHECKING

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.utils import call_func_with_quib_values
from ..assignment import QuibWithAssignment, IndicesAssignment

if TYPE_CHECKING:
    from pyquibbler.quib import Quib

from .reverser import Reversal, Reverser
from .utils import create_empty_array_with_values_at_indices


class CommonAncestorBetweenArgumentsException(PyQuibblerException):
    pass


def create_inverse_function_from_indexes_to_funcs(quib_argument_indexes_to_inverse_functions: Dict[int, Callable]):
    """
    Create an inverse function that will call actual inverse functions based on the index of the quib in the arguments
    """

    def _inverse(representative_result: Any, args, kwargs, quib_to_change: Quib):
        quib_index = next(i for i, v in enumerate(args) if v is quib_to_change)
        inverse_func = quib_argument_indexes_to_inverse_functions[quib_index]
        new_args = list(args)
        new_args[quib_index] = representative_result
        return call_func_with_quib_values(inverse_func, new_args, kwargs)

    return _inverse


class ElementWiseReverser(Reverser):
    """
    In charge of reversing all element-wise mathematical operation functions
    """

    # We use indexes instead of arg names because you cannot get signature from ufuncs (numpy functions)
    FUNCTIONS_TO_INVERSE_FUNCTIONS = {
        np.add: create_inverse_function_from_indexes_to_funcs(
            {
                i: np.subtract for i in range(2)
            }
        ),
        __add__: create_inverse_function_from_indexes_to_funcs(
            {
                i: np.subtract for i in range(2)
            }
        ),
        np.multiply: create_inverse_function_from_indexes_to_funcs(
            {
                i: np.divide for i in range(2)
            }
        ),
        np.subtract: create_inverse_function_from_indexes_to_funcs(
            {
                0: np.add,
                1: np.subtract
            }
        ),
        np.divide: create_inverse_function_from_indexes_to_funcs({
            0: np.multiply,
            1: np.divide
        }),
        __pow__: create_inverse_function_from_indexes_to_funcs({
            0: lambda x, n: x ** (1 / n),
            1: lambda x, n: math.log(n, x)
        }),
        __sub__: create_inverse_function_from_indexes_to_funcs(
            {
                0: np.add,
                1: np.subtract
            }
        )
    }

    SUPPORTED_FUNCTIONS = list(FUNCTIONS_TO_INVERSE_FUNCTIONS.keys())

    def _get_indices_to_change(self, argument_quib: Quib) -> Any:
        """
        Get the relevant indices for the argument quib that will need to be changed

        Even though the operation is element wise, this does not necessarily mean that the final results shape is
        the same as the arguments' shape, as their may have been broadcasting. Given this, we take our argument quib
        and broadcast it's index grid to the shape of the result, so we can see the corresponding quib indices for the
        result indices
        """
        if self._indices is None:
            return None
        index_grid = np.indices(argument_quib.get_shape().get_value())
        broadcasted_grid = np.broadcast_to(index_grid,
                                           (index_grid.shape[0], *self._function_quib.get_shape().get_value()))
        return [
            dimension[self._indices]
            for dimension in broadcasted_grid
        ]

    def raise_if_multiple_args_have_common_ancestor(self):
        """
        Raise an exception if we have multiple parents with a common ancestor- we do not know how to solve for x if
        x is on both sides of the equation
        """
        all_ancestors = set()
        for arg in self._get_quibs_in_args():
            from pyquibbler.quib import FunctionQuib
            arg_and_ancestors = {arg}
            if isinstance(arg, FunctionQuib):
                arg_and_ancestors |= arg.ancestors

            if all_ancestors & arg_and_ancestors:
                raise CommonAncestorBetweenArgumentsException()

            all_ancestors |= arg_and_ancestors

    def _create_quibs_with_assignments(self, quib_to_change: Quib, new_value_for_quib: Any):
        """
        Create all quibs with assignments after having calculated which quib to change and new value of quib
        """
        if isinstance(self._assignment, IndicesAssignment):
            changed_indices = self._get_indices_to_change(quib_to_change)

            return [QuibWithAssignment(
                quib=quib_to_change,
                assignment=IndicesAssignment(indices=changed_indices,
                                             value=new_value_for_quib[self._indices],
                                             field=self._assignment.field)
            )]
        return [
            QuibWithAssignment(
                quib=quib_to_change,
                assignment=Assignment(
                    value=new_value_for_quib,
                    field=self._assignment.field
                )
            )
        ]

    def _get_quibs_with_assignments(self) -> List[QuibWithAssignment]:
        self.raise_if_multiple_args_have_common_ancestor()

        quib_to_change = self._get_quibs_in_args()[0]

        inverse_function = self.FUNCTIONS_TO_INVERSE_FUNCTIONS[self._func]
        new_quib_argument_value = inverse_function(self._get_representative_function_quib_result_with_value(),
                                                   self._args,
                                                   self._kwargs,
                                                   quib_to_change)

        return self._create_quibs_with_assignments(quib_to_change=quib_to_change,
                                                   new_value_for_quib=new_quib_argument_value)
