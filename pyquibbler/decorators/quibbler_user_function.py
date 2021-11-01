import functools

from pyquibbler.quib.graphics import GraphicsFunctionQuib


def quibbler_user_function(lazy=True, receive_quibs=False):
    """
    Decorate your function with this in order for quibbler to automatically unpack quibs sent as arguments to this
    function, while reruninng this function every time any argument quib changes.

    Any graphics created in this function will also be redrawn if any argument quib changes.

    :param lazy: Should this function be run immediately (lazy=False), or only when it's needed down the line?
    (lazy=False) - if you do any graphics in this function you should probably set lazy=False
    :param receive_quibs: Should this function receive quibs or their values?
    """
    def _decorator(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            return GraphicsFunctionQuib.create(func=func, func_args=args, func_kwargs=kwargs, lazy=lazy,
                                               receive_quibs=receive_quibs)

        return _wrapper
    return _decorator
