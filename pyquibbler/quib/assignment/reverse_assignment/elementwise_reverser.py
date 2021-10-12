from __future__ import annotations
import math
import numpy as np
from operator import __add__, __pow__, __sub__, __mul__
from typing import Any, List, Dict, Callable, TYPE_CHECKING

from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.utils import call_func_with_quib_values

from .exceptions import CommonAncestorBetweenArgumentsException
from ..assignment import QuibWithAssignment, PathComponent

if TYPE_CHECKING:
    from pyquibbler.quib import Quib

from .reverser import Reverser


def create_inverse_func_from_indexes_to_funcs(quib_argument_indexes_to_inverse_functions: Dict[int, Callable]):
    """
    Create an inverse function that will call actual inverse functions based on the index of the quib in the arguments
    """

    def _inverse(representative_result: Any, args, kwargs, quib_to_change: Quib):
        quib_index = next(i for i, v in enumerate(args) if v is quib_to_change)
        inverse_func = quib_argument_indexes_to_inverse_functions[quib_index]
        new_args = list(args)
        new_args.pop(quib_index)
        return call_func_with_quib_values(inverse_func, [representative_result, *new_args], kwargs)

    return _inverse


class ElementWiseReverser(Reverser):
    """
    In charge of reversing all element-wise mathematical operation functions
    """

    identity = lambda x : x
    # We use indexes instead of arg names because you cannot get signature from ufuncs (numpy functions)
    FUNCTIONS_TO_INVERSE_FUNCTIONS = {
        **{
            func: create_inverse_func_from_indexes_to_funcs(
                {
                    0: np.subtract,
                    1: np.subtract
                }
            ) for func in [__add__, np.add]},
        **{
            func: create_inverse_func_from_indexes_to_funcs(
                {
                    0: np.divide,
                    1: np.divide
                }
            ) for func in [np.multiply, __mul__]},
        **{
            func: create_inverse_func_from_indexes_to_funcs(
                {
                    0: np.add,
                    1: lambda result, other: np.subtract(other, result)
                }
            ) for func in [np.subtract, __sub__]},
        np.divide: create_inverse_func_from_indexes_to_funcs({
            0: np.multiply,
            1: lambda result, other: np.divide(other, result)
        }),
        __pow__: create_inverse_func_from_indexes_to_funcs({
            0: lambda x, n: x ** (1 / n),
            1: lambda result, other: math.log(result, other)
        }),
        **{
            func: create_inverse_func_from_indexes_to_funcs({0: invfunc})
            for func,invfunc in
            [
                (np.sin,        np.arcsin),
                (np.cos,        np.arccos),
                (np.tan,        np.arctan),
                (np.sinh,       np.arcsinh),
                (np.cosh,       np.arccosh),
                (np.tanh,       np.arctanh),
                (np.arcsin,     np.sin),
                (np.arccos,     np.cos),
                (np.arctan,     np.tan),
                (np.arcsinh,    np.sinh),
                (np.arccosh,    np.cosh),
                (np.arctanh,    np.tanh),
                (np.ceil,       identity),
                (np.floor,      identity),
                (np.round,      identity),
                (np.exp,        np.log),
                (np.exp2,       np.log2),
                (np.expm1,      np.log1p),
                (np.log,        np.exp),
                (np.log2,       np.exp2),
                (np.log1p,      np.expm1),
                (np.log10,      lambda x: 10 ** x),
                (np.sqrt,       np.square),
                (np.square,     np.sqrt),
                (np.int,        identity),
                (np.float,      identity),
            ]
        },
    }

    def _get_indices_to_change(self, argument_quib: Quib) -> Any:
        """
        Get the relevant indices for the argument quib that will need to be changed

        Even though the operation is element wise, this does not necessarily mean that the final results shape is
        the same as the arguments' shape, as their may have been broadcasting. Given this, we take our argument quib
        and broadcast it's index grid to the shape of the result, so we can see the corresponding quib indices for the
        result indices
        """
        index_grid = np.indices(argument_quib.get_shape().get_value())
        broadcasted_grid = np.broadcast_to(index_grid,
                                           (index_grid.shape[0], *self._function_quib.get_shape().get_value()))
        return tuple([
            dimension[self._working_indices]
            for dimension in broadcasted_grid
        ])

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
                raise CommonAncestorBetweenArgumentsException(self._function_quib, self._assignment)

            all_ancestors |= arg_and_ancestors

    def _create_quibs_with_assignments(self, quib_to_change: Quib, new_value_for_quib: Any):
        """
        Create all quibs with assignments after having calculated which quib to change and new value of quib
        """
        changed_indices = self._get_indices_to_change(quib_to_change)
        if len(changed_indices) == 0:
            changed_indices = ...

        # We can't subscribe with ellipsis on `new_value_for_quib` because it might not be a numpy type
        value_to_set = new_value_for_quib if self._working_indices is ... else new_value_for_quib[self._working_indices]

        return [QuibWithAssignment(
            quib=quib_to_change,
            assignment=Assignment(path=[PathComponent(indexed_cls=self._function_quib.get_type(),
                                                      component=changed_indices)],
                                  value=value_to_set)
        )]

    def get_reversed_quibs_with_assignments(self) -> List[QuibWithAssignment]:
        self.raise_if_multiple_args_have_common_ancestor()

        quib_to_change = self._get_quibs_in_args()[0]

        inverse_function = self.FUNCTIONS_TO_INVERSE_FUNCTIONS[self._func]
        new_quib_argument_value = inverse_function(self._get_representative_function_quib_result_with_value(),
                                                   self._args,
                                                   self._kwargs,
                                                   quib_to_change)
        return self._create_quibs_with_assignments(quib_to_change=quib_to_change,
                                                   new_value_for_quib=new_quib_argument_value)
