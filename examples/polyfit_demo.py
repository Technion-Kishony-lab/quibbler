import numpy as np
from matplotlib import pyplot as plt
from matplotlib import widgets

from pyquibbler import iquib, quibbler_user_function, override_all, q
from pyquibbler.quib.assignment import RangeAssignmentTemplate

override_all()


x = iquib(np.arange(0., 10))
y = iquib(100. - np.power(np.arange(1, 11), 2) + 5 * np.random.randn(10))

degrees = iquib(2, assignment_template=RangeAssignmentTemplate(0, 5, 1))

plt.figure(figsize=[10, 7])
plt.axes([0.2, 0.2, 0.7, .6])


ax = plt.gca()


def plot_point(i):
    ax.plot(x[i], y[i], marker='o', markersize=12, markerfacecolor='y', linestyle='None', picker=True,
            pickradius=15)


res = np.apply_along_axis(plot_point, 0, np.arange(q(len, x)))

pf = np.polyfit(x, y, degrees)
x0 = np.linspace(q(min, x), q(max, x), 30)
y0 = np.polyval(pf, x0)
plt.plot(x0, y0, 'k-')

axfreq = plt.axes([0.25, 0.1, 0.65, 0.03])
freq_slider = widgets.Slider(
    ax=axfreq,
    label=q("poly deg {:.0f}".format, degrees),
    valmin=0,
    valmax=5,
    valinit=degrees,
)


plt.show()