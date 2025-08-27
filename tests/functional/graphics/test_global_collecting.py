import pytest
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D

from pyquibbler import iquib
from pyquibbler.graphics import global_collecting


@pytest.mark.parametrize("data", [
    [1, 2, 3],
    iquib([1, 2, 3])
])
def test_global_graphics_collecting_mode_happy_flow(axes, data):
    with global_collecting.ArtistsCollector() as collector:
        plt.plot(data)

    assert len(collector.objects_collected) == 1
    assert isinstance(collector.objects_collected[0], Line2D)


def test_global_graphics_collecting_stores_props_cycle_indices(axes):
    axes._get_lines._idx = 2
    with global_collecting.ColorCyclerIndexCollector() as collector:
        axes.plot([10, 11, 12])

    assert collector.color_cyclers_to_index[axes._get_lines] == 2


def test_global_graphics_collecting_within_collecting(axes):
    with global_collecting.ArtistsCollector() as collector, \
            global_collecting.ArtistsCollector() as nested_collector:
        plt.plot([1, 2, 3])
    assert len(collector.objects_collected) == 1
    assert len(nested_collector.objects_collected) == 1


def test_global_graphics_collecting_not_allowing_axes_creation(axes):
    with global_collecting.AxesCreationPreventor():
        with pytest.raises(global_collecting.AxesCreatedDuringQuibEvaluationException):
            axes.figure.add_axes([0, 0, 1, 1])


def test_get_current_axes_if_exists_no_figures():
    """Test get_current_axes_if_exists when there are no figures."""
    plt.close('all')
    result = global_collecting.get_current_axes_if_exists()
    assert result is None
    assert plt.get_fignums() == []  # Ensure no figures were created


def test_get_current_axes_if_exists_figure_no_axes():
    """Test get_current_axes_if_exists when there's a figure but no axes."""
    plt.close('all')
    fig = plt.figure()
    try:
        assert len(fig.axes) == 0  # Sanity check
        result = global_collecting.get_current_axes_if_exists()
        assert result is None
        assert len(fig.axes) == 0  # Ensure no axes were created
        assert len(plt.get_fignums()) == 1  # Figure should still exist
    finally:
        plt.close(fig)


def test_get_current_axes_if_exists_with_axes(axes):
    """Test get_current_axes_if_exists when there are axes."""
    plt.sca(axes)  # Make sure axes is current
    result = global_collecting.get_current_axes_if_exists()
    assert result is axes
    assert len(plt.get_fignums()) == 1  # Should not create additional figures


def test_get_current_axes_if_exists_multiple_axes():
    """Test get_current_axes_if_exists with multiple axes."""
    plt.close('all')
    fig = plt.figure()
    try:
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        
        # Test with ax1 as current
        plt.sca(ax1)
        result = global_collecting.get_current_axes_if_exists()
        assert result is ax1
        
        # Test with ax2 as current
        plt.sca(ax2)
        result = global_collecting.get_current_axes_if_exists()
        assert result is ax2
        
        assert len(fig.axes) == 2  # Should not create additional axes
    finally:
        plt.close(fig)


def test_get_current_axes_if_exists_after_figure_closed():
    """Test get_current_axes_if_exists after closing a figure."""
    plt.close('all')
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.sca(ax)
    plt.close(fig)
    
    result = global_collecting.get_current_axes_if_exists()
    assert result is None
    assert plt.get_fignums() == []


def test_get_current_axes_if_exists_multiple_figures():
    """Test get_current_axes_if_exists with multiple figures."""
    plt.close('all')
    try:
        fig1 = plt.figure()
        ax1 = fig1.add_subplot(111)
        fig2 = plt.figure()
        ax2 = fig2.add_subplot(111)
        
        # Make fig1/ax1 current
        plt.figure(fig1.number)
        plt.sca(ax1)
        result = global_collecting.get_current_axes_if_exists()
        assert result is ax1
        
        # Make fig2/ax2 current
        plt.figure(fig2.number)
        plt.sca(ax2)
        result = global_collecting.get_current_axes_if_exists()
        assert result is ax2
        
        assert len(plt.get_fignums()) == 2  # Should not create additional figures
    finally:
        plt.close('all')


def test_get_current_axes_if_exists_with_mock_figure_numbers():
    """Test get_current_axes_if_exists handles Mock figure numbers gracefully."""
    from unittest.mock import Mock, patch
    plt.close('all')
    
    # Mock plt.get_fignums to return something that causes TypeError when sorted
    with patch('matplotlib.pyplot.get_fignums') as mock_get_fignums:
        # This will cause TypeError when matplotlib tries to sort the figure numbers
        mock_get_fignums.return_value = [Mock(), 1]
        
        result = global_collecting.get_current_axes_if_exists()
        assert result is None  # Should handle the error gracefully
