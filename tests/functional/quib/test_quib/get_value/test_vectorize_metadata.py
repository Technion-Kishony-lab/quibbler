import numpy as np
from pytest import mark

from pyquibbler.quib.func_calling.func_calls.vectorize.utils import copy_vectorize, alter_signature
from pyquibbler.quib.func_calling.func_calls.vectorize.vectorize_metadata import VectorizeCall


@mark.parametrize(['args', 'kwargs'], [((np.zeros((2, 2, 2)),), dict(y=np.zeros((2, 1, 2))))])
@mark.parametrize(['func', 'signature', 'expected_core_ndims', 'expected_result_ndims', 'arg_ids_to_new_core_ndims'], [
    (None, '(x),(y,z)->()', [1, 2], 0, {}),
    (None, '(),()->(x),()', [0, 0], [1, 0], {}),
    (lambda x, y: (x, y), None, [0, 0], [0, 0], {}),
    (lambda x, y: x + y, None, [0, 0], 0, {}),
    (None, '(x),(y,z)->()', [0, 2], 0, {0: 0}),
    (None, '(x),(y,z)->()', [1, 1], 0, {'y': 1}),
    (None, '(x),(y,z)->()', [3, 3], 0, {0: 3, 'y': 3}),
    (lambda x, y: (x, y), None, [1, 0], [0, 0], {0: 1}),
    (lambda x, y: (x, y), None, [0, 2], [0, 0], {'y': 2}),
    (lambda x, y: (x, y), None, [3, 3], [0, 0], {0: 3, 'y': 3}),
])
def test_alter_signature(func, signature, args, kwargs, expected_core_ndims, expected_result_ndims,
                         arg_ids_to_new_core_ndims):
    vectorize = np.vectorize(func, signature=signature)
    metadata = VectorizeCall(vectorize, args, kwargs).get_metadata()
    altered_signature = alter_signature(metadata.args_metadata, metadata.result_or_results_core_ndims,
                                        arg_ids_to_new_core_ndims)
    vectorize_with_new_signature = copy_vectorize(vectorize, signature=altered_signature)
    metadata_with_new_signature = VectorizeCall(vectorize_with_new_signature, args, kwargs).get_metadata()

    assert metadata_with_new_signature.is_result_a_tuple == metadata.is_result_a_tuple
    assert [meta.core_ndim for meta in metadata_with_new_signature.args_metadata.values()] == expected_core_ndims
    assert (metadata_with_new_signature.results_core_ndims == expected_result_ndims) \
        if metadata.is_result_a_tuple else \
        (metadata_with_new_signature.result_core_ndim == expected_result_ndims)
