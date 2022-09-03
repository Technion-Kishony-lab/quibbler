import importlib


def deactivate_pyquibbler():

    import matplotlib
    importlib.reload(matplotlib)

    import numpy
    importlib.reload(numpy)

    from pyquibbler.quib import quib
    importlib.reload(quib)

    import ipywidgets
    from pyquibbler.function_overriding import override_all
    importlib.reload(ipywidgets)
    importlib.reload(override_all)
