from pyquibbler import iquib
from pyquibbler.refactor.cache.cache import CacheStatus
from pyquibbler.refactor.quib.specialized_functions.proxy import create_proxy


def test_proxy_never_invalidates():
    arg = iquib([100])
    proxy = create_proxy(arg)
    child = proxy[0]
    child.get_value()

    arg.invalidate_and_redraw_at_path([])

    assert child.cache_status == CacheStatus.ALL_VALID
