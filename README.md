# PyQuibbler

## Ideas for optimization

- Detect if a change actually occured before invalidating children
- Use weakref for results that lost the time/space cache tradeoff

## Notes

- Document GUI mac issue

## TODO

- Are `iter_quibs_in_object` and `deep_copy_and_replace_quibs_with_vals` good enough?
  - Consider using external lib
  - Support dict, list, set, frozenset, tuple, ndarray (both in code and tests)
- What happens when a quib(1) is plotted and a user drags it?
- Allow continuous update in graphics
- Keep an integer as integer while dragging
- if debug check that iquib does not contain quib
- protect user from setting properties on graphics elements
- should we use `perf_counter` or `process_time` for the cache tradeoff? `process_time` doesn't measure sleep time 


## Q/A

- Why do changes not occur after doing `plt.show(block=False); # my_stuff; time.sleep(1000)`
  - The event loop needs to run- we tried doing `flush_events` but the only way (we saw on mac) 
    for events to happen is to actually start the event loop (this happens automatically when pausing). <br/>
  As a side note, our solution (of ```axes.redraw_in_frame(); axes.figure.canvas.blit()```)
  has near identical performance to running the event loop ) <br/>
  It is important to note that we're not sure of all of this for other backends.
  
