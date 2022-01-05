from __future__ import annotations
from typing import Any, List, TYPE_CHECKING, Dict

from pyquibbler.refactor.function_definitions import add_definition_for_function
from pyquibbler.refactor.function_definitions.function_definition import create_function_definition
from pyquibbler.refactor.inversion import TranspositionalInverter
from pyquibbler.refactor.inversion.inverter import Inverter
from pyquibbler.refactor.path.path_component import Path
from pyquibbler.refactor.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.refactor.translation.forwards_path_translator import ForwardsPathTranslator
from pyquibbler.refactor.translation.types import Source, Inversal

if TYPE_CHECKING:
    from pyquibbler.refactor.quib import Quib


def create_proxy(quib: Quib):
    from pyquibbler.refactor.quib.factory import create_quib
    return create_quib(func=proxy, args=(quib,))


def proxy(quib_value: Any):
    return quib_value


class ProxyForwardsPathTranslator(ForwardsPathTranslator):

    def _forward_translate_source(self, source: Source, path: Path) -> List[Path]:
        # We never invalidate as a proxy
        return []


class ProxyBackwardsPathTranslator(BackwardsPathTranslator):

    def translate_in_order(self) -> Dict[Source, Path]:
        return {
            source: self._path
            for source in self.get_data_sources()
        }


class ProxyInverter(Inverter):

    def get_inversals(self):
        source = self._func_call.args[0]
        return [
            Inversal(
                source=source,
                assignment=self._assignment
            )
        ]


proxy_definition = create_function_definition(
    forwards_path_translators=[ProxyForwardsPathTranslator],
    backwards_path_translators=[ProxyBackwardsPathTranslator],
    data_source_arguments=[0],
    inverters=[ProxyInverter]
)

add_definition_for_function(proxy, proxy_definition)
