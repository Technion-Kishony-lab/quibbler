import functools
from pyquibbler.quib.quib import Quib


def is_ipywidgets_installed() -> bool:
    try:
        # noinspection PyPackageRequirements
        import ipywidgets
        # noinspection PyPackageRequirements
        import traitlets
    except ImportError:
        return False

    return True


def get_wrapper_for_trait_type_set():

    # noinspection PyPackageRequirements
    from traitlets import TraitType

    func = TraitType.set

    @functools.wraps(func)
    def _set(self, obj, value):
        if isinstance(value, Quib):

            def on_quib_change(new_value):
                func(self, obj, new_value)

            value.add_callback(on_quib_change)
            value = value.get_value()

        func(self, obj, value)

    return _set


def override_ipywidgets_if_installed():
    if not is_ipywidgets_installed():
        return

    # noinspection PyPackageRequirements
    from traitlets import TraitType

    TraitType.set = get_wrapper_for_trait_type_set()
