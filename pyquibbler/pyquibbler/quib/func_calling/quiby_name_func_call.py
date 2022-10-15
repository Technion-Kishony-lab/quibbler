from __future__ import annotations

from typing import Any

from pyquibbler.quib.func_calling.quib_func_call import WholeValueNonGraphicQuibFuncCall


class QuibyNameFuncCall(WholeValueNonGraphicQuibFuncCall):
    """
    Represents a FuncCall that of a quiby_name quib: returning the name of its quib argument.
    """

    def _run(self) -> Any:
        # func is get_quib_name
        return self.func_args_kwargs.func(*self.func_args_kwargs.args, **self.func_args_kwargs.kwargs)
