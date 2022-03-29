import pytest
from pyquibbler.quib.factory import create_quib
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.specialized_functions.iquib import identity_function
from pyquibbler import CachingOptions
import numpy as np

@pytest.fixture()
def uncached_array_quib() -> Quib:
    return create_quib(func=identity_function, args=(np.arange(6),),
                       allow_overriding=True,
                       lazy=False,
                       caching=CachingOptions.OFF,
                       )

@pytest.fixture()
def uncached_scalar_quib() -> Quib:
    return create_quib(func=identity_function, args=(3,),
                       allow_overriding=True,
                       lazy=False,
                       caching=CachingOptions.OFF,
                       )
