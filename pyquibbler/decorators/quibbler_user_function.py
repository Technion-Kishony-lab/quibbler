import functools


from pyquibbler.quib.factory import create_quib


def quibbler_user_function(lazy: bool = False, pass_quibs: bool = False):
    """
    Decorate your function with this in order for quibbler to automatically unpack quibs sent as arguments to this
    function, while reruninng this function every time any argument quib changes.

    Any graphics created in this function will also be redrawn if any argument quib changes.

    :param lazy: Should this function be run immediately (lazy=False), or only when
     it's needed down the line?
    (lazy=False) - if you do any graphics in this function you should probably set lazy=False
    :param pass_quibs: Should this function receive quibs or their values?
    """

    from pyquibbler.function_definitions.func_definition import FuncDefinition

    def _decorator(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            return create_quib(func=func, args=args, kwargs=kwargs, lazy=lazy,
                               function_definition=FuncDefinition(pass_quibs=pass_quibs),
                               )

        return _wrapper

    return _decorator
