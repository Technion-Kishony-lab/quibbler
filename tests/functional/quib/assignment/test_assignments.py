from pyquibbler import iquib


def test_assignment_do_not_change_each_other():
    a = iquib([1, 2])
    a.assign([10, 20, 30])
    a[1] = 21
    assert a.handler.overrider.get(()).value == [10, 20, 30], "sanity"
    a.get_value()

    assert a.handler.overrider.get(()).value == [10, 20, 30]
