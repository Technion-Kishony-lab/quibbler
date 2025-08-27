import matplotlib.pyplot as plt
from pyquibbler import iquib, quiby


@quiby(is_graphics=True)
def draw_func(y):
    plt.plot([0, 1], [0, y], 'b-', linewidth=2, marker='o')


def test_graphics_stay_in_correct_axes_on_update():
    """Test that graphics stay in the correct axes when quib is updated."""
    
    # Create figure with two axes
    fig = plt.figure()
    ax_plot1 = fig.add_axes([0.1, 0.55, 0.8, 0.4])
    ax_plot1.axis([0, 1, 0, 2])

    ax_plot2 = fig.add_axes([0.1, 0.05, 0.8, 0.4])
    ax_plot2.axis([0, 1, 0, 2])

    # Count initial children in each axes
    n1 = len(ax_plot1.get_children())
    n2 = len(ax_plot2.get_children())
    
    # Set ax_plot1 as current axes and draw
    plt.sca(ax_plot1)
    y_quib = iquib(1.0)

    # drawer = LineDrawer(y_quib)
    # drawer.draw_method()

    draw_func(y_quib)
    
    # Verify that graphics were added to ax_plot1 only
    assert len(ax_plot1.get_children()) == n1 + 1, "sanity"
    assert len(ax_plot2.get_children()) == n2, "sanity"
    
    # Set ax_plot2 as current axes (simulating user interaction)
    plt.sca(ax_plot2)
    
    # Update the quib - this should NOT move graphics to ax_plot2
    y_quib.assign(1.5)
    
    # Verify that graphics stayed in ax_plot1
    assert len(ax_plot1.get_children()) == n1 + 1, "Graphics should stay in ax_plot1 after update"
    assert len(ax_plot2.get_children()) == n2, "ax_plot2 should still be unchanged after update"
    
    plt.close(fig)
