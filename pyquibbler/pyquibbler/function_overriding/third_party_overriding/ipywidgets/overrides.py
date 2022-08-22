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


def get_widgets_requiring_tolerance_assignment():
    # noinspection PyPackageRequirements
    import ipywidgets
    return {
        ipywidgets.FloatSlider,
        ipywidgets.FloatRangeSlider,
    }


def _actual_set(widget, trait, value):
    """ The snippet from TraitType.set the does the bare set of the trait"""
    widget._trait_values[trait] = value


def set_widget_to_update_quib_upon_change(widget, trait, quib):
    # TODO: Implement push to undo/redo on mouse drop.
    #  We will need for this to get mouse release from the widget, possibly using:
    #  w = ipyevents.Event(source=widget, watched_events=['mouseup'])
    #  w.on_dom_event(on_drop)

    def on_widget_change(change):
        new_value = change['new']
        quib.assign(new_value)

    widget.observe(on_widget_change, trait)


def set_quib_to_update_widget_upon_change(widget, trait, quib):

    def on_quib_change(new_value):
        _actual_set(widget, trait, new_value)

    quib.add_callback(on_quib_change)


def get_wrapper_for_trait_type_set():

    # noinspection PyPackageRequirements
    from traitlets import TraitType
    original_set = TraitType.set

    @functools.wraps(original_set)
    def quiby_set(self, obj, value):
        if isinstance(value, Quib):
            # We cannot call original_set because it buffers future update to the quib.
            _actual_set(obj, self.name, value.get_value())

            set_widget_to_update_quib_upon_change(obj, self.name, value)
            set_quib_to_update_widget_upon_change(obj, self.name, value)
        else:
            original_set(self, obj, value)

    return quiby_set


def override_ipywidgets_if_installed():
    if not is_ipywidgets_installed():
        return

    # noinspection PyPackageRequirements
    from traitlets import TraitType

    TraitType.set = get_wrapper_for_trait_type_set()
