import numpy as np
from matplotlib import pyplot as plt

from pyquibbler import iquib, override_all, q

override_all()

# TODO: clrs(isoverride(WellFactor)+1)

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
ax1 = plt.gca()

plt.plot(x, plate_factor,
         marker='s', markerfacecolor='y', markersize=9,
         linestyle='None', picker=True)


# plt.show()
# exit(0)
def draw_plate_marker(i):
    ax1.plot(x[i], plate_factor[i],
             marker='s', markerfacecolor='y', markersize=9,
             linestyle='None', picker=True)


np.apply_along_axis(draw_plate_marker, 0, np.arange(q(len, x)))

plt.axis([-0.5, n_plates - 0.5, 0, 100])
plt.ylabel('Plate factor')

n_wells = iquib(6)
well_factor = np.repeat(plate_factor, n_wells, 0)
well_factor.set_assignment_template(0, 100, 1)
well_factor.allow_overriding = True
plt.subplot(2, 1, 2)
dd = np.linspace(-0.4, 0.4, n_wells + 1)
dd = (dd[0:-1] + dd[1:]) / 2.
xx = np.reshape(x + np.reshape(dd, (n_wells, 1)), (n_wells * n_plates,))
plt.bar(xx, well_factor, color=(0.7, 0.7, 0.7), width=0.1)
plt.axis([-0.5, n_plates - 0.5, 0, 100])

ax2 = plt.gca()


def draw_well_marker(i):
    ax2.plot(xx[i], well_factor[i],
             marker='s', markerfacecolor='y', markersize=9,
             linestyle='None', picker=True)


np.apply_along_axis(draw_well_marker, 0, np.arange(q(len, xx)))

plt.ylabel('Well factor')
plt.show()
