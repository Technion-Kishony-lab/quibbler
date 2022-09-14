from __future__ import annotations

from typing import Any, List, Union

from pyquibbler.path import Path
from pyquibbler.quib.func_calling import QuibFuncCall


class QuibyNameFuncCall(QuibFuncCall):
    """
    Represents a FuncCall with identity function applied to a single argument with no quibs.
    No need to cache. Also no graphics.
    """

    @property
    def created_graphics(self) -> bool:
        return False

    @property
    def func_can_create_graphics(self):
        return False

    def run(self, valid_paths: List[Union[None, Path]]) -> Any:
        # func is get_quib_name
        return self.func_args_kwargs.func(self.func_args_kwargs.get_arg_values_by_position()[0])
