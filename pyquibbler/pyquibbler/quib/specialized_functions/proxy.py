from __future__ import annotations
from typing import Any, Dict, List

from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_or_reuse_func_definition
from pyquibbler.inversion.inverter import Inverter
from pyquibbler.path import Path
from pyquibbler.path_translation import BackwardsPathTranslator, Source, Inversal

from typing import TYPE_CHECKING

from pyquibbler.path_translation.base_translators import BackwardsTranslationRunCondition

if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib


def create_proxy(quib: Quib) -> Quib:
    from pyquibbler.quib.factory import create_quib

    # We don't need to be the child of our parent, as we never want to be invalidated
    proxy_quib = create_quib(func=proxy, args=(quib,), register_as_child_of_parents=False)
    return proxy_quib


def proxy(quib_value: Any):
    return quib_value


class ProxyBackwardsPathTranslator(BackwardsPathTranslator):

    RUN_CONDITIONS = [BackwardsTranslationRunCondition.NO_SHAPE_AND_TYPE]

    def _backwards_translate(self) -> Dict[Source, Path]:
        return {
            source: self._path
            for source in self._func_call.get_data_sources()
        }


class ProxyInverter(Inverter):

    def get_inversals(self) -> List[Inversal]:
        source = self._func_call.args[0]
        return [Inversal(source=source, assignment=self._assignment)]


proxy_definition = create_or_reuse_func_definition(raw_data_source_arguments=[0], inverters=[ProxyInverter],
                                                   backwards_path_translators=[ProxyBackwardsPathTranslator])

add_definition_for_function(func=proxy, func_definition=proxy_definition, quib_creating_func=create_proxy)


def get_parent_of_proxy(quib: Quib):
    while quib.func is proxy:
        quib = quib.args[0]
    return quib
