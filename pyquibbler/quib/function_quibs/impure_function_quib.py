from dataclasses import dataclass

from pyquibbler.refactor.exceptions import PyQuibblerException

from .default_function_quib import DefaultFunctionQuib
from .function_quib import CacheBehavior


@dataclass
class InvalidCacheBehaviorForImpureFunctionQuibException(PyQuibblerException):
    invalid_cache_behavior: CacheBehavior

    def __str__(self):
        return 'Impure function quibs must always cache function results, ' \
               'so they are not changed until they are refreshed. ' \
               f'Therefore, the cache behavior should be always set to {CacheBehavior.ON}, ' \
               f'and {self.invalid_cache_behavior} is invalid.'


class ImpureFunctionQuib(DefaultFunctionQuib):
    """
    An impure function is any function that can potentially return different results when run multiple times
    """

    _DEFAULT_CACHE_BEHAVIOR = CacheBehavior.ON

    def set_cache_behavior(self, cache_behavior: CacheBehavior):
        """
        Sets the caching behavior for this ImpureFunctionQuib.
        Impure function quibs must always cache function results, so the only supported mode is `CacheBehavior.ON`.
        """
        if cache_behavior is not CacheBehavior.ON:
            raise InvalidCacheBehaviorForImpureFunctionQuibException(cache_behavior)
        super().set_cache_behavior(cache_behavior)
