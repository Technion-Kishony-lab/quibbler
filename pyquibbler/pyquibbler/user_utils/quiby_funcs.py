from types import ModuleType
from typing import Union, Type, List, Callable

from pyquibbler.function_overriding.is_initiated import warn_if_quibbler_not_initialized


def list_quiby_funcs(module_or_cls: Union[None, ModuleType, Type] = None) -> List[str]:
    """
    List quiby functions.

    Returns a list of string descriptions of all functions overridden to be able to work with quib arguments.

    Parameters
    ----------
    module_or_cls: ModuleType, optional (default: None)
        Specifies a module (numpy, matplotlib, ipywidgets). When specified, only functions belonging to the indicated
        module are listed.

    Returns
    -------
    list of str
        a list of strings indicating the quiby functions
    """
    warn_if_quibbler_not_initialized()

    from pyquibbler.function_definitions.definitions import FUNCS_TO_FUNC_INFO
    from pyquibbler.function_overriding.third_party_overriding.numpy.vectorize_overrides import QVectorize
    from pyquibbler.function_overriding.override_all import ATTRIBUTES_TO_ATTRIBUTE_OVERRIDES
    return \
        [f"{getattr(func_info.module_or_cls, '__name__', func_info.module_or_cls)}: {func_info.func_name}"
         for func_info in FUNCS_TO_FUNC_INFO.values()
         if func_info.is_overridden and (module_or_cls is None or func_info.module_or_cls is module_or_cls)
         and func_info.module_or_cls is not QVectorize] \
        + [f"np.ndarray.{attribute}" for attribute in ATTRIBUTES_TO_ATTRIBUTE_OVERRIDES]


def is_quiby(func: Callable) -> bool:
    """
    Check whether a given function is modified to work directly with quib arguments ("quiby").

    Returns
    -------
    bool

    See Also
    --------
    q, quiby, list_quiby_funcs

    Examples
    --------
    >>> is_quiby(np.sin)  # -> True
    >>> is_quiby(len)  # -> False
    """
    warn_if_quibbler_not_initialized()

    return hasattr(func, '__quibbler_wrapped__')
