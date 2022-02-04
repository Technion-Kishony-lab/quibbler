from functools import partial

import numpy as np
from matplotlib import pyplot as plt
from pyquibbler import iquib, override_all

override_all()


@partial(np.vectorize, excluded={0}, evaluate_now=True, pass_quibs=True)
def plot_dragger(ax, x, y, overridden):
    color = (1, 0, 0) if overridden.get_value() else (0, 1, 0)
    ax.plot(x, y, marker='s', markerfacecolor=color, markersize=9, linestyle='None', picker=True)


default_factor = iquib(np.array([70]))
default_factor.set_assignment_template(0, 100, 1)
n_plates = iquib(3)

plate_factor = np.repeat(default_factor, n_plates, 0)
plate_factor.set_assignment_template(0, 100, 1)
plate_factor.allow_overriding = True

clrs = iquib('gr')
plt.figure()
plt.subplot(2, 1, 1)
x = np.arange(n_plates)
plt.bar(x, plate_factor, color=(0.7, 0.7, 0.7))
plt.plot([-0.5, n_plates - 0.5], default_factor[[0, 0]], linewidth=5, picker=True)
plot_dragger(plt.gca(), x, plate_factor, plate_factor.get_override_mask())

plt.axis([-0.5, n_plates - 0.5, 0, 100])
plt.ylabel('Plate factor')

n_wells = iquib(6)
well_factor = np.repeat(plate_factor, n_wells, 0)
well_factor.set_assignment_template(0, 100, 1)
well_factor.allow_overriding = True
plt.subplot(2, 1, 2)
dd = np.linspace(-0.4, 0.4, n_wells + 1)
dd = (dd[0:-1] + dd[1:]) / 2.
xx = np.ravel(x + np.reshape(dd, (n_wells, 1)), 'F')
plt.bar(xx, well_factor, color=(0.7, 0.7, 0.7), width=0.1)
plt.axis([-0.5, n_plates - 0.5, 0, 100])
plot_dragger(plt.gca(), xx, well_factor, well_factor.get_override_mask())

plt.ylabel('Well factor')
plt.show()
