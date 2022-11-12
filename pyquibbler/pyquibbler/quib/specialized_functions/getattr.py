from dataclasses import dataclass

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.function_overriding.override_all import ATTRIBUTES_TO_DEFINITIONS


@dataclass
class PyQuibblerAttributeError(PyQuibblerException, AttributeError):
    item: str

    def __str__(self):
        return f"Quib has no attribute {self.item}."


def create_getattr_quib(quib, item):
    from pyquibbler.quib.factory import create_quib

    type_and_definition = ATTRIBUTES_TO_DEFINITIONS.get(item, None)
    if type_and_definition is None:
        raise PyQuibblerAttributeError(item)

    func_definition = type_and_definition

    getattr_quib = create_quib(func=getattr,
                               args=(quib, item),
                               func_definition=func_definition)

    return getattr_quib
