from typing import Union

import numpy as np

from pyquibbler.function_definitions.func_call import ArgsValues
from pyquibbler.function_definitions.function_definition import FunctionDefinition
from pyquibbler.function_overriding.function_override import FunctionOverride
from pyquibbler.quib.function_calling.func_calls.vectorize.vectorize_function_runner \
    import VectorizeQuibFuncCall
from pyquibbler.quib.graphics import UpdateType
from pyquibbler.env import PRETTY_REPR
from pyquibbler.translation.translators.vectorize_translator import VectorizeForwardsPathTranslator, \
    VectorizeBackwardsPathTranslator


class VectorizeOverride(FunctionOverride):

    def _create_quib_supporting_func(self):
        QVectorize.__quibbler_wrapped__ = self.original_func
        return QVectorize


class VectorizeCallDefinition(FunctionDefinition):

    def get_data_source_argument_values(self, args_values: ArgsValues):
        """
        Given a call to a vectorized function, return the arguments which act as data sources.
        We are using args_values.args and args_values.kwargs instead of the full args dict on purpose,
        to match vectorize function behavior.
        """
        from pyquibbler.quib.function_calling.func_calls.vectorize.utils import iter_arg_ids_and_values
        vectorize, *args = args_values.args
        return [val
                for key, val in iter_arg_ids_and_values(args, args_values.kwargs) if key not in vectorize.excluded]


class VectorizeCallOverride(FunctionOverride):

    def _get_creation_flags(self, args, kwargs):
        vectorize, *_ = args
        return {
            'evaluate_now': vectorize.evaluate_now,
            'call_func_with_quibs': vectorize.pass_quibs,
            'update_type': vectorize.update_type
        }


class QVectorize(np.vectorize):
    """
    A small wrapper to the np.vectorize class, adding options to __init__ and wrapping __call__
    with a quib function wrapper.
    """

    def __init__(self, *args, pass_quibs=False, update_type: Union[str, UpdateType] = None,
                 evaluate_now: bool = None, signature=None, cache=False, **kwargs):
        # We don't need the underlying vectorize object to cache, we are doing that ourselves.
        super().__init__(*args, signature=signature, cache=False, **kwargs)
        self.pass_quibs = pass_quibs
        self.update_type = update_type or UpdateType.DRAG
        self.evaluate_now = evaluate_now or False

    def __repr__(self):
        if PRETTY_REPR:
            return f"np.vectorize({self.pyfunc.__name__}{'' if self.signature is None else ', ' + self.signature})"
        return f"<{self.__class__.__name__} {self.signature}>"


def create_vectorize_overrides():
    return [
        VectorizeOverride(func_name="vectorize", module_or_cls=np),
        VectorizeCallOverride(func_name="__call__", module_or_cls=QVectorize,
                              function_definition=VectorizeCallDefinition(
                                  function_runner_cls=VectorizeQuibFuncCall,
                                  forwards_path_translators=[VectorizeForwardsPathTranslator],
                                  backwards_path_translators=[VectorizeBackwardsPathTranslator]
                              )
                              )
    ]
