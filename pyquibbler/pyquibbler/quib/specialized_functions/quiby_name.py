from pyquibbler import create_quib
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_func_definition
from pyquibbler.quib.quib import Quib
from pyquibbler.translation.translators.quiby_name.quiby_name import \
    BackwardsQuibyNameTranslator, ForwardsQuibyNameTranslator


def get_quiby_name(quib: Quib):
    return quib.name


# For the pretty functional_representation:
get_quiby_name.__name__ = 'quiby_name'


def get_quiby_name_func_call():
    from pyquibbler.quib.func_calling.quiby_namne_func_call import QuibyNameFuncCall
    return QuibyNameFuncCall


quiby_name_definition = create_func_definition(
    is_graphics=False,
    is_random=False,
    lazy=True,
    raw_data_source_arguments=[],
    backwards_path_translators=[BackwardsQuibyNameTranslator],
    forwards_path_translators=[ForwardsQuibyNameTranslator],
    quib_function_call_cls=get_quiby_name_func_call(),
)


def quiby_name(quib: Quib) -> Quib:
    """
    Returns a quib representing the name of an input quib.

    Parameters
    ----------
    quib : Quib
        The quib whose name to represent.

    Returns
    -------
    Quib

    See Also
    --------
    q, quiby, Quib.name, Quib.assigned_name
    """

    return create_quib(
        func=get_quiby_name,
        args=(quib,),
    )


add_definition_for_function(func=get_quiby_name,
                            func_definition=quiby_name_definition,
                            quib_creating_func=quiby_name)
