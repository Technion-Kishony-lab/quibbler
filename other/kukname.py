from pyquibbler import q, iquib, override_all
override_all()
import numpy as np
from pyquibbler.utilities.iterators import get_paths_for_objects_of_type
import  matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

f1 = plt.figure().gca()
f2 = plt.figure().gca()
f3 = plt.figure().gca()

def mygraph(x):
    f1.plot(range(len(x)), x)
    f2.loglog(range(len(x)), x)


a = iquib([1,2,3,4])
qb = q(mygraph, a)

f3.plot([1,2,3,4],a,'o',picker=True)

qb.get_value()

plt.show()
