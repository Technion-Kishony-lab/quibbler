from __future__ import annotations

from typing import Any, List, Union

from pyquibbler.path import Path
from pyquibbler.quib.func_calling import QuibFuncCall


class IQuibFuncCall(QuibFuncCall):
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
        """
        Simply return the value of the argument
        """
        return self.func_args_kwargs[0]
