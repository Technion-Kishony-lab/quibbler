from pyquibbler.project import Project
from pyquibbler.quib import GraphicsFunctionQuib
from pyquibbler.quib import DefaultFunctionQuib


def q(func, *args, **kwargs):
    """
    Creates a function quib from the given function call.
    """
    # In case the given function is already a wrapper for a specific quib type, we use it.
    quib_type = getattr(func, '__quib_wrapper__', DefaultFunctionQuib)
    return quib_type.create(func=func, func_args=args, func_kwargs=kwargs)


def q_graphics(func, *args, **kwargs):
    """
    Creates a graphical function quib from the given function call.
    """
    # In case the given function is already a wrapper for a specific quib type, we use it.
    quib_type = getattr(func, '__quib_wrapper__', GraphicsFunctionQuib)
    return quib_type.create(func=func, func_args=args, func_kwargs=kwargs)


def reset_impure_function_quibs():
    """
    Resets all impure function quib caches and invalidates and redraws with them- note that this does NOT necessarily
    mean they will run
    """
    Project.get_or_create().reset_invalidate_and_redraw_all_impure_function_quibs()
