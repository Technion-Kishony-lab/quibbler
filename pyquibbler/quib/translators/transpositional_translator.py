from typing import Callable, Any, Dict, List

import numpy as np

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.translators.translator import Translator
from pyquibbler.quib.utils import recursively_run_func_on_object, call_func_with_quib_values


class TranspositionalPathTranslator(Translator):

    @property
    def _args(self):
        return self._function_quib.args

    @property
    def _func(self):
        return self._function_quib.args

    @property
    def _kwargs(self):
        return self._function_quib.args

    def _get_quibs_which_can_change(self):
        return self._function_quib.get_data_source_quibs()