import numpy as np
from matplotlib import pyplot as plt
from matplotlib import widgets
from pyquibbler import iquib, override_all, q

override_all()
plt.figure(figsize=[10, 7])

points = 10
x = iquib(np.arange(0., points))
y = iquib(100. - np.power(np.arange(1, points + 1), 2) + 5 * np.random.randn(points))

n = iquib(2)

axfreq = plt.axes([0.25, 0.1, 0.65, 0.03])
freq_slider = widgets.Slider(
    ax=axfreq,
    label=q("poly deg {:.0f}".format, n),
    valmin=0,
    valmax=5,
    valstep=1,
    valinit=n
)

plt.axes([0.2, 0.2, 0.7, .6])
plt.plot(x, y,
         marker='o', markersize=12, markerfacecolor='y',
         linestyle='None', picker=True, pickradius=15)

pf = np.polyfit(x, y, n)
x0 = np.linspace(q(min, x), q(max, x), 30)
y0 = np.polyval(pf, x0)
plt.plot(x0, y0, 'k-')

plt.show()
