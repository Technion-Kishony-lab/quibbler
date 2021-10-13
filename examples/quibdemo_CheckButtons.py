from pyquibbler import iquib, override_all, q
import matplotlib.pyplot as plt
from matplotlib import widgets
override_all()

plt.figure()
axs = plt.gca()
act = iquib([False,True,True])
widgets.CheckButtons(ax=axs,labels=['Red','Green','Blue'],actives=act)
axs.set_facecolor(act)

plt.show()