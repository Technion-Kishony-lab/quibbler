import pathlib

from tests.conftest import get_axes, create_mouse_press_move_release_events, plt_pause
from tests.integration.quib.graphics.widgets.utils import quibbler_image_comparison, count_canvas_draws


@quibbler_image_comparison(baseline_images=['covid_demo'])
def test_covid_demo(live_artists):
    from pyquibbler import iquib, q, initialize_quibbler
    from matplotlib import pyplot as plt
    import numpy as np
    axes = get_axes()
    initialize_quibbler()

    # Load data file of COVID statistics per countries
    file_name = iquib(pathlib.Path(__file__).parent.resolve() / 'covid_fatality.csv')

    dtype = [("Country", str, 32), ("ConfirmedCases", int), ("Deaths", int), ("Population", float)]
    fatality_table = np.genfromtxt(file_name, dtype=dtype, delimiter=',', names=True)

    # %%

    # Figure setup
    plt.xlabel("Confirmed Cases (%)")
    plt.ylabel("Number of countries")
    max_xlim = 20
    plt.xlim([0, max_xlim])

    # %%

    # Calculate and plot histogram of infection rate
    rate = fatality_table['ConfirmedCases'] / fatality_table['Population'] * 100
    plt.hist(rate, np.arange(0, 20, 1), facecolor='g', edgecolor='black', linewidth=1.2)

    # %%

    # Define a threshold for high-rate countries
    threshold = iquib(15)

    # Identify countries above/below threshold
    below_threshold = rate < threshold
    above_threshold = rate >= threshold

    # Plot histogram of above-threshold countries
    plt.hist(rate[above_threshold], np.arange(0, 20, 1), facecolor='r', alpha=1, edgecolor='black', linewidth=1.2)

    # Plot the threshold (using picker=True indicates that it is draggable)
    plt.plot(threshold, 0, markerfacecolor='k', marker='^', markersize=30,
             picker=True, pickradius=30);

    # %%

    # List countries above the threshold:
    plt.text(18, 68, 'High-rate countries', fontsize=14, verticalalignment='top',
             horizontalalignment='right', color='r')
    plt.text(18, 63, q("\n".join, fatality_table[above_threshold]['Country']), verticalalignment='top',
             horizontalalignment='right', color='r');

    # %%

    # Pie chart
    below_threshold_sum = q(sum, below_threshold)
    above_threshold_sum = q(sum, above_threshold)
    ax = plt.axes([0.3, 0.4, 0.3, 0.3])
    plt.pie([below_threshold_sum, above_threshold_sum], colors=['g', 'r'])

    plt_pause(0.1)

    with count_canvas_draws(axes.figure.canvas) as canvas_redraw_count:
        create_mouse_press_move_release_events(axes, [(15, 0), (12.5, 0), (10, 0)])

    assert canvas_redraw_count.count == 2  # 2 x motion
