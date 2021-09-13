from functools import wraps
from typing import Set, List, Callable, Any, Mapping, Tuple

from .quib import Quib
from .utils import is_there_a_quib_in_args, iter_quibs_in_args, call_func_with_quib_values


class FunctionQuib(Quib):
    """
    An abstract class for quibs that represent the result of a computation.
    """
    MAX_BYTES_PER_SECOND = 2 ** 30
    MIN_SECONDS_FOR_CACHE = 1e-3

    def __init__(self,
                 artists_redrawers: Set,
                 children: List[Quib],
                 func: Callable,
                 args: Tuple[Any, ...],
                 kwargs: Mapping[str, Any]):
        super().__init__(artists_redrawers=artists_redrawers, children=children)
        self._func = func
        self._args = args
        self._kwargs = kwargs

    @classmethod
    def create(cls, func, func_args=(), func_kwargs=None):
        """
        Public constructor for DefaultFunctionQuib.
        """
        if func_kwargs is None:
            func_kwargs = {}
        self = cls(artists_redrawers=set(), children=[], func=func, args=func_args, kwargs=func_kwargs)
        for arg in iter_quibs_in_args(func_args, func_kwargs):
            arg.add_child(self)
        return self

    @classmethod
    def create_wrapper(cls, func):
        @wraps(func)
        def quib_supporting_func_wrapper(*args, **kwargs):
            if is_there_a_quib_in_args(args, kwargs):
                return cls.create(func=func, func_args=args, func_kwargs=kwargs)

            return func(*args, **kwargs)

        return quib_supporting_func_wrapper

    def _call_func(self):
        """
        Call the function wrapped by this FunctionQuib with the
        given arguments after replacing quib with their values.
        """
        return call_func_with_quib_values(self._func, self._args, self._kwargs)
