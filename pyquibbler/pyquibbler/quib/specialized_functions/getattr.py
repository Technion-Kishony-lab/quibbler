from dataclasses import dataclass

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.function_overriding.attribute_override import MethodOverride
from pyquibbler.function_overriding.override_all import ATTRIBUTES_TO_ATTRIBUTE_OVERRIDES
from pyquibbler.quib.specialized_functions.quiby_methods import QuibyMethod


@dataclass
class PyQuibblerAttributeError(PyQuibblerException, AttributeError):
    item: str

    def __str__(self):
        return f"Quib has no attribute {self.item}."


def create_getattr_quib_or_quiby_method(quib, item):
    from pyquibbler.quib.factory import create_quib

    attribute_override = ATTRIBUTES_TO_ATTRIBUTE_OVERRIDES.get(item, None)
    if attribute_override is None:
        raise PyQuibblerAttributeError(item)

    if isinstance(attribute_override, MethodOverride):
        return QuibyMethod(quib, method_override=attribute_override)
    else:
        return create_quib(func=getattr,
                           args=(quib, item),
                           func_definition=attribute_override.func_definition)
