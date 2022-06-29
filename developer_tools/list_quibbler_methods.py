from pyquibbler import iquib, initialize_quibbler
initialize_quibbler()
import numpy as np

quib = iquib(None)

dir_quib = np.array(dir(quib))

is_magic = np.vectorize(lambda x: x.startswith('__') and x.endswith('__'))(dir_quib)
is_private = np.vectorize(lambda x: x.startswith('__') and not x.endswith('__'))(dir_quib)
is_protected = np.vectorize(lambda x: x.startswith('_') and not x.startswith('__'))(dir_quib)
is_public = ~(is_magic | is_private | is_protected)

print('Public properties/methods:')
for prop in dir_quib[is_public]:
    print(prop)

print('Protected attributes/methods:')
for prop in dir_quib[is_protected]:
    print(prop)
