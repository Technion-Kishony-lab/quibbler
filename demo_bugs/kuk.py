from functools import partial
from pyquibbler import iquib, override_all, q
override_all()
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
mpl.use('macosx')

# Set number of plates
n_plates = iquib(10)

# Figure setup
plt.figure()
plt.axis([-0.5, n_plates - 0.5, 0, 100])
plt.ylabel('Per-item factor')
plt.xticks(np.arange(n_plates))

# Common properties
input_properties = {'assignment_template':(0, 100, 1), 'allow_overriding':True}

# Define and plot the default factor
default_factor = iquib(np.array([70]), **input_properties)
plt.plot([-0.5, n_plates - 0.5], default_factor[[0, 0]], 'k',
         zorder=3, linewidth=2, picker=True)

# Define and plot the per-item factor
from matplotlib.colors import ListedColormap
per_item_factor = np.repeat(default_factor, n_plates, 0) \
    .setp(**input_properties, assigned_quibs='self')

x = np.arange(n_plates)
plt.bar(x, per_item_factor, color=(0.7, 0.7, 0.7))

plt.scatter(x, per_item_factor, marker='s', s=150, zorder=2,
            cmap=ListedColormap(['grey', 'red']),
            c=per_item_factor.get_override_mask(),
            picker=True, pickradius=20)

plt.show()
