from __future__ import annotations

from typing import Any, List, Union

from pyquibbler.path import Path
from pyquibbler.quib.func_calling import WholeValueNonGraphicQuibFuncCall


class IQuibFuncCall(WholeValueNonGraphicQuibFuncCall):
    """
    Represents a FuncCall with identity function applied to a single argument with no quibs.
    No need to cache. Also no graphics.
    """

    @property
    def _value(self):
        return self.func_args_kwargs.get_arg_values_by_position()[0]

    def _run(self, valid_paths: List[Union[None, Path]]) -> Any:
        # func is identity_function, so we this will simply return the "value", which is the first argument:
        return self._value
