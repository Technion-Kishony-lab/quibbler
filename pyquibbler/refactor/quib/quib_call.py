from dataclasses import dataclass
from functools import lru_cache

from pyquibbler.quib.assignment import Path
from pyquibbler.quib.function_quibs.cache.cache import Cache
from pyquibbler.quib.function_quibs.external_call_failed_exception_handling import \
    external_call_failed_exception_handling
from pyquibbler.quib.function_quibs.utils import FuncWithArgsValues
from dataclasses import dataclass
from typing import List, Optional, Any

import numpy as np

from pyquibbler.quib import PathComponent
from pyquibbler.quib.assignment import Path
from pyquibbler.quib.assignment.utils import deep_get, deep_assign_data_in_path
from pyquibbler.quib.function_quibs.cache import create_cache, HolisticCache, NdUnstructuredArrayCache
from pyquibbler.quib.function_quibs.cache.cache import Cache
from pyquibbler.quib.function_quibs.cache.holistic_cache import PathCannotHaveComponentsException
from pyquibbler.quib.function_quibs.cache.shallow.indexable_cache import transform_cache_to_nd_if_necessary_given_path
from pyquibbler.quib.function_quibs.utils import FuncWithArgsValues
from pyquibbler.refactor.graphics.graphics_collection import GraphicsCollection
from pyquibbler.refactor.quib.utils import call_func_with_quib_values


@dataclass
class QuibFunctionRunner:

    func_with_args_values: FuncWithArgsValues
    cache: Cache
    graphics_collections: GraphicsCollection
    valid_path: Path

    @property
    @lru_cache()
    def _truncated_path(self):
        """
        Truncate a path so it can be used by shallow caches- we only want to cache and store elements at their first
        component in their path
        """
        if self.valid_path is None:
            new_path = None
        else:
            first_two_components = self.valid_path[0:2]
            if (
                    len(first_two_components) == 2
                    and first_two_components[0].references_field_in_field_array()
                    and not first_two_components[1].references_field_in_field_array()
                    and first_two_components[1].indexed_cls == np.ndarray
            ):
                # We are in a situation in which we have a field, and then indexes- these are always interchangable
                # by definition, so we switch them to get the indexes in order to behave in the same fashion-
                # e.g.
                # ["a"][0] or [0]["a"] should cache in the same fashion (for an ndarray)
                new_path = [first_two_components[1]]
            else:
                new_path = [*first_two_components[0:1]]
        return new_path

    @property
    def _args(self):
        return self.func_with_args_values.args_values.args

    @property
    def _kwargs(self):
        return self.func_with_args_values.args_values.kwargs

    def get_cached_data_at_truncated_path_given_result_at_uncached_path(self, result, uncached_path):
        data = self.cache.get_value()

        # Need to refactor this so that the cache itself takes care of these edge cases- for example,
        # indexablecache already knows how to take care of tuples, and holisticache knows not to try setting values at
        # specific paths.
        # Perhaps get_value(with_data_at_component)?
        # Or perhaps simply wait for deep caches...
        if isinstance(result, list) and isinstance(self.cache, NdUnstructuredArrayCache):
            result = np.array(result)

        valid_value = deep_get(result, uncached_path)

        if isinstance(data, tuple):
            new_data = deep_assign_data_in_path(list(data), uncached_path, valid_value)
            value = deep_get(tuple(new_data), self._truncated_path)
        else:
            if isinstance(self.cache, HolisticCache):
                value = valid_value
            else:
                new_data = deep_assign_data_in_path(data, uncached_path, valid_value)
                value = deep_get(new_data, self._truncated_path)

        return value

    def _call_func(self, valid_path: List[PathComponent]):
        self._initialize_graphics_collections()

        # TODO: how do we choose correct indexes for graphics collection?
        graphics_collection: GraphicsCollection = self._graphics_collections[()]

        # TODO: pass_quibs
        # TODO: quib_guard

        with graphics_collection.track_and_handle_new_graphics(
                kwargs_specified_in_artists_creation=set(self._kwargs.keys())
        ):
            with external_call_failed_exception_handling():
                res = self.func_with_args_values.func(*new_args, **new_kwargs)

                # TODO: Move this logic somewhere else
                if len(graphics_collection.widgets) > 0 and isinstance(res, AxesWidget):
                    assert len(graphics_collection.widgets) == 1
                    res = list(graphics_collection.widgets)[0]

                # We don't allow returning quibs as results from functions
                from pyquibbler.quib import Quib
                if isinstance(res, Quib):
                    res = res.get_value()
                ####

                return res

    def _ensure_cache_matches_result(self, new_result: Any):
        """
        Ensure there exists a current cache matching the given result; if the held cache does not match,
        this function will now recreate the cache to match it
        """
        if self.cache is None or not self.cache.matches_result(new_result):
            self.cache = create_cache(new_result)

    def _call_func_on_uncached_path(self, path: Path):
        return call_func_with_quib_values(self.func_with_args_values.func,
                                          args=self.func_with_args_values.args_values.args,
                                          kwargs=self.func_with_args_values.args_values.kwargs)

    def _run_func_on_uncached_paths(self, uncached_paths: List[Optional[Path]]):
        """
        Run the function a list of uncached paths, given an original truncated path, storing it in our cache
        """
        for uncached_path in uncached_paths:
            result = self._call_func_on_uncached_path(uncached_path)

            self._ensure_cache_matches_result(result)

            if uncached_path is not None:
                try:
                    cache = transform_cache_to_nd_if_necessary_given_path(self.cache, self._truncated_path)
                    value = self.get_cached_data_at_truncated_path_given_result_at_uncached_path(result, uncached_path)

                    cache.set_valid_value_at_path(self._truncated_path, value)
                except PathCannotHaveComponentsException:
                    # We do not have a diverged cache for this type, we can't store the value; this is not a problem as
                    # everything will work as expected, but we will simply not cache
                    assert len(uncached_paths) == 1, "There should never be a situation in which we have multiple " \
                                                     "uncached paths but our cache can't handle setting a value at a " \
                                                     "specific component"
                    break
                else:
                    # sanity
                    assert len(cache.get_uncached_paths(truncated_path)) == 0

        return cache

    def _get_uncached_paths_matching_path(self):
        """
        Get a list of paths that are uncached within the given path- these paths must be a subset of the given path
        (or the path itself)
        """

        if self.cache is not None:
            if self.valid_path is None:
                # We need to be valid at no paths, so by definitions we also have no uncached paths that match no paths
                return []

            try:
                uncached_paths = self.cache.get_uncached_paths(self.valid_path)
            except (TypeError, IndexError):
                # It's possible the user is requesting a value at index which our current cache does not have but which
                # will exist after rerunning the function- in that case, return that the given path is not cached
                uncached_paths = [self.valid_path]
        else:
            uncached_paths = [self.valid_path]

        return uncached_paths

    def run_and_update_cache(self):
        uncached_paths = self._get_uncached_paths_matching_path()

        if len(uncached_paths) == 0:
            return

        self._run_func_on_uncached_paths(uncached_paths)

