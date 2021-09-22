from matplotlib.testing.decorators import image_comparison

import matplotlib.pyplot as plt
from pyquibbler import iquib
from pyquibbler.graphics.artists_redrawer import ArtistsRedrawer

# This import is critical!! Do not delete!!
# This imports a fixture (it has autouse=True) that cleans up matplotlib stuffs our tests do
from matplotlib.testing.conftest import mpl_test_settings


@image_comparison(baseline_images=['happy_flow'], remove_text=True,
                  extensions=['png'])
def test_artists_redrawer_happy_flow():
    redrawer = ArtistsRedrawer.create_from_function_call(
        func=plt.plot,
        args=([30 for _ in range(3)],),
        kwargs={}
    )

    redrawer.redraw()


@image_comparison(baseline_images=["happy_flow"], remove_text=True,
                  extensions=['png'])
def test_artists_redrawer_uses_quib_value():
    redrawer = ArtistsRedrawer.create_from_function_call(
        func=plt.plot,
        args=([iquib(30) for _ in range(3)],),
        kwargs={}
    )

    redrawer.redraw()


@image_comparison(baseline_images=["happy_flow"], remove_text=True,
                  extensions=['png'])
def test_artists_redrawer_does_not_change_on_redraw():
    redrawer = ArtistsRedrawer.create_from_function_call(
        func=plt.plot,
        args=([30 for _ in range(3)],),
        kwargs={}
    )

    for i in range(10):
        redrawer.redraw()


@image_comparison(baseline_images=["layered"], remove_text=True,
                  extensions=['png'])
def test_artists_redrawer_does_not_change_artist_position():
    redrawer = ArtistsRedrawer.create_from_function_call(
        func=plt.plot,
        args=([iquib(30) for _ in range(3)],),
        kwargs=dict(linewidth=20, color="yellow"),
    )

    plt.plot([30, 30, 30], color="blue")

    redrawer.redraw()
