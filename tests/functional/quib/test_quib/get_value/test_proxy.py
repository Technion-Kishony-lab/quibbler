from pyquibbler.path.path_component import PathComponent
from pyquibbler.quib.specialized_functions.proxy import create_proxy
from tests.functional.quib.test_quib.get_value.utils import collecting_quib


def test_proxy_get_value():
    val = [1, 2, 3]
    path_collector_quib = collecting_quib(val)
    proxy = create_proxy(path_collector_quib)

    with path_collector_quib.collect_valid_paths() as valid_paths:
        res = proxy.get_value_valid_at_path([PathComponent(0)])

    assert valid_paths == [[PathComponent(0)]]
    assert res == val