import functools
from typing import Dict

from pyquibbler.quib.quib import Quib


TRAIT_TO_QUIB_ATTR = '_quibbler_trait_to_quib'


def is_ipywidgets_installed() -> bool:
    try:
        # noinspection PyPackageRequirements
        import ipywidgets
        # noinspection PyPackageRequirements
        import traitlets
    except ImportError:
        return False

    return True


def _get_or_create_trait_to_quib(widget) -> Dict[str, Quib]:
    if not hasattr(widget, TRAIT_TO_QUIB_ATTR):
        setattr(widget, TRAIT_TO_QUIB_ATTR, {})

    return getattr(widget, TRAIT_TO_QUIB_ATTR)


def get_wrapper_for_trait_type_set():

    # noinspection PyPackageRequirements
    from traitlets import TraitType

    def actual_set(self, obj, value):
        new_value = self._validate(obj, value)
        obj._trait_values[self.name] = new_value

    func = TraitType.set

    @functools.wraps(func)
    def _set(self, obj, value):
        if isinstance(value, Quib):
            quib = value

            def on_quib_change(new_value):
                func(self, obj, new_value)

            # indicate on the widget that the trait is connected to the quib:
            _get_or_create_trait_to_quib(obj)[self.name] = quib

            # set the quib to call back when changed:
            quib.add_callback(on_quib_change)

            value = quib.get_value()
            actual_set(self, obj, value)
            return
        else:
            quib = _get_or_create_trait_to_quib(obj).get(self.name, None)
            if quib is not None:
                quib.assign(value)
                return
            
        func(self, obj, value)

    return _set


def override_ipywidgets_if_installed():
    if not is_ipywidgets_installed():
        return

    # noinspection PyPackageRequirements
    from traitlets import TraitType

    TraitType.set = get_wrapper_for_trait_type_set()
