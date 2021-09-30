import functools

from pyquibbler.quib.graphics import GraphicsFunctionQuib


def quibbler_user_function(lazy=True):
    """
    Decorate your function with this in order for quibbler to automatically unpack quibs sent as arguments to this
    function, while reruninng this function every time any argument quib changes.

    Any graphics created in this function will also be redrawn if any argument quib changes.

    :param lazy: Should this function be run immediately (lazy=False), or only when it's needed down the line?
    (lazy=False) - if you do any graphics in this function you should probably set lazy=False
    """
    def _decorator(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            quib = GraphicsFunctionQuib.create(func=func, func_args=args, func_kwargs=kwargs, lazy=lazy)
            if not lazy:
                quib.get_value()
            return quib
        return _wrapper
    return _decorator
