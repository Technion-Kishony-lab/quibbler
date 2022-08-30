from __future__ import annotations

import functools

from .quiby_widget_trait import QuibyWidgetTrait, get_quiby_widget_trait_type
from pyquibbler.user_utils.obj2quib import obj2quib
from pyquibbler.quib.quib import Quib
from typing import Dict

from pyquibbler.utilities.iterators import is_iterator_empty, iter_objects_of_type_in_object


TRAIT_TO_QUIBY_WIDGET_ATTR = '_quibbler_trait_to_quiby_widget'


def is_ipywidgets_installed() -> bool:
    try:
        # noinspection PyPackageRequirements
        import ipywidgets   # noqa: F401
        # noinspection PyPackageRequirements
        import traitlets   # noqa: F401
    except ImportError:
        return False

    return True


def _bare_set(self, obj, value):
    """The snippet from TraitType.set that does the bare set of the trait"""
    new_value = self._validate(obj, value)
    obj._trait_values[self.name] = new_value


def _get_or_create_trait_to_quiby_widget_trait(widget) -> Dict:
    if not hasattr(widget, TRAIT_TO_QUIBY_WIDGET_ATTR):
        setattr(widget, TRAIT_TO_QUIBY_WIDGET_ATTR, {})

    return getattr(widget, TRAIT_TO_QUIBY_WIDGET_ATTR)


def get_wrapper_for_trait_type_set():

    # noinspection PyPackageRequirements
    from traitlets import TraitType
    QuibyWidgetTrait.original_set = TraitType.set

    @functools.wraps(QuibyWidgetTrait.original_set)
    def quiby_set(self, obj, value):
        if isinstance(value, (list, tuple)) \
                and not is_iterator_empty(iter_objects_of_type_in_object(object_type=Quib, obj=value)):
            value = obj2quib(value)

        if isinstance(value, Quib):
            # We cannot call original_set because it buffers future update to the quib.
            _bare_set(self, obj, value.get_value())

            manager_type = get_quiby_widget_trait_type(obj)
            manager = manager_type(quib=value, trait=self, widget=obj)
            manager.set_widget_to_update_quib_upon_change()
            manager.set_quib_to_update_widget_upon_change()

            trait_to_quiby_widget_trait = _get_or_create_trait_to_quiby_widget_trait(obj)
            trait_to_quiby_widget_trait[self.name] = manager
        else:
            QuibyWidgetTrait.original_set(self, obj, value)

    return quiby_set


def get_wrapper_for_range_widget_init(class_to_override):
    original__init__ = class_to_override.__init__

    @functools.wraps(original__init__)
    def _quibbler__init__(self, *args, **kwargs):
        try:
            original__init__(self, *args, **kwargs)
        except TypeError:
            if not isinstance(kwargs['value'], Quib):
                raise
            super(class_to_override, self).__init__(*args, **kwargs)

    return _quibbler__init__


def override_ipywidgets_if_installed():
    """Allow ipywidgets to work with quib arguments"""

    # ipywidgets is not a required package for quibbler. We only override it if it is installed:
    if not is_ipywidgets_installed():
        return

    # noinspection PyPackageRequirements
    from traitlets import TraitType
    # noinspection PyPackageRequirements
    from ipywidgets.widgets.widget_int import _BoundedIntRange
    # noinspection PyPackageRequirements
    from ipywidgets.widgets.widget_float import _BoundedFloatRange

    # Replace the base set for all widget traits:
    TraitType.set = get_wrapper_for_trait_type_set()

    # Replace init for widgets that check input validity in their init:
    _BoundedIntRange.__init__ = get_wrapper_for_range_widget_init(_BoundedIntRange)
    _BoundedFloatRange.__init__ = get_wrapper_for_range_widget_init(_BoundedFloatRange)
