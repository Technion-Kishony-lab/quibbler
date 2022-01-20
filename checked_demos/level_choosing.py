from functools import partial
from pyquibbler import iquib, override_all, q
override_all()
import matplotlib.pyplot as plt
import numpy as np

#%%

# user function to plot markers at specified colors
@partial(np.vectorize, excluded={0}, evaluate_now=True, pass_quibs=True)
def plot_dragger(ax, x, y, overridden):
    color = 'r' if overridden.get_value() else 'g'
    ax.plot(x, y, marker='d', markerfacecolor=color, markeredgecolor='None',
            markersize=12, linestyle='None', picker=True)

#%%

# Set number of plate and number wells per plate
n_plates = iquib(3)
n_wells = iquib(6)

#%%

# Figure setup
plt.figure()

ax1 = plt.subplot(2, 1, 1)
ax1.axis([-0.5, n_plates - 0.5, 0, 100])
ax1.set_ylabel('Plate factor')
ax1.set_xticks(np.arange(n_plates))

ax2 = plt.subplot(2, 1, 2)
ax2.axis([-0.5, n_plates - 0.5, 0, 100])
ax2.set_ylabel('Well factor');
ax2.set_xticks(np.arange(n_plates));

#%%

# Common properties
input_properties = {'assignment_template':(0, 100, 1), 'allow_overriding':True}

#%%

# Define and plot the default factor
default_factor = iquib(np.array([70])).setp(**input_properties, name='Default')
ax1.plot([-0.5, n_plates - 0.5], default_factor[[0, 0]], 'k', linewidth=5, picker=True);

#%%

# Define and plot the per-plate factor
plate_factor = np.repeat(default_factor, n_plates, 0).setp(**input_properties, name='Plate_factor')
x = np.arange(n_plates)
ax1.bar(x, plate_factor, color=(0.7, 0.7, 0.7))
plot_dragger(ax1, x, plate_factor, plate_factor.get_override_mask());

#%%

# Define the per-plate-per-well factor
well_factor = np.repeat(plate_factor, n_wells, 0).setp(**input_properties, name='Well_factor')
dd = np.linspace(-0.4, 0.4, n_wells + 1)
dd = (dd[0:-1] + dd[1:]) / 2.
xx = np.ravel(x + np.reshape(dd, (n_wells, 1)), 'F')
ax2.bar(xx, well_factor, color=(0.7, 0.7, 0.7), width=0.1)
plot_dragger(ax2, xx, well_factor, well_factor.get_override_mask());

#%%

plt.show()
