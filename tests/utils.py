import functools

from matplotlib.testing.decorators import image_comparison

quibbler_image_comparison = functools.partial(image_comparison, remove_text=True, extensions=['png'],
                                              savefig_kwarg=dict(dpi=100))

