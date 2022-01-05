from functools import wraps

from typing import Callable

from pyquibbler.refactor.quib.quib_ref import QuibRef


def quib_method(func: Callable) -> Callable:
    """
    A decorator for methods of Quib classes that should return quibs that depend on self.
    For example:
    ```
    Class ExampleQuib(Quib):
        @quib_method
        def method(self, some_quib_val):
            return 1

    example_quib = ExampleQuib()
    # This will return a quib that depends both on example_quib and on some_quib.
    example_quib.method(some_quib)
    ```
    """

    @wraps(func)
    def quib_supporting_method_wrapper(self, *args, **kwargs):
        from pyquibbler.refactor.quib.factory import create_quib
        args = (QuibRef(self), *args)
        return create_quib(func=func, args=args, kwargs=kwargs)

    return quib_supporting_method_wrapper

