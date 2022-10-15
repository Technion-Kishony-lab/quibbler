from typing import Any

import numpy as np
import pytest

from pyquibbler import create_quib
from pyquibbler.function_definitions import FuncArgsKwargs
from pyquibbler.function_definitions.func_definition import create_func_definition
from pyquibbler.quib.func_calling import QuibFuncCall
from pyquibbler.quib.quib import QuibHandler, Quib


class NoRunQuibFuncCall(QuibFuncCall):
    def run(self, *args, **kwargs) -> Any:
        assert False

    def _calculate_type(self):
        self.result_type = type(self.func_args_kwargs.args[0])


class NoRunNoTypeQuibFuncCall(NoRunQuibFuncCall):
    def _calculate_type(self):
        assert False


def create_type_only_quib(arg):
    return Quib(quib_function_call=NoRunQuibFuncCall(func_args_kwargs=FuncArgsKwargs(None, (arg,), {}),
                func_definition=create_func_definition()))


no_value_or_shape_quib = Quib(quib_function_call=NoRunQuibFuncCall(), func_definition=create_func_definition())


@pytest.mark.parametrize("func, args, expected_type", [
    [np.array, (no_value_or_shape_quib, ), np.ndarray],
    [int, (no_value_or_shape_quib,), int],
    [np.ravel, (no_value_or_shape_quib,), np.ndarray],
    [np.sin, (7,), np.float64],
    [np.sin, ([7],), np.ndarray],
    [np.sin, ([no_value_or_shape_quib],), np.ndarray],
])
def test_quib_can_know_its_type_without_getting_the_value_or_type_of_its_arguments(func, args, expected_type):
    quib = create_quib(func=func, args=args)
    type_ = quib.get_type()

    assert type_ == expected_type


@pytest.mark.parametrize("func, args_values, expected_type", [
    [np.sin, ([7],), np.ndarray],
    [np.sin, (7,), np.float64],
])
def test_quib_can_know_its_type_getting_only_the_type_of_its_quib_arguments(func, args_values, expected_type):
    args = [create_type_only_quib(arg_value) for arg_value in args_values]
    quib = create_quib(func=func, args=args)
    type_ = quib.get_type()

    assert type_ == expected_type
