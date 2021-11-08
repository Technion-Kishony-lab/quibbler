from matplotlib import pyplot as plt, widgets
from pyquibbler import *

override_all()

init_val = iquib(4)
another_val = iquib(3) + 9

multiplied_init_val = another_val / (4 * init_val)

yet_another_weirdo = (multiplied_init_val ** 2 / 3) ** 4

plt.text(0.2, 0.5, q("after some stuff, init val is {}".format, yet_another_weirdo))

axfreq = plt.axes([0.23, 0.4, 0.65, 0.03])
widgets.Slider(
    ax=axfreq,
    label="Drag to 0",
    valmin=0,
    valmax=10,
    valstep=1,
    valinit=init_val
)

plt.show()
