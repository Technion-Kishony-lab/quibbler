import numpy as np
from typing import Callable

from .transpositional_function_quib import TranspositionalFunctionQuib
from ..indices_translator_function_quib import SupportedFunction


class ConcatenateFunctionQuib(TranspositionalFunctionQuib):
    SUPPORTED_FUNCTIONS = {
        np.concatenate: SupportedFunction({0}),
    }

    def _convert_data_sources_in_args(self, convert_data_source: Callable):
        return super()._convert_data_sources_in_args(lambda arg: tuple(convert_data_source(arr) for arr in arg))
