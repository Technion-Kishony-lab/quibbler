from pyquibbler import iquib, override_all, q
override_all()
import matplotlib.pyplot as plt
import numpy as np

# Figure setup:
fig1 = plt.figure(figsize=(4,4))
ax = fig1.gca()
ax.axis('square');
ax.axis([0, 12, 0, 12]);

#%%

# Define star coordinates:
nPoints = iquib(5);
dtet = 2 * np.pi / (2*nPoints)
tet = np.arange(np.pi/2, np.pi/2+2*np.pi, dtet);
rR = np.array([1.5, 0.7])
rs = np.tile(rR, (nPoints,));
x_star = np.cos(tet) * rs;
y_star = np.sin(tet) * rs;

#%%

# Allow changing the coordinates:
x_star.set_allow_overriding(True);
y_star.set_allow_overriding(True);

#%%

x_star_circ = np.concatenate([x_star, x_star[[0]]])
y_star_circ = np.concatenate([y_star, y_star[[0]]])

#%%

# Define and draw movable star:
x_center_movable = iquib(np.array([7.]));
y_center_movable = iquib(np.array([5.]));

# using x_center_movable as the first argument
# (to which the inverse-assignment is channeled):
x_movable_star = x_center_movable + x_star_circ;
y_movable_star = y_center_movable + y_star_circ;
ax.text(x_center_movable, y_center_movable+np.min(y_star_circ)-0.2, 'Move me!',
       horizontalalignment='center', verticalalignment='top')

ax.plot(x_movable_star, y_movable_star, linewidth=2, color='m', picker=True);

#%%

# Define and draw changeable star:
x_center_fixed = iquib(np.array([2.]));
y_center_fixed = iquib(np.array([8.]));

# using x_star as the first argument:
x_changeable_star = x_star_circ + x_center_fixed;
y_changeable_star = y_star_circ + y_center_fixed;
ax.text(x_center_fixed, y_center_fixed+np.min(y_star_circ)-0.2,'Change me!',
        horizontalalignment='center', verticalalignment='top')
aaa = ax.plot(x_changeable_star, y_changeable_star, linewidth=2, color='c', picker=True);

#%%

ax.set_title(q('{:.1f},{:.1f}'.format, x_center_movable[0], y_center_movable[0]));


plt.show()