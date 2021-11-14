import numpy as np

from pyquibbler.quib.graphics.axiswise_function_quibs.vectorize.vectorize_metadata import VectorizeCall


def test_meta_with_different_declared_and_actual_otypes():
    vectorize = np.vectorize(lambda x: [1.7, 1.9], otypes=[np.int32], signature='()->(m)')
    meta = VectorizeCall(vectorize, ([1, 2],), {}).get_metadata()

    meta.result_shape