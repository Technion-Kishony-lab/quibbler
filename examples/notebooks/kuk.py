from pyquibbler import iquib, override_all, q, quibbler_user_function, q_graphics
override_all()
from pyquibbler.quib.assignment import RangeAssignmentTemplate
import matplotlib.pyplot as plt
import numpy as np

def myplot(*args,**kwargs):
    print('ploting')
    return plt.plot(*args,**kwargs)

x = iquib(np.array([1.,3.,2.]))
l = iquib(1)

q_graphics(myplot,x,'o',linewidth=l)
x[1] = 1.5

plt.show()


