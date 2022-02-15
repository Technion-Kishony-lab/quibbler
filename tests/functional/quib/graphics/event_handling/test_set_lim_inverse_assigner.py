import pytest

from pyquibbler import iquib
from pyquibbler.quib.graphics.event_handling.graphics_inverse_assigner import inverse_assign_axes_lim_func
from pyquibbler.quib import Quib


def test_axis_lim_inverse_assigner_happy_flow(axes):
    q = iquib(2.)

    inverse_assign_axes_lim_func(
        args=(axes, 0., q),
        lim=(0., 1.),
        is_override_removal=True,
    )

    assert q.get_value() == 1.


@pytest.mark.parametrize("args,lim,expected_value", [
    ([0., iquib(2.)], (1., 3.), [0., 3.]),
    ([iquib([0, 2.])], (1., 3.), [[1., 3.]]),
    ([iquib(0.), 3.], (1., 4.), [1., 3.]),
    ([iquib(0.), iquib(3.)], (1., 4.), [1., 4.]),
], ids=[
    "set_lim(x, iquib)",
    "set_lim(iquib(list))",
    "set_lim(iquib, x)",
    "set_lim(iquib, iquib)",
])
def test_plot_inverse_assigner(axes, args, lim, expected_value):
    inverse_assign_axes_lim_func(
        args=[axes, *args],
        lim=lim,
        is_override_removal=True,
    )

    arg_result = [arg.get_value() if isinstance(arg, Quib) else arg for arg in args]
    assert arg_result == expected_value
