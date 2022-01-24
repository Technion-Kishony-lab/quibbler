from __future__ import annotations
from typing import Any, List, TYPE_CHECKING, Dict

from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_func_definition
from pyquibbler.inversion.inverter import Inverter
from pyquibbler.path.path_component import Path
from pyquibbler.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.translation.forwards_path_translator import ForwardsPathTranslator
from pyquibbler.translation.types import Source, Inversal

if TYPE_CHECKING:
    from pyquibbler.quib import Quib


def create_proxy(quib: Quib):
    from pyquibbler.quib.factory import create_quib
    return create_quib(func=proxy, args=(quib,))


def proxy(quib_value: Any):
    return quib_value


class ProxyForwardsPathTranslator(ForwardsPathTranslator):

    SHOULD_ATTEMPT_WITHOUT_SHAPE_AND_TYPE = True

    def _forward_translate_source(self, source: Source, path: Path) -> List[Path]:
        # We never invalidate as a proxy
        return []


class ProxyBackwardsPathTranslator(BackwardsPathTranslator):

    SHOULD_ATTEMPT_WITHOUT_SHAPE_AND_TYPE = True

    def translate(self) -> Dict[Source, Path]:
        return {
            source: self._path
            for source in self._func_call.get_data_sources()
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


proxy_definition = create_func_definition(
    forwards_path_translators=[ProxyForwardsPathTranslator],
    backwards_path_translators=[ProxyBackwardsPathTranslator],
    data_source_arguments=[0],
    inverters=[ProxyInverter]
)

add_definition_for_function(proxy, proxy_definition)
