import numpy as np

from pyquibbler.graphics.widgets import QRectangleSelector


def test_move_only_one_rectangle_selector(axes, create_axes_mouse_press_move_release_events):
    w1 = QRectangleSelector(axes, extents=[0.4, 0.6, 0.4, 0.6])
    w2 = QRectangleSelector(axes, extents=[0.4, 0.6, 0.4, 0.6])

    create_axes_mouse_press_move_release_events([(0.5, 0.5), (0.6, 0.6), (0.7, 0.7)])
    assert np.array_equal(np.round(w1.extents, 2), [0.6, 0.8, 0.6, 0.8])
    assert np.array_equal(np.round(w2.extents, 2), [0.4, 0.6, 0.4, 0.6])  # this fails in normal RectangleSelector

    create_axes_mouse_press_move_release_events([(0.5, 0.5), (0.6, 0.6), (0.7, 0.7)])
    assert np.array_equal(np.round(w1.extents, 2), [0.6, 0.8, 0.6, 0.8])
    assert np.array_equal(np.round(w2.extents, 2), [0.6, 0.8, 0.6, 0.8])
