import numpy as np
from matplotlib import pyplot as plt
from matplotlib import widgets
from pyquibbler import iquib, override_all, q

override_all()
plt.figure(figsize=[10, 7])

x = iquib(np.arange(0., 10))
y = iquib(100. - np.power(np.arange(1, 11), 2) + 5 * np.random.randn(10))

axfreq = plt.axes([0.25, 0.1, 0.65, 0.03])
freq_slider = q(widgets.Slider,
                ax=axfreq,
                label='Freq',
                valmin=0,
                valmax=5,
                valstep=1
                )
axfreq.text(0, -1, q("poly deg {:.0f}".format, freq_slider.val))

ax = plt.axes([0.2, 0.2, 0.7, .6])


def plot_point(i):
    ax.plot(x[i], y[i], marker='o', markersize=12, markerfacecolor='y', linestyle='None', picker=True,
            pickradius=15)


res = np.apply_along_axis(plot_point, 0, np.reshape(np.arange(q(len, x)), (1, q(len, x))))

pf = np.polyfit(x, y, freq_slider.val)
x0 = np.linspace(q(min, x), q(max, x), 30)
y0 = np.polyval(pf, x0)
plt.plot(x0, y0, 'k-')

plt.show()
