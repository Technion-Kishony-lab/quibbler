from __future__ import annotations
import weakref
from _weakref import ReferenceType
from pathlib import Path
import sys
from typing import Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from pyquibbler.quib import Quib


class Project:

    current_project = None

    def __init__(self, path: Optional[Path], quib_weakrefs: Set[ReferenceType[Quib]]):
        self._path = path
        self._quib_weakrefs = quib_weakrefs

    @classmethod
    def get_or_create(cls):
        if cls.current_project is None:
            main_module = sys.modules['__main__']
            path = Path(main_module.__file__) if hasattr(main_module, '__file__') else None
            cls.current_project = cls(path=path, quib_weakrefs=set())
        return cls.current_project

    @property
    def quibs(self):
        refs_to_remove = set()
        for quib_weakref in self._quib_weakrefs:
            if quib_weakref() is None:
                refs_to_remove.add(quib_weakref)
        for ref in refs_to_remove:
            self._quib_weakrefs.remove(ref)

        return [quib_weakref() for quib_weakref in self._quib_weakrefs]

    def register_quib(self, quib: Quib):
        self._quib_weakrefs.add(weakref.ref(quib))

    def reset_invalidate_and_redraw_all_impure_function_quibs(self):
        from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode
        from pyquibbler.quib import ImpureFunctionQuib
        impure_function_quibs = [quib for quib in self.quibs if isinstance(quib, ImpureFunctionQuib)]
        with aggregate_redraw_mode():
            for function_quib in impure_function_quibs:
                function_quib.reset_cache()
                function_quib.invalidate_and_redraw_at_path([])
