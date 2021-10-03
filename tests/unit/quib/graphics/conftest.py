import pytest
from matplotlib import pyplot as plt


@pytest.fixture
def axes():
    plt.close("all")
    plt.gcf().set_size_inches(8, 6)
    return plt.gca()
