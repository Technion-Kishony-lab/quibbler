from unittest import mock

from pyquibbler.utils import ensure_only_run_once_globally


def test_ensure_run_once_globally_runs_once():
    global_func = mock.Mock()

    wrapped_func = ensure_only_run_once_globally(global_func)
    res = wrapped_func()
    wrapped_func()

    global_func.assert_called_once()
    assert res == global_func.return_value
