from typing import Any

# create quib
from pyquibbler import create_quib
from pyquibbler.function_definitions.location import get_object_type_locations_in_args_kwargs
from pyquibbler.quib.quib import Quib
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_or_reuse_func_definition

# translation/inversion
from pyquibbler.inversion.inverters.obj2quib import Obj2QuibInverter
from pyquibbler.path_translation.translators.obj2quib import \
    Obj2QuibBackwardsPathTranslator, Obj2QuibForwardsPathTranslator
from pyquibbler.type_translation.translators import SameAsArgumentTypeTranslator


def identity_function_obj2quib(v):
    return v


# For functional_representation:
identity_function_obj2quib.__name__ = 'obj2quib'


obj2quib_definition = create_or_reuse_func_definition(raw_data_source_arguments=[0], inverters=[Obj2QuibInverter],
                                                      backwards_path_translators=[Obj2QuibBackwardsPathTranslator],
                                                      forwards_path_translators=[Obj2QuibForwardsPathTranslator],
                                                      result_type_or_type_translators=[SameAsArgumentTypeTranslator])


def obj2quib(obj: Any) -> Quib:
    """
    Create a quib from an object containing quibs.

    Convert an object containing quibs to a quib whose value represents the object.

    Parameters
    ----------
    obj : any object
        The object to convert to quib. Can contain nested lists, tuples, dicts and quibs.

    See Also
    --------
    quiby, q, iquib

    Examples
    --------
    >>> a = iquib(3)
    >>> my_list = obj2quib([1, 2, a, 4])
    >>> a.assign(7)
    >>> my_list.get_value()
    [1, 2, 7, 4]

    >>> my_list[3] = 11
    >>> a.get_value()
    11

    Note
    ----
    If the argument obj is a quib, the function returns this quib.
    """

    # TODO: We do the source search here. This is done to make it easier, in the future, to allow adding an exception
    #  for searching also within object-arrays for this special case of obj2quib (if we want).
    locations = get_object_type_locations_in_args_kwargs(Quib, (obj, ), {})

    return create_quib(
        func=identity_function_obj2quib,
        quib_locations=locations,
        args=(obj,),
    )


add_definition_for_function(func=identity_function_obj2quib,
                            func_definition=obj2quib_definition,
                            quib_creating_func=obj2quib)
