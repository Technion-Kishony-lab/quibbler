import functools

import pytest
from matplotlib.testing.decorators import image_comparison

import matplotlib.pyplot as plt
from pyquibbler import iquib
from pyquibbler.quib.graphics import redraw_axes

# This import is critical!! Do not delete!!
# This imports a fixture (it has autouse=True) that cleans up matplotlib stuffs our tests do
from matplotlib.testing.conftest import mpl_test_settings

from pyquibbler.quib.graphics import GraphicsFunctionQuib, override_axes_methods


def run_graphics_function_quib_and_redraw(q: GraphicsFunctionQuib):
    q.get_value()
    for axes in q.get_axeses():
        redraw_axes(axes)


quibbler_image_comparison = functools.partial(image_comparison, remove_text=True, extensions=['png'],
                                              savefig_kwarg=dict(dpi=100))


@quibbler_image_comparison(baseline_images=['happy_flow'])
def test_graphics_function_quib_happy_flow(axes):
    q = GraphicsFunctionQuib.create(
        func=axes.plot,
        func_args=([30 for _ in range(3)],),
        func_kwargs={},
    )

    run_graphics_function_quib_and_redraw(q)


@image_comparison(baseline_images=["happy_flow"], remove_text=True,
                  extensions=['png'], savefig_kwarg=dict(dpi=100))
def test_graphics_function_quib_uses_quib_value(axes):
    q = GraphicsFunctionQuib.create(
        func=axes.plot,
        func_args=([iquib(30) for _ in range(3)],),
        func_kwargs={}
    )

    run_graphics_function_quib_and_redraw(q)


@image_comparison(baseline_images=["happy_flow"], remove_text=True,
                  extensions=['png'], savefig_kwarg=dict(dpi=100))
def test_graphics_function_quib_does_not_change_on_redraw(axes):
    q = GraphicsFunctionQuib.create(
        func=axes.plot,
        func_args=([30 for _ in range(3)],),
        func_kwargs={}
    )

    for i in range(10):
        run_graphics_function_quib_and_redraw(q)


@quibbler_image_comparison(baseline_images=["layered"])
def test_graphics_function_quib_does_not_change_artist_position(axes):
    q = GraphicsFunctionQuib.create(
        func=axes.plot,
        func_args=([iquib(30) for _ in range(3)],),
        func_kwargs=dict(linewidth=20, color="yellow"),
    )

    plt.plot([30, 30, 30], color="blue")

    run_graphics_function_quib_and_redraw(q)
