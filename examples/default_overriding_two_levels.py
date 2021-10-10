import numpy as np
from matplotlib import pyplot as plt

from pyquibbler import iquib, override_all, q

override_all()

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

for i in range(len(x)):
    color = q(tuple, [(0, 1, 0), (1, 0, 0)])[plate_factor.get_override_mask()[i]]
    plt.plot(x[[i]], plate_factor[[i]],
             marker='s', markerfacecolor=color, markersize=9,
             linestyle='None', picker=True)

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

for i in range(len(xx)):
    color = q(tuple, [(0, 1, 0), (1, 0, 0)])[well_factor.get_override_mask()[i]]
    plt.plot(xx[[i]], well_factor[[i]],  # TODO: without list
             marker='s', markerfacecolor=color, markersize=9,
             linestyle='None', picker=True)

plt.ylabel('Well factor')
plt.show()
# when override source iquib from overridden value, dragging is weird
