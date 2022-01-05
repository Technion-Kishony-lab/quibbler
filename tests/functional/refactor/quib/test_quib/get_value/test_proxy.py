from pyquibbler import iquib
from pyquibbler.refactor.path.path_component import PathComponent
from pyquibbler.refactor.quib.specialized_functions.proxy import create_proxy
from tests.functional.refactor.quib.test_quib.get_value.utils import collecting_quib


def test_proxy_get_value():
    val = [1, 2, 3]
    path_collector_quib = collecting_quib(val)
    proxy = create_proxy(path_collector_quib)

    with path_collector_quib.collect_valid_paths() as valid_paths:
        res = proxy.get_value_valid_at_path([PathComponent(component=0, indexed_cls=list)])

    assert valid_paths == [[PathComponent(indexed_cls=list, component=0)]]
    assert res == val