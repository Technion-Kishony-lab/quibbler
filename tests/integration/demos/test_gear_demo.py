from tests.conftest import get_axes, create_mouse_press_move_release_events
from tests.integration.quib.graphics.widgets.utils import quibbler_image_comparison, count_canvas_draws


@quibbler_image_comparison(baseline_images=['gear_demo'])
def test_gear_demo(live_artists):
    from pyquibbler import iquib, quiby, initialize_quibbler
    from matplotlib import pyplot as plt
    import numpy as np
    from numpy import pi, sin, cos
    from matplotlib.widgets import Slider

    ax = get_axes()
    initialize_quibbler()

    # create the figure
    plt.axis('equal')

    def create_wheel(center, n, r, phase, idx, color):
        # wheel body
        ax.add_patch(plt.Circle((center, 0), r, color='gray'))

        # 90 deg lines
        a = phase + np.arange(4) * 2 * pi / 4
        ax.plot(cos(a[0::2]) * r + center, sin(a[0::2]) * r, '-k', lw=2)
        ax.plot(cos(a[1::2]) * r + center, sin(a[1::2]) * r, '-k', lw=2)

        # teeth
        a = phase + (0.5 * idx + np.arange(np.abs(n))) * 2 * pi / n
        ax.plot(cos(a) * r + center, sin(a) * r, '.', markersize=15, color=color)

        # central axis
        ax.plot(center, 0, 'ko', markersize=20)
        ax.set_xlim(-10, 200)

    # Parameters
    default_num_tooth = 5
    radius_per_teeth = 2
    all_colors = list('rgbmcy')
    n_w = iquib(2)
    phase0 = iquib(0.)

    # Create derived quibs
    teeth_nums = (np.zeros(n_w, dtype=int) + default_num_tooth)
    teeth_nums.allow_overriding = True
    teeth_nums = teeth_nums * 2  # make sure teeth_num is even

    radii = teeth_nums * radius_per_teeth
    centers = -radii + np.cumsum(2 * radii)
    transmision = - teeth_nums[:-1] / teeth_nums[1:]

    colors = iquib(all_colors)[:n_w]
    indices = np.arange(n_w)

    phases = phase0 * np.concatenate(([1], np.cumprod(transmision)))

    # Slider for number of wheels
    ax_slider = plt.axes(position=(0.3, 0.13, 0.4, 0.06))
    Slider(ax_slider, valinit=n_w, valmin=1, valmax=5, label='# wheels');

    # Implement using quiby
    @quiby(pass_quibs=True, is_graphics=True)
    def create_wheels(centers, teeth_nums, radii, phases, indices, colors):
        n = len(centers.get_value())
        for i in range(n):
            create_wheel(centers[i], teeth_nums[i], radii[i], phases[i], indices[i], colors[i])

    create_wheels(centers, teeth_nums, radii, phases, indices, colors)

    assert n_w.get_value() == 2,  "Sanity"
    create_mouse_press_move_release_events(ax_slider, [(4.3, 0.5)])
    assert n_w.get_value() == 4

    assert phase0.get_value() == 0.,  "Sanity"
    create_mouse_press_move_release_events(ax, [(0, 0), (0, 20)])
    assert abs(phase0.get_value() + np.pi / 4) < 0.03

    assert radii.get_value()[1] == 20
    create_mouse_press_move_release_events(ax, [(60, 0), (70, 0)])
    assert radii.get_value()[1] == 28
