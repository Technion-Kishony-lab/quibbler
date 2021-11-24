import types

from pyquibbler.quib.refactor.iterators import iter_quibs_in_args
from pyquibbler.quib.refactor.quib import Quib
from pyquibbler.quib.utils import deep_copy_without_quibs_or_graphics


def create_quib(func, args=(), kwargs=None, cache_behavior=None, evaluate_now=False, is_known_graphics_func=False,
                **init_kwargs):
    """
    Public constructor for creating a quib.
    """
    # If we received a function that was already wrapped with a function quib, we want want to unwrap it
    while hasattr(func, '__quib_wrapper__'):
        previous_func = func
        func = func.__wrapped__
        # If it was a bound method we need to recreate it
        if hasattr(previous_func, '__self__'):
            func = types.MethodType(func, previous_func.__self__)

    if kwargs is None:
        kwargs = {}
    kwargs = {k: deep_copy_without_quibs_or_graphics(v) for k, v in kwargs.items()}
    args = deep_copy_without_quibs_or_graphics(args)
    quib = Quib(func=func, args=args, kwargs=kwargs,
                cache_behavior=cache_behavior, assignment_template=None, allow_overriding=False,
                is_known_graphics_func=is_known_graphics_func, **init_kwargs)
    for arg in iter_quibs_in_args(args, kwargs):
        arg.add_child(quib)

    if evaluate_now:
        quib.get_value()

    return quib

