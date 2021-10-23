import numpy as np

from pyquibbler.quib.function_quibs.cache.shallow.nd_cache.nd_array_cache import NdArrayCache


class NdFieldArrayShallowCache(NdArrayCache):

    @classmethod
    def create_from_result(cls, result):
        mask = np.full(result.shape, True, dtype=[(name, np.bool_) for name in result.dtype.names])
        return cls(result, True, mask)

    @classmethod
    def supports_result(cls, result):
        return super(NdFieldArrayShallowCache, cls).supports_result(result) and result.dtype.names is not None

    def _is_completely_invalid(self):
        return super(NdFieldArrayShallowCache, self)._is_completely_invalid() \
               or all(np.all(self._invalid_mask[name]) for name in self._invalid_mask.dtype.names)