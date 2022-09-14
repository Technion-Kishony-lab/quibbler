from __future__ import annotations

from typing import Any

from pyquibbler.quib.func_calling.quib_func_call import WholeValueNonGraphicQuibFuncCall


class QuibyNameFuncCall(WholeValueNonGraphicQuibFuncCall):
    """
    Represents a FuncCall with identity function applied to a single argument with no quibs.
    No need to cache. Also no graphics.
    """

    def _run(self) -> Any:
        # func is get_quib_name
        return self.func_args_kwargs.func(self.func_args_kwargs.get_arg_values_by_position()[0])
