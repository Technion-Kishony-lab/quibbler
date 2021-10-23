from __future__ import annotations

import math
from operator import __neg__, __pos__, __sub__, __pow__, __mul__, __add__

import numpy as np
from typing import TYPE_CHECKING, Any, List

from pyquibbler.quib.assignment.inverse_assignment import ElementWiseInverter

from .default_function_quib import DefaultFunctionQuib
from .indices_translator_function_quib import IndicesTranslatorFunctionQuib
from ..assignment.assignment import get_working_component_value_from_path
from ..assignment.inverse_assignment.exceptions import CommonAncestorBetweenArgumentsException
from ..assignment.inverse_assignment.utils import create_empty_array_with_values_at_indices
from ..utils import call_func_with_quib_values, iter_quibs_in_object_recursively

from pyquibbler.quib.assignment import Assignment, PathComponent
from ...env import ASSIGNMENT_RESTRICTIONS

if TYPE_CHECKING:
    from pyquibbler.quib import Quib


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


class ElementWiseFunctionQuib(DefaultFunctionQuib, IndicesTranslatorFunctionQuib):
    """
    A quib representing an element wise mathematical operation- this includes any op that can map an output element
    back to an input element, and the operation can be inversed per element
    """

    identity = lambda x: x
    # We use indexes instead of arg names because you cannot get signature from ufuncs (numpy functions)
    FUNCTIONS_TO_INVERSE_FUNCTIONS = {
        **{
            func: create_inverse_func_from_indexes_to_funcs(
                {
                    0: np.subtract,
                    1: np.subtract
                }
            ) for func in [np.add, __add__]},
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
            for func, invfunc in
            [
                (__neg__, __neg__),
                (__pos__, __pos__),
                (np.sin, np.arcsin),
                (np.cos, np.arccos),
                (np.tan, np.arctan),
                (np.sinh, np.arcsinh),
                (np.cosh, np.arccosh),
                (np.tanh, np.arctanh),
                (np.arcsin, np.sin),
                (np.arccos, np.cos),
                (np.arctan, np.tan),
                (np.arcsinh, np.sinh),
                (np.arccosh, np.cosh),
                (np.arctanh, np.tanh),
                (np.ceil, identity),
                (np.floor, identity),
                (np.round, identity),
                (np.exp, np.log),
                (np.exp2, np.log2),
                (np.expm1, np.log1p),
                (np.log, np.exp),
                (np.log2, np.exp2),
                (np.log1p, np.expm1),
                (np.log10, lambda x: 10 ** x),
                (np.sqrt, np.square),
                (np.square, np.sqrt),
                (np.int, identity),
                (np.float, identity),
            ]
        },
    }

    SUPPORTED_FUNCTIONS = None

    def _forward_translate_indices_to_bool_mask(self, quib: Quib, indices: Any) -> Any:
        """
        # TODO change comment
        Create a boolean mask representing the quib at certain indices in the result.
        For a simple operation (eg `invalidator=[1, 2, 3]`, `invalidator + [2, 3, 4]`, and we invalidate `(0, 0)`),
        the `True`'s will be in the location of the indices (`[True, False, False]`)- but if
        the invalidator quib was broadcasted, we need to make sure we get a boolean mask representing where the indices
        were in the entire result.

        For example- if we have
        ```
        quib = [[1, 2, 3]]
        sum_ = quib + [[1], [2], [3]]
        ```
        and we invalidate at (0, 0), we need to create a mask broadcasted like the argument was, ie
        [[True, False, False],
         [True, False, False],
         [True, False, False]]
        """
        bool_mask = self._get_source_shaped_bool_mask(quib, indices)
        return np.broadcast_to(bool_mask, self.get_shape().get_value())

    def raise_if_multiple_args_have_common_ancestor(self):
        """
        Raise an exception if we have multiple parents with a common ancestor- we do not know how to solve for x if
        x is on both sides of the equation
        """
        all_ancestors = set()
        for arg in iter_quibs_in_object_recursively(self._args):
            from pyquibbler.quib import FunctionQuib
            arg_and_ancestors = {arg}
            if isinstance(arg, FunctionQuib):
                arg_and_ancestors |= arg.ancestors

            if all_ancestors & arg_and_ancestors:
                raise CommonAncestorBetweenArgumentsException(self, None)

            all_ancestors |= arg_and_ancestors

    def _get_indices_to_change(self, argument_quib: Quib, working_indices) -> Any:
        """
        Get the relevant indices for the argument quib that will need to be changed

        Even though the operation is element wise, this does not necessarily mean that the final results shape is
        the same as the arguments' shape, as their may have been broadcasting. Given this, we take our argument quib
        and broadcast it's index grid to the shape of the result, so we can see the corresponding quib indices for the
        result indices
        """
        index_grid = np.indices(argument_quib.get_shape().get_value())
        broadcasted_grid = np.broadcast_to(index_grid,
                                           (index_grid.shape[0], *self.get_shape().get_value()))
        return tuple([
            dimension[working_indices]
            for dimension in broadcasted_grid
        ])

    def _get_quibs_to_paths_in_result(self, filtered_path_in_result):
        quib_to_change = self._get_quibs_in_args()[0]
        changed_indices = self._get_indices_to_change(quib_to_change,
                                                      get_working_component_value_from_path(filtered_path_in_result))

        if len(changed_indices) == 0:
            new_path = []
        else:
            new_path = [PathComponent(indexed_cls=self.get_type(), component=changed_indices)]

        return {
            quib_to_change: new_path
        }

    def _get_quibs_in_args(self) -> List[Quib]:
        """
        Gets a list of all unique quibs in the args of self._function_quib
        """
        quibs = []
        for quib in iter_quibs_in_object_recursively(self._args):
            if quib not in quibs:
                quibs.append(quib)

        return quibs

    def _get_quibs_to_relevant_result_values(self, assignment: Assignment):
        if ASSIGNMENT_RESTRICTIONS:
            self.raise_if_multiple_args_have_common_ancestor()

        working_component = get_working_component_value_from_path(assignment.path)
        quib_to_change = self._get_quibs_in_args()[0]

        inverse_function = self.FUNCTIONS_TO_INVERSE_FUNCTIONS[self._func]
        new_quib_argument_value = inverse_function(self._get_representative_result(working_component, assignment.value),
                                                   self._args,
                                                   self._kwargs,
                                                   quib_to_change)
        value_to_set = new_quib_argument_value \
            if working_component is True \
            else new_quib_argument_value[working_component]
        return {
            quib_to_change: value_to_set
        }
