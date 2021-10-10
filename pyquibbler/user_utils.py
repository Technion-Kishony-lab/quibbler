from pyquibbler.quib import GraphicsFunctionQuib


def q(func, *args, **kwargs):
    """
    Creates a function quib from the given function call.
    """
    # In case the given function is already a wrapper for a specific quib type, we use it.
    quib_type = getattr(func, '__quib_wrapper__', GraphicsFunctionQuib)
    return quib_type.create(func=func, func_args=args, func_kwargs=kwargs)
