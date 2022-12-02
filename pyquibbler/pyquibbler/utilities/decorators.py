import functools
from typing import Callable, Optional


def ensure_only_run_once_globally(func: Callable):
    """
    Decorator to ensure the function is only run once (globally)
    This does not raise an exception if the function is called twice
    """
    did_run = False

    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        nonlocal did_run
        if not did_run:
            res = func(*args, **kwargs)
            did_run = True
            return res

    return _wrapper


def assign_func_name(name: str):
    """
    Assign the __name__ property of a function.
    """

    def _assign(func):
        func.__name__ = name
        return func

    return _assign


def squash_recursive_calls(prevent_squash: Optional[Callable]):
    """
    When the function is running, additional calls to the function
    are squashed, so that when the run is completed only the last pending
    call is executed.
    """

    def decorator(func: Callable):
        pending_args = None
        pending_kwargs = None

        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            if prevent_squash and prevent_squash(args, kwargs):
                return func(*args, **kwargs)

            nonlocal pending_args, pending_kwargs
            already_running = pending_args is not None
            pending_args, pending_kwargs = args, kwargs

            if already_running:
                return

            while pending_args is not None:
                args = pending_args
                kwargs = pending_kwargs
                func(*args, **kwargs)
                if pending_args is args and pending_kwargs is pending_kwargs:
                    pending_args = None
                    pending_kwargs = None

        return _wrapper

    return decorator
