from pyquibbler import iquib
from pyquibbler.cache.cache import CacheStatus
from pyquibbler.quib.specialized_functions.proxy import create_proxy


def test_proxy_never_invalidates():
    arg = iquib([100])
    proxy = create_proxy(arg)
    child = proxy[0]
    child.get_value()

    arg.handler.invalidate_and_aggregate_redraw_at_path([])

    assert child.cache_status == CacheStatus.ALL_VALID
