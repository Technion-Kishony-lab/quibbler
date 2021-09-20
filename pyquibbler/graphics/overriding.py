from matplotlib import pyplot as plt

from pyquibbler.graphics import global_collecting
from pyquibbler.graphics.artists_redrawer import ArtistsRedrawer
from pyquibbler.quib.utils import iter_quibs_in_args, call_func_with_quib_values
from pyquibbler.utils import ensure_only_run_once_globally


def override_axes_method(method_name: str):
    """
    Override an axes method to create a method that will add an artistsredrawer to any quibs in the arguments

    :param method_name - name of axes method
    """
    cls = plt.Axes
    original_method = getattr(cls, method_name)

    def override(*args, **kwargs):
        artists = call_func_with_quib_values(func=original_method, args=args, kwargs=kwargs)
        if global_collecting.COLLECTING_GLOBAL_ARTISTS:
            global_collecting.GRAPHICS_CALLS_COLLECTED.append(
                global_collecting.GraphicsFunctionCall(original_method, args, kwargs)
            )
            global_collecting.ARTISTS_COLLECTED.extend(artists)
        else:
            redrawer = ArtistsRedrawer(
                artists=artists,
                func=original_method,
                args=args,
                kwargs=kwargs
            )
            for quib in iter_quibs_in_args(args, kwargs):
                quib.add_artists_redrawer(redrawer)

        return artists

    setattr(cls, method_name, override)


OVERRIDDEN_AXES_METHODS = ['plot', 'imshow', 'text']


@ensure_only_run_once_globally
def override_axes_methods():
    """
    Override all axes methods so we can add redrawers to the relevant quibs
    """
    for axes_method in OVERRIDDEN_AXES_METHODS:
        override_axes_method(axes_method)


