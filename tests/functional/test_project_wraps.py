
import pyquibbler as qb


def test_get_project(project):
    assert qb.get_project() is project


def test_get_set_project_directory():
    qb.set_project_directory(None)
    assert qb.get_project_directory() is None

