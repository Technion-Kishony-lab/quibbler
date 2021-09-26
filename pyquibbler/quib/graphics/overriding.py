from matplotlib import pyplot as plt

from pyquibbler.quib.graphics import global_collecting, GraphicsFunctionQuib
from pyquibbler.quib.utils import iter_quibs_in_args, call_func_with_quib_values, is_there_a_quib_in_args
from pyquibbler.utils import ensure_only_run_once_globally


def override_axes_method(method_name: str):
    """
    Override an axes method to create a method that will add an artistsredrawer to any quibs in the arguments

    :param method_name - name of axes method
    """
    cls = plt.Axes
    original_method = getattr(cls, method_name)

    def override(*args, **kwargs):
        if is_there_a_quib_in_args(args, kwargs):
            from pyquibbler import CacheBehavior
            return GraphicsFunctionQuib.create(
                func=original_method,
                func_args=args,
                func_kwargs=kwargs,
                cache_behavior=CacheBehavior.AUTO,
                lazy=False
            )
        return call_func_with_quib_values(func=original_method, args=args, kwargs=kwargs)

    setattr(cls, method_name, override)


OVERRIDDEN_AXES_METHODS = ['plot', 'imshow', 'text', 'bar', 'set_xlim', 'set_ylim']


@ensure_only_run_once_globally
def override_axes_methods():
    """
    Override all axes methods so we can add redrawers to the relevant quibs
    """
    for axes_method in OVERRIDDEN_AXES_METHODS:
        override_axes_method(axes_method)


