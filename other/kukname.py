from pyquibbler import q, iquib, override_all
override_all()
import numpy as np
from pyquibbler.utilities.iterators import get_paths_for_objects_of_type

id = lambda x: x
age = iquib(27)
a = q(id, {'name': 'roy', 'age': age})
print(a['age'].get_value()) # -> returns the Quib age, rather than int: 27