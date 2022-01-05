from unittest import mock

from pyquibbler import iquib
from pyquibbler.quib.function_quibs.cache.cache import CacheStatus
from pyquibbler.refactor.quib import Quib
from pyquibbler.refactor.quib.specialized_functions.proxy import create_proxy
from tests.functional.refactor.quib.test_quib.get_value.utils import collecting_quib


def test_proxy_never_invalidates():
    arg = iquib([100])
    proxy = create_proxy(arg)
    child = proxy[0]
    child.get_value()

    arg.invalidate_and_redraw_at_path([])

    assert child.cache_status == CacheStatus.ALL_VALID
