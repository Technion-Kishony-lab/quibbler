import numpy as np
from matplotlib import pyplot as plt, widgets

from pyquibbler import q, initialize_quibbler, iquib

initialize_quibbler()

count = iquib(6).setp(assignment_template=(2, 12, 2))

numbers = np.arange(count).setp(allow_overriding=True)
reshaped_numbers = np.reshape(numbers, (q(int, count / 2), 2))

axis = plt.gca()


def run_heavy_averages(oned_slice):
    print("running heavy average...")
    return np.average(oned_slice)


def plot_averages(res):
    average, x = res
    print("plotting average")
    axis.text(x, 0.5, f"avg: {average}")


result = np.apply_along_axis(func1d=run_heavy_averages, axis=1, arr=reshaped_numbers, lazy=True)
xs_to_plot = np.linspace(0, 0.7, num=q(int, count / 2))
result_with_xs = np.concatenate((result[:, np.newaxis], xs_to_plot[:, np.newaxis]), axis=1)
np.apply_along_axis(func1d=plot_averages, axis=1, arr=result_with_xs)

axfreq = plt.axes([0.23, 0.4, 0.65, 0.03])
widgets.Slider(
    ax=axfreq,
    label="Drag to 0",
    valmin=2,
    valmax=12,
    valstep=2,
    valinit=count
)

plt.show(block=False)

# Feel free to play with specific values in `numbers`- you'll see in the prints it only
# reruns one average and one plotting
# You can also play with the slider
